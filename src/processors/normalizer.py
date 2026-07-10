import logging
import unicodedata

logger = logging.getLogger(__name__)


def normalice_text(text: str) -> str:
    texto_normalizado = unicodedata.normalize("NFKD", text)
    return texto_normalizado.encode("ASCII", "ignore").decode("ASCII")


def normalice_text_new(text: str, secure: bool = False) -> str:
    if not isinstance(text, str):
        return text

    text = (
        text.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )

    if secure:
        reemplazos = {
            "\u00e1": "a", "\u00e9": "e", "\u00ed": "i", "\u00f3": "o", "\u00fa": "u",
            "\u00c1": "A", "\u00c9": "E", "\u00cd": "I", "\u00d3": "O", "\u00da": "U",
            "\u00f1": "n", "\u00d1": "N",
            "\u00fc": "u", "\u00dc": "U",
            "\u00a1": "", "\u00bf": "",
        }
        for original, limpio in reemplazos.items():
            text = text.replace(original, limpio)

        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ASCII", "ignore").decode("ASCII")

    return text


def clean_normalice(data: dict[str, str]) -> dict[str, str]:
    output = {}
    for key, value in data.items():
        try:
            output[key] = normalice_text(value)
        except Exception as e:
            logger.error(f"Error normalizing '{key}': {e}")
            output[key] = value
    return output


def clean_normalice_new(data: dict[str, str], secure: bool = False) -> dict[str, str]:
    output = {}
    for key, value in data.items():
        try:
            output[key] = normalice_text_new(value, secure)
        except Exception as e:
            logger.error(f"Error normalizing '{key}': {e}")
            output[key] = value
    return output
