import os
from pathlib import Path

PROJECT_DIR = Path.cwd()

DEFAULT_PATHS = {
    "route_input_file": "lang_input.json",
    "route_output_file": "lang_es_out.json",
    "route_strings_result_file": "strings_es.json",
    "route_normalize_file": "lang_es_normalize.json",
    "route_manual_file": "lang_manual_edit.json",
    "umt_cli_path": "",
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
    "Devolverás los json exactamente con este formato para ser parseado:\n\n"
    '{\n'
    '    "[Nombre de la clave tal cual como esta]": "[Contenido de la clave ya traducido]",\n'
    '    ...\n'
    '}\n'
)

DEFAULT_MODEL = "gemini-2.5-flash"

DEFAULT_PROVIDER = "gemini"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_TIMEOUT = 120

DEFAULT_SETTINGS_FILE = "settings.json"

DEFAULT_UMT_DOWNLOAD_URL = (
    "https://github.com/UnderminersTeam/UndertaleModTool/releases/download/0.9.1.1/UTMT_CLI_v0.9.1.1-Windows.zip"
)
