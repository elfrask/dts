# Archivos y configuración

## Archivos del proyecto

Todos los archivos generados se almacenan dentro del directorio del proyecto. Las rutas pueden ser relativas (al directorio del proyecto) o absolutas.

| Archivo | Rol | Formato |
|---|---|---|
| `strings.json` | Todos los strings del juego (desde data.win) | `{"Strings": ["id1", "dialog1", ...]}` |
| `lang_input.json` | Input generado para traducción | `{"key_id": "dialog text", ...}` |
| `lang_es_out.json` | Output de traducción automática | `{"key_id": "diálogo traducido", ...}` |
| `lang_es_normalize.json` | Output normalizado | Mismo formato que `lang_es_out.json` |
| `strings_es.json` | Strings resultantes aplicados | Mismo formato que `strings.json` |
| `lang_manual_edit.json` | Edición manual de diálogos faltantes | Mismo formato que `lang_es_out.json` |
| `settings.json` | Configuración del proyecto | Ver sección ProjectConfig |

## Configuración de la aplicación (AppConfig)

Archivo: `%APPDATA%/dts/settings.json` (Windows) o `~/.config/dts/settings.json` (Linux/macOS)

Contiene datos sensibles (API keys) y configuración global. Nunca se almacena dentro de un proyecto.

### Estructura

```json
{
  "providers": {
    "gemini": {
      "keys": [
        {"name": "key1", "key": "AIza...", "enabled": true}
      ]
    },
    "groq": {
      "keys": [
        {"name": "main", "key": "gsk_...", "enabled": true}
      ]
    }
  },
  "ollama_host": "http://localhost",
  "ollama_port": 11434,
  "ollama_timeout": 120,
  "umt_directory": "C:/UMT",
  "umt_auto_download": false
}
```

### Campos

| Campo | Tipo | Defecto | Descripción |
|---|---|---|---|
| `providers` | objeto | `{}` | Mapa de nombre de proveedor a sus API keys |
| `ollama_host` | string | `"http://localhost"` | Host del servidor Ollama |
| `ollama_port` | int | `11434` | Puerto del servidor Ollama |
| `ollama_timeout` | int | `120` | Timeout de conexión a Ollama (segundos) |
| `umt_directory` | string | `""` | Carpeta donde está instalado UMT CLI |
| `umt_auto_download` | bool | `false` | Indica si UMT fue descargado automáticamente |

## Configuración del proyecto (ProjectConfig)

Archivo: `<directorio_del_proyecto>/settings.json`

Contiene datos de sesión del proyecto. No contiene API keys ni datos de conexión de proveedores.

### Estructura

```json
{
  "route_strings_file": "strings.json",
  "route_data_win": "",
  "route_input_file": "lang_input.json",
  "route_output_file": "lang_es_out.json",
  "route_strings_result_file": "strings_es.json",
  "route_normalize_file": "lang_es_normalize.json",
  "route_manual_file": "lang_manual_edit.json",
  "chunk_size": 200,
  "provider": "gemini",
  "prompt": "Actúa como un traductor profesional...",
  "model": "gemini-3.5-flash",
  "umt_directory": ""
}
```

### Campos

| Campo | Tipo | Defecto | Descripción |
|---|---|---|---|
| `route_strings_file` | string | `"strings.json"` | Ruta al archivo de strings original |
| `route_data_win` | string | `""` | Ruta al archivo data.win original |
| `route_input_file` | string | `"lang_input.json"` | Ruta al archivo de input para traducción |
| `route_output_file` | string | `"lang_es_out.json"` | Ruta al archivo de traducción raw |
| `route_strings_result_file` | string | `"strings_es.json"` | Ruta al archivo de strings traducidos |
| `route_normalize_file` | string | `"lang_es_normalize.json"` | Ruta al archivo normalizado |
| `route_manual_file` | string | `"lang_manual_edit.json"` | Ruta al archivo de edición manual |
| `chunk_size` | int | `200` | Diálogos por lote de traducción |
| `provider` | string | `"gemini"` | Proveedor de IA activo |
| `prompt` | string | `""` | Prompt de traducción (usa el default si está vacío) |
| `model` | string | `"gemini-3.5-flash"` | Modelo de IA activo |
| `umt_directory` | string | `""` | Carpeta UMT (hereda de AppConfig si no se especifica) |

## Gestión de configuración desde CLI

```bash
# Ver configuración del proyecto actual
dts settings --show

# Cambiar proveedor
dts settings --provider groq

# Cambiar modelo
dts settings --model "deepseek-ai/DeepSeek-V4-Flash"

# Cambiar chunk size
dts settings --chunk-size 150

# Ver configuración global
dts config --show

# Agregar API key
dts config --add-key "AIzaSy..."

# Cambiar host de Ollama
dts config --ollama-host "http://192.168.1.100"
```
