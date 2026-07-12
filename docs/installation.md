# Instalación

## Requisitos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- Opcional: [UndertaleModTool CLI](https://github.com/UnderminersTeam/UndertaleModTool) para trabajar con archivos `data.win`
- Opcional: [Ollama](https://ollama.ai) para traducción local

## Instalación desde código fuente

1. Clona el repositorio:
```bash
git clone <url-del-repositorio>
cd dts-v2
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Verifica que todo funciona:
```bash
python -m dts help
```

## Dependencias

| Paquete | Versión mínima | Propósito |
|---|---|---|
| `google-genai` | >=1.0.0 | Proveedor Gemini |
| `ollama` | >=0.6.0 | Proveedor Ollama (local) |
| `openai` | >=1.0.0 | Proveedores OpenAI, Groq, DeepInfra, Together |
| `anthropic` | >=0.30.0 | Proveedor Anthropic (Claude) |
| `click` | >=8.1.0 | CLI (interfaz de línea de comandos) |
| `rich` | >=13.0.0 | Output con colores en CLI |
| `ttkbootstrap` | >=1.10.0 | GUI (interfaz gráfica) |

## Configuración de UndertaleModTool (UMT)

DTS necesita UMT CLI para extraer strings de archivos `data.win`. Hay dos formas de obtenerlo:

### Opción 1: Descarga automática (recomendada)

Desde la GUI:
1. Abre **Configuración global** → pestaña **Motor (UMT)**
2. Haz clic en **"Descargar UMT CLI"**
3. La descarga se realiza automáticamente y se configura la ruta

### Opción 2: Manual

1. Descarga [UndertaleModTool CLI](https://github.com/UnderminersTeam/UndertaleModTool/releases) desde GitHub
2. Extrae el archivo ZIP en una carpeta
3. En DTS, configura la ruta de la carpeta en **Configuración global** → **Motor (UMT)** → **Método manual**

> **Nota legal**: UMT está bajo licencia GPLv3. DTS no incluye UMT en su distribución; lo invoca externamente.

## Verificación

```bash
# Ver CLI
dts help

# Ver configuración global
dts config --show
```
