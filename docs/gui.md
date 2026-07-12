# GUI — Interfaz gráfica

## Inicio

Ejecuta DTS sin argumentos para abrir la interfaz gráfica:

```bash
dts
```

## Pantalla de bienvenida

Al iniciar, verás la pantalla de bienvenida con las siguientes opciones:

- **Abrir proyecto**: selecciona un directorio de proyecto existente
- **Crear proyecto**: crea un nuevo proyecto en el directorio que elijas
- **Configuración global**: accede a la configuración de API keys, UMT y más
- **Proyectos recientes**: lista de proyectos abiertos anteriormente (doble clic para abrir)

## Vista de proyecto

Una vez abierto o creado un proyecto, se muestra un panel con 4 pestañas:

### 1. Resumen (Overview)

Muestra información general del proyecto y el estado del pipeline:

- **Información del proyecto**: directorio, proveedor, modelo, chunk size, ruta de data.win
- **Estado del pipeline**: cada paso del proceso tiene un checkmark o cruz
- **Acciones**:
  - **Seleccionar data.win**: si UMT está configurado, extrae strings automáticamente. Si no, ofrece cargar `strings.json` manualmente o ir a configuración de UMT.
  - **Cargar strings.json manualmente**: para proyectos donde ya tienes el archivo extraído
  - **Ver diálogos**: abre un popup con todos los diálogos (solo lectura)

### 2. Traducir (Translate)

Interfaz para ejecutar la traducción:

- **Configuración**:
  - **Proveedor**: selector de proveedor de IA (solo aparecen los que tienen API key configurada u Ollama detectado)
  - **Modelo**: selector de modelo, se actualiza según el proveedor seleccionado
  - **Chunk size**: número de diálogos por lote (10-1000)
- **Barra de progreso**: muestra el avance de la traducción
- **Botón Iniciar/Cancelar**: inicia o detiene la traducción
- **Panel inferior** con dos pestañas:
  - **Prompt**: muestra el prompt de traducción (solo lectura)
  - **Logs**: registro detallado del proceso con códigos de colores

La traducción se ejecuta en segundo plano, procesando los diálogos no traducidos en lotes.

### 3. Revisión (Review)

Para revisar y editar traducciones pendientes:

- **Contadores**: total / traducidos / pendientes
- **Botones**:
  - **Pull pendientes**: genera archivo con diálogos no traducidos para edición manual
  - **Guardar cambios**: aplica las ediciones manuales al archivo de salida
- **Filtro**: checkbox "Mostrar solo pendientes de revisión" (activado por defecto)
- **Tabla**: columnas Key ID, Original, Traducción
  - Las filas pendientes tienen fondo naranja oscuro
  - Las filas vacías/inválidas tienen fondo rojo oscuro
- **Edición**: doble clic en una fila abre un editor donde puedes modificar la traducción. Guardar escribe en `lang_manual_edit.json`.

### 4. Exportar (Export)

Tres modos de exportación:

1. **Exportar como `strings_es.json`**:
   - Checkbox "Normalizar caracteres especiales (seguro para GML)"
   - Guarda el archivo con las traducciones aplicadas

2. **Exportar como `data.win`** (basado en el original):
   - Requiere UMT configurado y data.win seleccionado
   - Genera un nuevo `data.win` con los diálogos traducidos insertados

3. **Parchear otro `data.win`**:
   - Selecciona un `data.win` diferente al original
   - Extrae sus strings, fusiona las traducciones, y re-importa
   - Útil para traducir diferentes versiones del mismo juego

## Configuración global

Accesible desde la pantalla de bienvenida o desde cualquier proyecto (botón "Config global").

### Pestaña: Proveedor de IA

Selecciona el proveedor en la lista lateral para configurarlo:

| Proveedor | Configuración | Modelos |
|---|---|---|
| **Gemini** | API key(s) | gemini-3.5-flash, 3.1-pro-preview, 3.1-flash-lite, 3.0-deep-think, 2.5-pro, 2.5-flash |
| **Groq** | API key | openai/gpt-oss-20b, gpt-oss-120b, qwen/qwen3.6-27b |
| **DeepInfra** | API key | DeepSeek-V4-Flash, Llama-3.3-70B, Qwen2.5-72B |
| **Together AI** | API key | Qwen3.7-Plus, Llama-3-8B-Lite |
| **Anthropic** | API key | claude-3.5-sonnet, claude-3.5-haiku |
| **OpenAI** | API key | gpt-4o-mini, gpt-4o |
| **Ollama** | Host, Puerto, Timeout | Detecta modelos instalados automáticamente |

### Pestaña: Motor (UMT)

Configuración de UndertaleModTool:

- **Estado**: muestra si el CLI y scripts están disponibles
- **Método manual**: selecciona la carpeta donde tienes instalado UMT
- **Descarga automática**: descarga UMT CLI desde GitHub con barra de progreso

### Pestaña: Configuración del Proyecto

Información de solo lectura del proyecto actual: proveedor, modelo, chunk size, rutas de archivos.

## Notas importantes

- **Cierre sin exportar**: si cierras un proyecto sin exportar, se te preguntará si deseas hacerlo.
- **Proyectos independientes**: 1 proyecto = 1 `data.win`. Juegos con múltiples `data.win` requieren proyectos separados.
- **Archivos generados**: todos los archivos se guardan dentro del directorio del proyecto.
