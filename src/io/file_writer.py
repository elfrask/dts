import json
import logging
from pathlib import Path

from src.io.formats import StringsFile, TranslationDict

logger = logging.getLogger(__name__)


def write_json(path: Path, data: dict, ensure_ascii: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=ensure_ascii)
    logger.info(f"Written: '{path}'")


def write_strings(path: Path, strings: StringsFile) -> None:
    write_json(path, {"Strings": strings.Strings})


def write_translation_dict(path: Path, data: TranslationDict) -> None:
    write_json(path, data.data)
