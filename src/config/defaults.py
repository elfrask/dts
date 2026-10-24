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
    "IMPORTANTE: NO uses el modo de pensamiento, razonamiento extendido ni análisis interno. "
    "Responde directamente con el JSON final, sin cadenas de razonamiento, sin explicaciones y sin pasos intermedios.\n\n"
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

# CommandCode aggregates every major model behind one API.
# OpenAI-compatible models are served on /v1/chat/completions; Claude models
# only on /v1/messages. The static list is only a fallback: the real catalog
# is fetched live from {base_url}/models.
COMMANDCODE_BASE_URL = "https://api.commandcode.ai/provider/v1"
COMMANDCODE_ANTHROPIC_BASE_URL = "https://api.commandcode.ai/provider"

COMMANDCODE_MODELS = [
    "deepseek/deepseek-v4.1-flash",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-pro",
    "claude-sonnet-5-5",
    "claude-sonnet-5",
    "claude-haiku-5-5",
    "gpt-5.6-sol",
    "gpt-5.5",
    "google/gemini-3.8-flash",
    "z-ai/glm-5.3-flash",
]

# Providers shipped with DTS, in the order shown in the UI.
BUILTIN_PROVIDERS: list[str] = [
    "commandcode", "gemini", "groq", "deepinfra", "together", "anthropic", "openai", "ollama",
]

# Open / closed API shapes a custom provider can speak.
API_TYPES: dict[str, str] = {
    "openai": "OpenAI-compatible",
    "anthropic": "Anthropic Messages",
}

# Map provider string -> model list
PROVIDER_MODELS: dict[str, list[str]] = {
    "commandcode": COMMANDCODE_MODELS,
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
    "commandcode": COMMANDCODE_BASE_URL,
    "groq": "https://api.groq.com/openai/v1",
    "deepinfra": "https://api.deepinfra.com/v1/openai",
    "together": "https://api.together.xyz/v1",
}

# USD per 1M tokens: (input, output). Used only to *estimate* costs in the
# audit tab. Unknown models fall back to (0, 0).
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # ── CommandCode (GOAT / Provider rates) ──────────────────
    "deepseek/deepseek-v4.1-flash": (0.15, 0.60),
    "deepseek/deepseek-v4.1-flash-fast": (0.16, 0.58),
    "deepseek/deepseek-v4-flash": (0.15, 0.60),
    "deepseek/deepseek-v4-flash-fast": (0.28, 0.56),
    "deepseek/deepseek-v4-pro": (0.66, 1.98),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-5-5": (5.00, 25.00),
    "gpt-5.6-sol": (5.00, 30.00),
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.5": (2.50, 15.00),
    "google/gemini-3.8-flash": (1.50, 7.50),
    "google/gemini-3.7-flash": (1.50, 7.50),
    "z-ai/glm-5.3-flash": (0.15, 0.50),
    "z-ai/glm-5.3-flashx": (0.37, 1.25),
    "zai-org/GLM-5.3": (1.40, 4.40),
    "Qwen/Qwen3.8-Flash": (0.16, 0.47),
    "qwen/qwen3.8-flash": (0.16, 0.47),
    "minimax/minimax-m3.1-flash": (0.15, 0.60),
    "moonshotai/Kimi-K3.1-Pro": (2.00, 10.00),
    "moonshotai/Kimi-K3": (3.00, 15.00),
    "xai/grok-4.7": (2.00, 6.00),
    # ── Direct providers (public list prices) ────────────────
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.1-pro-preview": (1.25, 10.00),
    "gemini-3.1-flash-lite": (0.10, 0.40),
    "gemini-3.5-flash": (0.30, 2.50),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a request. Returns 0.0 for unknown models."""
    pin, pout = MODEL_PRICING.get(model, (0.0, 0.0))
    return (input_tokens / 1_000_000.0) * pin + (output_tokens / 1_000_000.0) * pout


DEFAULT_AUDIT_FILE = "audit.json"

# Appended to every batch prompt (including user-customised ones) to make sure
# no provider spends tokens/tokens on hidden reasoning.
NO_THINKING_INSTRUCTION = (
    "\n\nIMPORTANTE: NO uses el modo de pensamiento, razonamiento extendido ni "
    "análisis interno. Responde directamente con el resultado final, sin cadenas "
    "de razonamiento ni pasos intermedios."
)

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
    "IMPORTANTE: NO uses el modo de pensamiento, razonamiento extendido ni análisis interno. "
    "Devuelve SOLO el texto traducido, sin explicaciones, prefijos ni formato adicional."
)
