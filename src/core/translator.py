import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from src.io.formats import AuditEntry, ProjectConfig
from src.config.defaults import DEFAULT_PROMPT, NO_THINKING_INSTRUCTION, estimate_cost
from src.io.file_loader import load_json, ensure_json
from src.io.file_writer import write_json
from src.core.events import EventBus
from src.core.provider import TranslationProvider

logger = logging.getLogger(__name__)


class _AuditStore:
    """Loads, appends and persists the project's audit.json."""

    def __init__(self, path: Optional[Path]) -> None:
        self.path = path
        self.entries: list[AuditEntry] = []
        if path is not None and path.exists():
            try:
                data = load_json(path)
                raw = data.get("entries", []) if isinstance(data, dict) else []
                self.entries = [
                    AuditEntry.from_dict(e) for e in raw if isinstance(e, dict)
                ]
            except Exception as exc:
                logger.warning("Could not read audit file '%s': %s", path, exc)

    def add(self, entry: AuditEntry) -> None:
        self.entries.append(entry)
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(
                    {"entries": [e.to_dict() for e in self.entries]},
                    f, indent=4, ensure_ascii=False,
                )
        except Exception as exc:
            logger.warning("Could not write audit file '%s': %s", self.path, exc)


def _audit_path(config: ProjectConfig, output_path: Path) -> Path:
    path = Path(config.route_audit_file)
    return path if path.is_absolute() else output_path.parent / path


def _effective_prompt(config: ProjectConfig) -> str:
    """Resolve the batch prompt and always forbid hidden reasoning."""
    prompt = config.prompt or DEFAULT_PROMPT
    if "NO uses" not in prompt:
        prompt += NO_THINKING_INSTRUCTION
    return prompt


def _emit_audit(
    event_bus: Optional[EventBus],
    store: Optional[_AuditStore],
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    dialogs: int,
    attempts: int,
) -> None:
    """Record one request and notify listeners."""
    entry = AuditEntry(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        dialogs=dialogs,
        attempts=attempts,
        cost=estimate_cost(model, input_tokens, output_tokens),
    )
    logger.info(
        "Audit: %s / %s | in=%d out=%d dialogs=%d attempts=%d cost=$%.6f",
        provider, model, input_tokens, output_tokens, dialogs, attempts, entry.cost,
    )
    if store is not None:
        store.add(entry)
    if event_bus:
        event_bus.emit_audit(entry)


def use_translate(
    provider: TranslationProvider,
    config: ProjectConfig,
    input_path: Path,
    output_path: Path,
    event_bus: Optional[EventBus] = None,
    restart: bool = False,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> None:
    input_data = load_json(input_path)
    ensure_json(output_path)
    output_data = load_json(output_path)

    untranslated = {
        k: v for k, v in input_data.items() if k not in output_data
    }
    total = len(untranslated)

    if total == 0:
        msg = "All dialogs are already translated"
        logger.info(msg)
        if event_bus:
            event_bus.emit_log("info", msg)
        return

    keys = list(untranslated.keys())
    done_count = len(output_data)
    audit_store = _AuditStore(_audit_path(config, output_path))

    # ── Safety net ─────────────────────────────────────────────
    provider_name = str(getattr(config.provider, "value", config.provider))
    use_single = config.single_translate and provider_name == "ollama"
    if config.single_translate and provider_name != "ollama":
        logger.warning("single_translate solo funciona con Ollama. Usando batch mode.")
        if event_bus:
            event_bus.emit_log("warning", "single_translate solo funciona con Ollama. Forzando batch.")

    if use_single:
        _translate_single_mode(
            provider=provider,
            config=config,
            keys=keys,
            untranslated=untranslated,
            output_data=output_data,
            output_path=output_path,
            total=total,
            done_count=done_count,
            event_bus=event_bus,
            is_cancelled=is_cancelled,
            audit_store=audit_store,
        )
    else:
        _translate_batch_mode(
            provider=provider,
            config=config,
            keys=keys,
            untranslated=untranslated,
            output_data=output_data,
            output_path=output_path,
            total=total,
            done_count=done_count,
            event_bus=event_bus,
            is_cancelled=is_cancelled,
            audit_store=audit_store,
        )


def _translate_single_mode(
    *,
    provider: TranslationProvider,
    config: ProjectConfig,
    keys: list[str],
    untranslated: dict[str, str],
    output_data: dict[str, str],
    output_path: Path,
    total: int,
    done_count: int,
    event_bus: Optional[EventBus],
    is_cancelled: Optional[Callable[[], bool]],
    audit_store: Optional[_AuditStore] = None,
) -> None:
    failed: list[str] = []

    for i, key in enumerate(keys):
        if is_cancelled and is_cancelled():
            msg = f"Translation cancelled by user at {i}/{total}"
            logger.info(msg)
            if event_bus:
                event_bus.emit_log("info", msg)
            break

        if event_bus:
            event_bus.emit_progress(done_count, total + done_count)

        text = untranslated[key]

        for attempt in range(3):
            try:
                translated = provider.translate_single(
                    key=key,
                    text=text,
                    prompt="",
                    config=config,
                )
                output_data[key] = translated
                done_count += 1
                write_json(output_path, output_data)
                # Single-dialog mode does not report token usage; keep the row
                # so dialogs/attempts remain auditable.
                _emit_audit(
                    event_bus,
                    audit_store,
                    provider=provider.name,
                    model=config.model,
                    input_tokens=0,
                    output_tokens=0,
                    dialogs=1,
                    attempts=attempt + 1,
                )
                if event_bus:
                    event_bus.emit_log(
                        "info",
                        f"✓ {key} ({done_count}/{total + len(output_data) - done_count})",
                    )
                break

            except NotImplementedError:
                logger.warning(
                    "translate_single not supported by %s, falling back to batch",
                    provider.name,
                )
                # Fall back to batch for remaining items
                remaining_keys = keys[i:]
                remaining_untranslated = {k: untranslated[k] for k in remaining_keys}
                _translate_batch_mode(
                    provider=provider,
                    config=config,
                    keys=remaining_keys,
                    untranslated=remaining_untranslated,
                    output_data=output_data,
                    output_path=output_path,
                    total=total,
                    done_count=done_count,
                    event_bus=event_bus,
                    is_cancelled=is_cancelled,
                    audit_store=audit_store,
                )
                return

            except Exception as e:
                logger.warning(
                    "Single translate attempt %d/3 for '%s' failed: %s",
                    attempt + 1, key, e,
                )
                if attempt == 2:
                    failed.append(key)
                    if event_bus:
                        event_bus.emit_log("warning", f"✗ {key} (failed after 3 attempts)")
                time.sleep(1)

        # No sleep between Ollama single dialogs (local, no rate limits)
        if i < total - 1 and not (is_cancelled and is_cancelled()):
            if event_bus:
                event_bus.emit_progress(done_count, total + done_count)

    if failed and event_bus:
        event_bus.emit_error(f"Failed to translate {len(failed)} dialogs")

    cancelled = is_cancelled and is_cancelled()
    final_msg = (
        f"{'Cancelled' if cancelled else 'Translation complete'}: "
        f"{done_count}/{total + len(output_data) - done_count} dialogs"
    )
    logger.info(final_msg)
    if event_bus:
        event_bus.emit_complete(final_msg)


def _translate_batch_mode(
    *,
    provider: TranslationProvider,
    config: ProjectConfig,
    keys: list[str],
    untranslated: dict[str, str],
    output_data: dict[str, str],
    output_path: Path,
    total: int,
    done_count: int,
    event_bus: Optional[EventBus],
    is_cancelled: Optional[Callable[[], bool]],
    audit_store: Optional[_AuditStore] = None,
) -> None:
    provider_name = str(getattr(config.provider, "value", config.provider))
    tries = 0
    index = 0
    chunk_size = config.chunk_size

    while index < total:
        if is_cancelled and is_cancelled():
            msg = f"Translation cancelled by user at {index}/{total}"
            logger.info(msg)
            if event_bus:
                event_bus.emit_log("info", msg)
            break

        if event_bus:
            event_bus.emit_progress(done_count, total + done_count)

        if tries >= 5:
            msg = f"Max retries reached at {index}/{total}"
            logger.error(msg)
            if event_bus:
                event_bus.emit_error(msg)
            break

        effective_chunk = max(1, chunk_size // (tries + 1))
        chunk_keys = keys[index : index + effective_chunk]
        chunk = {k: untranslated[k] for k in chunk_keys}

        try:
            result = provider.translate_batch(
                items=chunk,
                prompt=_effective_prompt(config),
                config=config,
            )
            tries = 0
        except Exception as e:
            tries += 1
            logger.warning("Chunk failed (try %d/5): %s", tries, e)
            if event_bus:
                event_bus.emit_error(f"Chunk failed: {e}")
            time.sleep(3)
            continue

        if result.success:
            output_data.update(result.data)
            done_count += len(result.data)
            write_json(output_path, output_data)

            _emit_audit(
                event_bus,
                audit_store,
                provider=provider.name,
                model=config.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                dialogs=len(chunk_keys),
                attempts=result.attempts,
            )

            if result.failed_keys:
                logger.warning("Failed keys in chunk: %s", result.failed_keys)
        else:
            logger.error("Batch failed: %s", result.error)
            tries += 1
            time.sleep(3)
            continue

        index += len(chunk_keys)

        if index < total and not (is_cancelled and is_cancelled()):
            if provider_name != "ollama" and config.paused_mode:
                logger.info("Waiting 7s before next chunk (%d/%d)", index, total)
                time.sleep(7)

    cancelled = is_cancelled and is_cancelled()
    final_msg = f"{'Cancelled' if cancelled else 'Translation complete'}: {done_count}/{done_count} dialogs"
    logger.info(final_msg)
    if event_bus:
        event_bus.emit_complete(final_msg)
