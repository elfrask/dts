# DTS v2 — Dialogue Translation System

**DTS (Dialogue Translation System)** es una herramienta para traducir diálogos de videojuegos (GameMaker) del inglés al español usando APIs de inteligencia artificial. Soporta múltiples proveedores de IA, interfaz gráfica (GUI) y línea de comandos (CLI), y se integra con UndertaleModTool (UMT) para extraer y reinsertar strings directamente en archivos `data.win`.

## Características

- **Múltiples proveedores de IA**: Gemini, OpenAI, Anthropic (Claude), Groq, DeepInfra, Together AI, y Ollama (local).
- **Dos interfaces**: GUI gráfica (ttkbootstrap) y CLI completa (Click).
- **Sistema de proyectos**: cada proyecto tiene su propia configuración, archivos de entrada/salida y estado.
- **Pipeline automatizado**: extraer strings → traducir → normalizar → exportar.
- **Post-procesamiento**: normalización de caracteres, limpieza de valores vacíos, preservación de comandos especiales.
- **Integración UMT**: extracción e importación directa desde/hacia archivos `data.win`.

## Flujo de trabajo

```
                   ┌──────────────── GUI ────────────────┐
                   │                                      │
data.win ──→ [extraer con UMT] ──→ strings.json ──→ lang_input.json
                                                              │
                                                         [traducir]
                                                              │
                                                   lang_es_out.json
                                                              │
                                               ┌──────────────┴──────────────┐
                                               │                             │
                                         [Exportar]                  [Parchear otro
                                          strings_es.json             data.win]
                                          (normaliza si el check       │
                                           está activo)                │
                                               │                   extraer → fusionar
                                         [Exportar data.win]        → reimportar
                                          (misma normalización)
```

## Enlaces rápidos

- [Instalación](installation.md)
- [CLI - Línea de comandos](cli.md)
- [GUI - Interfaz gráfica](gui.md)
- [Configuración de proveedores](providers.md)
- [Configuración de archivos](configuration.md)
