# Proveedores de IA

DTS soporta múltiples proveedores de IA para la traducción. Se dividen en tres categorías según su velocidad y caso de uso.

## 1. Ultra Velocidad (Inferencia especializada)

Estos proveedores usan hardware optimizado para alta velocidad, ideales para lotes masivos de diálogos sencillos.

### Groq

- **API**: OpenAI-compatible
- **URL base**: `https://api.groq.com/openai/v1`
- **Requiere**: API key

| Modelo | Descripción |
|---|---|
| `openai/gpt-oss-20b` | Superveloz, ideal para strings comunes |
| `openai/gpt-oss-120b` | Alta capacidad para mantener formato JSON |
| `qwen/qwen3.6-27b` | Excelente con caracteres no latinos y variables de código |

### DeepInfra

- **API**: OpenAI-compatible
- **URL base**: `https://api.deepinfra.com/v1/openai`
- **Requiere**: API key

| Modelo | Descripción |
|---|---|
| `deepseek-ai/DeepSeek-V4-Flash` | Rápido y económico para estructurar datos |
| `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Gran comprensión de contextos y chistes |
| `Qwen/Qwen2.5-72B-Instruct` | Meticuloso respetando variables de formato |

### Together AI

- **API**: OpenAI-compatible
- **URL base**: `https://api.together.xyz/v1`
- **Requiere**: API key

| Modelo | Descripción |
|---|---|
| `together/Qwen3.7-Plus` | Potente para coherencia de género y número |
| `together/Llama-3-8B-Instruct-Lite` | Modo económico de alta velocidad |

## 2. Proveedores propietarios (Casos complejos)

### Anthropic (Claude)

- **API**: Anthropic Messages API
- **Requiere**: API key

| Modelo | Descripción |
|---|---|
| `claude-3-5-sonnet-20241022` | El mejor siguiendo reglas complejas. No rompe JSONs. |
| `claude-3-5-haiku-20241022` | Alternativa rápida y económica |

### OpenAI

- **API**: OpenAI API
- **URL base**: `https://api.openai.com/v1`
- **Requiere**: API key

| Modelo | Descripción |
|---|---|
| `gpt-4o-mini` | Extremadamente barato. El caballo de batalla. |
| `gpt-4o` | Máxima inteligencia para textos enrevesados |

## 3. Proveedor local

### Ollama

- **API**: Ollama REST API
- **Requiere**: [Ollama](https://ollama.ai) instalado y corriendo en el sistema

| Parámetro | Defecto | Descripción |
|---|---|---|
| Host | `http://localhost` | Dirección del servidor Ollama |
| Puerto | `11434` | Puerto del servidor Ollama |
| Timeout | `120s` | Timeout de conexión |

Los modelos disponibles se detectan automáticamente desde la instalación local de Ollama.

> **Nota**: Ollama solo aparece en el selector de proveedores si el motor está corriendo y responde en `http://localhost:11434/api/tags`.

## Configuración de API keys

### Desde la GUI

1. Abre **Configuración global** → pestaña **Proveedor de IA**
2. Selecciona el proveedor en la lista lateral
3. Agrega una o más API keys usando el botón **"+ Agregar key"**
4. Marca/desmarca las keys habilitadas según necesites
5. Haz clic en **Guardar**

### Desde el CLI

```bash
# Agregar key de Gemini
dts config --add-key "tu-api-key-aqui"

# Ver configuración actual
dts config --show
```

## Rotación de API keys

Cuando un proveedor tiene múltiples API keys configuradas, DTS las rota automáticamente. Si una key falla (límite de cuota, error de red), pasa a la siguiente key automáticamente. Esto es especialmente útil para proveedores con límites de uso gratuitos como Gemini.
