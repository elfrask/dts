import json
import logging
import re
from pathlib import Path

from src.io.formats import StringsFile, TranslationDict

logger = logging.getLogger(__name__)

ID_PATTERN = re.compile(
    r"^([a-zA-Z0-9_]+_slash_[a-zA-Z0-9_]+_gml_\d+_\d+)(?:_\w+)?$"
)


def generate_input(strings: StringsFile) -> TranslationDict:
    output: dict[str, str] = {}
    add_key = ""

    for item in strings.Strings:
        if ID_PATTERN.match(item):
            add_key = str(item)
            continue

        if add_key:
            if "gml_Script_scr_" in str(item):
                add_key = ""
                continue
            if item == str(item).lower() and item.count(" ") == 0:
                add_key = ""
                continue
            output[add_key] = item
            add_key = ""

    logger.info(f"Generated {len(output)} key-dialog pairs")
    return TranslationDict(data=output)


_BEFORE_TOKENS = ["\\", "*"]
_AFTER_TOKENS = ["/%", "/"]


def check_commands(new_dialog: str, old_dialog: str) -> str:
    result = new_dialog

    for _bef in _BEFORE_TOKENS:
        if old_dialog.strip()[: len(_bef)] == _bef:
            if result.strip()[: len(_bef)] != _bef:
                result = f"{_bef}{result}"
                break

    for _aff in _AFTER_TOKENS:
        if old_dialog.strip()[-len(_aff) :] == _aff:
            if result.strip()[-len(_aff) :] != _aff:
                result = f"{result}{_aff}".replace("//%", "/%")
                break

    return result


def apply_strings(
    strings: StringsFile,
    translations: TranslationDict,
    fix_mode: bool = False,
) -> StringsFile:
    result: list[str] = []
    next_word = ""

    for item in strings.Strings:
        if next_word:
            if next_word.count(" ") != 0 and str(item).count(" ") == 0:
                next_word = item
                result.append(next_word)
                next_word = ""
                continue
            result.append(check_commands(next_word, item))
            next_word = ""
            continue

        if item in translations.data:
            next_word = str(translations.data[item])

        result.append(item)

    logger.info(f"Applied {len(translations.data)} translations to strings")
    return StringsFile(Strings=result)


def merge_dicts(
    original: dict[str, str],
    overlay: dict[str, str],
) -> dict[str, str]:
    output = dict(original)
    output.update(overlay)
    return output


def manual_generate(
    original: TranslationDict,
    translated: TranslationDict,
) -> TranslationDict:
    output: dict[str, str] = {}
    for key in original.data:
        if key not in translated.data:
            output[key] = original.data[key]
    logger.info(f"Found {len(output)} untranslated dialogs")
    return TranslationDict(data=output)


def manual_apply(
    current: TranslationDict,
    manual: TranslationDict,
) -> TranslationDict:
    output = dict(current.data)
    output.update(manual.data)
    logger.info(f"Merged {len(manual.data)} manual edits")
    return TranslationDict(data=output)
