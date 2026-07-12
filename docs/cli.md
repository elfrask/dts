# CLI — Interfaz de línea de comandos

## Uso básico

```bash
dts [OPCIONES GLOBALES] <COMANDO> [OPCIONES]
```

## Opciones globales

| Opción | Descripción |
|---|---|
| `--project-dir, -p <ruta>` | Directorio del proyecto (por defecto: directorio actual) |
| `--help` | Muestra ayuda del comando |

## Comandos

### `input-generate`

Genera `lang_input.json` a partir de `strings.json`.

```bash
dts input-generate
```

Extrae los diálogos del archivo `strings.json` usando un regex que identifica las claves con formato `nombre_slash_nombre_gml_N_N` y asigna cada clave a su diálogo correspondiente.

### `run`

Ejecuta la traducción usando el proveedor y modelo configurados.

```bash
dts run [--chunk-size N]
```

| Opción | Descripción |
|---|---|
| `--chunk-size N` | Sobrescribe el tamaño de lote configurado para esta ejecución |

Traduce los diálogos de `lang_input.json` que aún no están en `lang_es_out.json`, en lotes (chunks). Soporta cancelación y reintentos automáticos.

### `apply`

Aplica las traducciones normalizadas a los strings originales.

```bash
dts apply
```

Lee `strings.json` (original) y `lang_es_normalize.json` (traducciones normalizadas), aplica las traducciones preservando comandos especiales, y escribe `strings_es.json`.

### `fix`

Re-aplica traducciones sobre un `strings_es.json` existente (modo fix).

```bash
dts fix
```

Similar a `apply`, pero usa `strings_es.json` como origen en vez de `strings.json`, y activa modo de reparación.

### `normalice`

Normaliza caracteres especiales en las traducciones.

```bash
dts normalice [--secure] [--old]
```

| Opción | Descripción |
|---|---|
| `--secure` | Elimina tildes y caracteres especiales (seguro para GML) |
| `--old` | Usa el normalizador antiguo (`clean_normalice`) en vez del nuevo |

Lee `lang_es_out.json` y escribe `lang_es_normalize.json`, preservando intacto el archivo original.

### `normalice-old`

Alias de `normalice --old`.

### `voids`

Elimina traducciones vacías o inválidas.

```bash
dts voids
```

Compara `lang_es_out.json` contra `lang_input.json` y remueve entradas que están vacías, son inválidas o contienen solo prefijos.

### `clean`

Limpia valores con prefijos de código.

```bash
dts clean
```

Procesa `lang_es_out.json` eliminando prefijos no deseados de los valores traducidos.

### `merge`

Fusiona archivos de entrada y salida.

```bash
dts merge
```

Carga `lang_input.json` y superpone `lang_es_out.json`, escribiendo el resultado fusionado en `lang_es_out.json`.

### `pull-manual`

Genera archivo con diálogos pendientes de traducción manual.

```bash
dts pull-manual
```

Compara `lang_input.json` vs `lang_es_out.json` y escribe las claves faltantes en `lang_manual_edit.json`.

### `apply-manual`

Aplica las ediciones manuales desde `lang_manual_edit.json`.

```bash
dts apply-manual
```

Lee el archivo de ediciones manuales y las fusiona en `lang_es_out.json`.

### `view`

Muestra el progreso de traducción.

```bash
dts view
```

Imprime: total de diálogos, traducidos, pendientes.

### `settings`

Gestiona la configuración del proyecto actual.

```bash
dts settings [--show] [--provider PROVIDER] [--model MODEL] [--chunk-size N]
```

| Opción | Descripción |
|---|---|
| `--show` | Muestra la configuración actual del proyecto |
| `--provider {gemini,ollama,groq,deepinfra,together,anthropic,openai}` | Cambia el proveedor de IA |
| `--model <nombre>` | Cambia el modelo activo |
| `--chunk-size N` | Cambia el tamaño de lote |

### `config`

Gestiona la configuración global de la aplicación.

```bash
dts config [--show] [--add-key KEY] [--ollama-host HOST] [--ollama-timeout S]
```

| Opción | Descripción |
|---|---|
| `--show` | Muestra la configuración global (API keys ocultas) |
| `--add-key KEY` | Agrega una clave de API para Gemini |
| `--ollama-host HOST` | Establece el host de Ollama |
| `--ollama-timeout S` | Establece el timeout de Ollama en segundos |

### `help`

Muestra un resumen de todos los comandos disponibles.

```bash
dts help
```

## Pipeline completo típico

```bash
# 1. Generar input desde strings.json
dts input-generate

# 2. Traducir
dts run

# 3. Normalizar
dts normalice --secure

# 4. Aplicar traducciones a strings originales
dts apply

# 5. (Opcional) Revisar pendientes
dts pull-manual
# editar lang_manual_edit.json manualmente
dts apply-manual

# 6. Ver progreso
dts view
```
