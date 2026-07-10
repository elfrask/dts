import re
import logging

logger = logging.getLogger(__name__)

BLACKLIST = ["traduccion_", "Traducci\u00f3n ", "Traducci\u00f3n_"]


def clean_values(data: dict[str, str]) -> dict[str, str]:
    output = {}
    for key, value in data.items():
        clean_key = key
        for prefix in BLACKLIST:
            if clean_key[: len(prefix)] == prefix:
                clean_key = clean_key[len(prefix) :]
        output[clean_key] = value
    return output


def clean_codes(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text)


def clean_void(
    data: dict[str, str],
    original: dict[str, str],
) -> dict[str, str]:
    output = {}
    removed = 0

    for key, value in data.items():
        cadena = str(value).strip()
        cadena_original = str(original.get(key, "-TTT-")).strip()

        if cadena == "" and cadena_original != "":
            removed += 1
            continue

        if cadena[:1] == "\\" and "*" in cadena.strip()[3:5]:
            if len(clean_codes(cadena[5:]).replace(" ", "")) < 4:
                removed += 1
                continue

        if cadena[:1] == "*" and "*" in cadena.strip()[1:4]:
            if len(clean_codes(cadena[4:]).replace(" ", "")) < 3:
                removed += 1
                continue

        output[key] = value

    logger.info(f"Removed {removed} empty/invalid entries")
    return output
