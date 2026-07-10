import json
import logging
import time
from pathlib import Path
from typing import Optional

from src.io.formats import ProjectConfig, TranslationProgress
from src.io.file_loader import load_json, ensure_json
from src.io.file_writer import write_json
from src.core.events import EventBus
from src.core.provider import TranslationProvider

logger = logging.getLogger(__name__)


def use_translate(
    provider: TranslationProvider,
    config: ProjectConfig,
    input_path: Path,
    output_path: Path,
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

    tries = 0
    index = 0
    chunk_size = config.chunk_size

    while index < total:
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
        else:
            logger.error("Batch failed: %s", result.error)
            tries += 1
            time.sleep(3)
            continue

        index += len(chunk_keys)

        if index < total:
            logger.info("Waiting 7s before next chunk (%d/%d)", index, total)
            time.sleep(7)

    msg = f"Translation complete: {done_count}/{done_count} dialogs"
    logger.info(msg)
    if event_bus:
        event_bus.emit_complete(msg)
