import json
import logging
import time
from typing import Optional

from src.io.formats import ProjectConfig, TranslationResult, TranslationProgress
from src.io.file_loader import load_json, load_translation_dict, ensure_json
from src.io.file_writer import write_json
from src.core.events import EventBus, Signal
from src.core.provider import TranslationProvider

logger = logging.getLogger(__name__)


def _show_extremes(string: str, margin: int = 10) -> str:
    return f"{repr(string[:margin])} - {repr(string[-margin:])}"


def str2json(response: str) -> dict[str, str]:
    _original = response
    response = response.replace("`", "")

    while response[:1] != "{":
        response = response[1:]
        if not response:
            raise ValueError("Response is not JSON: " + _original)

    while response[-1:] != "}":
        response = response[:-1]
        if response[-2:] != '",':
            response = response[:-1] + "}"
            break
        if not response:
            raise ValueError("Response is not JSON: " + _original)

    import unicodedata
    while True:
        try:
            normalizado = unicodedata.normalize("NFKD", response)
            ascii_text = normalizado.encode("ASCII", "ignore").decode("ASCII")
            return json.loads(ascii_text)
        except Exception:
            logger.warning("reducing... %s", _show_extremes(response))

        while response[-2:] != '",':
            response = response[:-1]
            if not response:
                raise ValueError("Response is not JSON: " + _original)
        response = response[:-1] + "}"


def new_str2json(response: str) -> dict[str, str]:
    json_limpio = response.strip("```json").strip("```").strip()

    while True:
        try:
            return json.loads(json_limpio)
        except Exception as e:
            while json_limpio[-2:] != '",':
                json_limpio = json_limpio[:-1]
                if not json_limpio:
                    raise ValueError(f"Response is not JSON: {response}") from e
            json_limpio = json_limpio[:-1] + "}"
            logger.warning("reducing... %s", _show_extremes(json_limpio))


def use_translate(
    provider: TranslationProvider,
    config: ProjectConfig,
    input_path: str,
    output_path: str,
    event_bus: Optional[EventBus] = None,
    restart: bool = False,
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

    def _emit_progress(chunk_idx: int, chunk_total: int):
        if event_bus:
            progress = TranslationProgress(
                total=total,
                completed=done_count,
                current_chunk=chunk_idx,
                total_chunks=chunk_total,
            )
            event_bus.emit_progress(done_count, total + done_count)

    tries = 0
    index = 0
    chunk_size = config.chunk_size

    while index < total:
        _emit_progress(index, total)

        if tries >= 5:
            msg = f"Max retries reached at {index}/{total}"
            logger.error(msg)
            if event_bus:
                event_bus.emit_error(msg)
            break

        chunk_keys = keys[index : index + chunk_size]
        chunk = {k: untranslated[k] for k in chunk_keys}

        try:
            result = provider.translate_batch(
                items=chunk,
                prompt=config.prompt,
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

            if result.failed_keys:
                logger.warning("Failed keys in chunk: %s", result.failed_keys)

        index += len(chunk_keys)

        if index < total:
            logger.info(f"Waiting 7s before next chunk ({index}/{total})")
            time.sleep(7)

    msg = f"Translation complete: {done_count}/{done_count} dialogs"
    logger.info(msg)
    if event_bus:
        event_bus.emit_complete(msg)
