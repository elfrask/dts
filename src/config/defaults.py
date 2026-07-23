import os
from pathlib import Path

PROJECT_DIR = Path.cwd()

DEFAULT_PATHS = {
    "route_input_file": "lang_input.json",
    "route_output_file": "lang_es_out.json",
    "route_strings_result_file": "strings_es.json",
    "route_normalize_file": "lang_es_normalize.json",
    "route_manual_file": "lang_manual_edit.json",
    "umt_directory": "",
}

DEFAULT_CHUNK_SIZE = 200

DEFAULT_APP_CONFIG_DIR = (
    Path(os.environ.get("APPDATA", Path.home() / ".config")) / "dts"
)
DEFAULT_APP_CONFIG_FILE = DEFAULT_APP_CONFIG_DIR / "settings.json"

DEFAULT_PROMPT = (
    "Actúa como un traductor profesional de nivel C2 de ingles el cual tu rol va a ser "
    "traducir diálogos de un juego respetando el orden de los diálogos y conservando la "
    "coherencia entre ellos. Vas a traducir diálogos del ingles al español. "
    "Manten los nombres de los personajes y lugares iguales, no los traduzcas ni los alteres. "
    "No traduzcas comandos ni símbolos especiales. Devuelve todo el texto conservando los "
    "símbolos exactamente iguales, sin modificaciones. "
    "Hay comandos en los diálogos! ten cuidado con esos comandos, entre ellos están: "
    "\\\\XX <- cuando están estas barras los 2 siguientes caracteres que pueden ser "
    "mayúsculas y minúsculas son parte del comando, déjalos tal cual igual. "
    "$~X y ~X <- esto es un parámetro, no lo modifiques; ^X <- esto también es otro comando, "
    "no lo modifiques. Algunos diálogos al final tienen sufijos como '/', '%' u '/%' "
    "consérvelos en el texto al final sin alterar su posición. "
    "Si consigues formatos asi: [N:TEXTO] solo traduce el texto. "
    "Si llegas a conseguir un dialogo sin espacios, comandos ni símbolos que esta todo en "
    "minúscula déjalo tal cual y si trae '_' con mas razón déjalo igual. "
    "Los textos de las traducciones no pueden ser mas grandes que el original, para evitar "
    "desbordamiento se recomiendo que sea igual de largo o mas corto que el original. "
    "evita por completo usar el modo de pensamiento, para esta tarea no la usaras, si puedes no usarla mejor, eso evita consumir mucho tiempo en procesar la solicitud"
    "Devolverás los json exactamente con este formato para ser parseado:\n\n"
    '{\n'
    '    "[Nombre de la clave tal cual como esta]": "[Contenido de la clave ya traducido]",\n'
    '    ...\n'
    '}\n'
)

DEFAULT_MODEL = "gemini-3.5-flash"

DEFAULT_PROVIDER = "gemini"

DEFAULT_OLLAMA_HOST = "http://localhost"
DEFAULT_OLLAMA_PORT = 11434
DEFAULT_OLLAMA_TIMEOUT = 120

DEFAULT_SETTINGS_FILE = "settings.json"

DEFAULT_UMT_DOWNLOAD_URL = (
    "https://github.com/UnderminersTeam/UndertaleModTool/releases/download/0.9.1.1/UTMT_CLI_v0.9.1.1-Windows.zip"
)

# ── Provider model lists ──────────────────────────────────────────

GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.0-deep-think",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]

OLLAMA_DEFAULT_MODELS = [
    "llama3", "llama3.1", "llama3.2",
    "qwen2.5", "mistral", "mixtral",
    "gemma2", "codellama",
]

GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
]

DEEPINFRA_MODELS = [
    "deepseek-ai/DeepSeek-V4-Flash",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "Qwen/Qwen2.5-72B-Instruct",
]

TOGETHER_MODELS = [
    "together/Qwen3.7-Plus",
    "together/Llama-3-8B-Instruct-Lite",
]

ANTHROPIC_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
]

OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
]

# Map provider string -> model list
PROVIDER_MODELS: dict[str, list[str]] = {
    "gemini": GEMINI_MODELS,
    "ollama": OLLAMA_DEFAULT_MODELS,
    "groq": GROQ_MODELS,
    "deepinfra": DEEPINFRA_MODELS,
    "together": TOGETHER_MODELS,
    "anthropic": ANTHROPIC_MODELS,
    "openai": OPENAI_MODELS,
}

# OpenAI-compatible base URLs
OPENAI_COMPATIBLE_BASE_URLS: dict[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
    "deepinfra": "https://api.deepinfra.com/v1/openai",
    "together": "https://api.together.xyz/v1",
}

DEFAULT_OLLAMA_SINGLE_PROMPT = (
    "Actúa como un traductor profesional de nivel C2 de inglés. "
    "Tu rol es traducir un diálogo de un videojuego del inglés al español. "
    "Es una traducción independiente, no necesitas mantener coherencia con otros diálogos. "
    "Manten los nombres de los personajes y lugares iguales, no los traduzcas ni los alteres. "
    "No traduzcas comandos ni símbolos especiales. Conserva los símbolos exactamente iguales, sin modificaciones. "
    "Hay comandos en los diálogos, ten cuidado con ellos: "
    "\\XX cuando están estas barras, los 2 siguientes caracteres (mayúsculas o minúsculas) son parte del comando, déjalos tal cual. "
    "$~X y ~X son parámetros, no los modifiques. "
    "^X también es otro comando, no lo modifiques. "
    "Algunos diálogos al final tienen sufijos como '/', '%' u '/%', consérvalos al final sin alterar su posición. "
    "Si ves formatos como [N:TEXTO] solo traduce el texto dentro de los corchetes. "
    "Si el diálogo está todo en minúscula sin espacios, comandos ni símbolos, déjalo tal cual. "
    "Si trae '_' con más razón déjalo igual. "
    "Los textos de las traducciones no pueden ser más grandes que el original, para evitar desbordamiento. "
    "Debe ser igual de largo o más corto que el original. "
    "Devuelve SOLO el texto traducido, sin explicaciones, prefijos ni formato adicional."
)
