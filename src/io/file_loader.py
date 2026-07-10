import json
import logging
from pathlib import Path
from typing import Any

from src.io.formats import StringsFile, TranslationDict

logger = logging.getLogger(__name__)


def _validate_json_object(content: str, path: Path) -> None:
    if content[:1] + content[-1:] != "{}":
        raise ValueError(f"File '{path}' is not a valid JSON object")


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    _validate_json_object(content, path)
    return json.loads(content)


def load_strings(path: Path) -> StringsFile:
    data = load_json(path)
    if "Strings" not in data or not isinstance(data["Strings"], list):
        raise ValueError(f"File '{path}' is missing 'Strings' array")
    return StringsFile(Strings=data["Strings"])


def load_translation_dict(path: Path) -> TranslationDict:
    data = load_json(path)
    return TranslationDict(data=data)


def ensure_json(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{}")
        logger.info(f"Created empty JSON file: '{path}'")


def try_load_json(path: Path) -> dict[str, Any] | None:
    try:
        return load_json(path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        logger.warning(f"Cannot load '{path}': {e}")
        return None
