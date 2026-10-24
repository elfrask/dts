# Proveedores de IA

DTS soporta múltiples proveedores de IA para la traducción. Se dividen en tres categorías según su velocidad y caso de uso.

## 0. Agregador — CommandCode

Un solo API key para todos los modelos principales (DeepSeek, Claude, GPT, Gemini, Qwen, GLM, Kimi…).

- **API**: OpenAI-compatible **y** Anthropic Messages
- **URL base (OpenAI)**: `https://api.commandcode.ai/provider/v1`
- **URL base (Anthropic)**: `https://api.commandcode.ai/provider` (el SDK añade `/v1/messages`)
- **Catálogo**: `GET https://api.commandcode.ai/provider/v1/models`
- **Requiere**: API key (plan Provider, GOAT, Pro, Max o Team; el plan Go no tiene API)

Los modelos Claude se enrutan automáticamente por `/v1/messages`; el resto por
`/v1/chat/completions`. El catálogo se carga en vivo con **"Actualizar modelos"**
o **"Cargar del proveedor"**.

| Modelo | Descripción |
|---|---|
| `deepseek/deepseek-v4.1-flash` | Rápido y económico, recomendado |
| `deepseek/deepseek-v4-pro` | Razonamiento de contexto largo |
| `claude-sonnet-5-5` | Excelente siguiendo instrucciones complejas |
| `claude-haiku-5-5` | Rápido y compacto |
| `gpt-5.6-sol` | Modelo frontera de OpenAI |
| `google/gemini-3.8-flash` | Rápido y capaz |
| `z-ai/glm-5.3-flash` | Económico con 1M de contexto |

> La lista anterior es solo respaldo. El catálogo real (más de 60 modelos) se
> consulta al endpoint `/models`; los modelos de decisión `typesafe/*` se
> excluyen porque no son modelos de chat.

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

## 4. Proveedores personalizados

Puedes conectar cualquier endpoint que hable el protocolo de OpenAI o de
Anthropic, sin tocar el código: vLLM, LM Studio, LiteLLM, un proxy corporativo,
etc.

### Crear uno desde la GUI

1. **Configuración global** → pestaña **Proveedor de IA**
2. Pulsa **"+ Nuevo proveedor"** y escribe un nombre
3. Completa el formulario:
   - **Nombre visible**: etiqueta que verás en la lista
   - **Tipo de API**: `openai` (compatible) o `anthropic`
   - **Base URL**: por ejemplo `http://localhost:8000/v1`
   - **API keys**: igual que cualquier otro proveedor
4. En **Modelos disponibles** pulsa **"Cargar del proveedor"** para consultar el
   catálogo (`GET {base_url}/models`), o agrega los modelos a mano
5. Guarda y selecciona el proveedor en la pestaña **Traducir**

### Modelos dinámicos

Cada proveedor puede listar sus modelos en vivo:

| Proveedor | Endpoint consultado |
|---|---|
| OpenAI-compatible | `GET {base_url}/models` |
| Anthropic | `GET /v1/models` |
| Gemini | `client.models.list()` |
| Ollama | `GET /api/tags` |

Si el endpoint no responde, DTS usa la lista guardada por el usuario (custom) o
la lista estática integrada. En la pestaña **Traducir** puedes forzar un refresco
con el botón **"Actualizar modelos"**.

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
