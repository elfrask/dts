import logging
import threading
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.config.settings import load_app_settings, save_app_settings, save_project
from src.config.defaults import (
    DEFAULT_PROMPT, DEFAULT_OLLAMA_SINGLE_PROMPT, PROVIDER_MODELS,
    OPENAI_COMPATIBLE_BASE_URLS,
)
from src.core.provider import create_provider
from src.core.translator import use_translate
from src.core.events import EventBus, Signal, get_event_bus
from src.core.model_catalog import fetch_models, fetch_ollama_models

def _builtin_base_url(provider: str) -> str:
    if provider == "openai":
        return "https://api.openai.com/v1"
    return OPENAI_COMPATIBLE_BASE_URLS.get(provider, "")


# ── Logging handler that forwards to the GUI ────────────────────

class _GuiLogHandler(logging.Handler):
    """Sends Python logging messages to the translate tab's log widget."""

    def __init__(self, log_callback: callable) -> None: #type: ignore
        super().__init__()
        self._callback = log_callback

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        is_error = record.levelno >= logging.ERROR
        try:
            self._callback(msg, is_error)
        except Exception:
            self.handleError(record)


class TranslateTab(ttk.Frame):
    def __init__(self, parent: ttk.Window, state) -> None:
        super().__init__(parent, padding=15)
        self.state = state
        self._running = False
        self._cancel_event = threading.Event()
        self._log_handler: logging.Handler = None #type: ignore
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build()

        # Register once on the shared bus so the audit tab receives events too.
        self._event_bus = get_event_bus()
        self._event_bus.on(Signal.PROGRESS, self._on_progress)
        self._event_bus.on(Signal.LOG, self._on_log_event)
        self._event_bus.on(Signal.ERROR, self._on_error_event)
        self._event_bus.on(Signal.COMPLETE, self._on_complete_event)
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event) -> None:
        if event.widget is not self:
            return
        try:
            self._event_bus.off(Signal.PROGRESS, self._on_progress)
            self._event_bus.off(Signal.LOG, self._on_log_event)
            self._event_bus.off(Signal.ERROR, self._on_error_event)
            self._event_bus.off(Signal.COMPLETE, self._on_complete_event)
        except Exception:
            pass

    def _build(self) -> None:
        project = self.state.project #type: ignore
        if not project:
            ttk.Label(self, text="No hay proyecto abierto").pack()
            return

        # ── Config row ─────────────────────────────────────────
        cfg_frame = ttk.Labelframe(self, text="Configuración de traducción", padding=10)
        cfg_frame.pack(fill=X, pady=(0, 10))
        cfg_frame.columnconfigure(1, weight=1)

        ttk.Label(cfg_frame, text="Proveedor:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=3, padx=(0, 8))
        current_provider = str(getattr(project.config.provider, "value", project.config.provider))
        self._provider_var = tk.StringVar(value=current_provider)
        self._provider_combo = ttk.Combobox(
            cfg_frame, textvariable=self._provider_var, state="readonly", width=20)
        self._provider_combo.grid(row=0, column=1, sticky="w", pady=3)
        self._provider_combo.bind("<<ComboboxSelected>>", self._on_provider_change)

        ttk.Label(cfg_frame, text="Modelo:", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", pady=3, padx=(0, 8))
        self._model_var = tk.StringVar(value=project.config.model)
        self._model_combo = ttk.Combobox(
            cfg_frame, textvariable=self._model_var, state="normal", width=30)
        self._model_combo.grid(row=1, column=1, sticky="w", pady=3)
        self._model_combo.bind("<<ComboboxSelected>>", self._save_config)
        self._model_combo.bind("<FocusOut>", self._save_config)
        self._model_combo.bind("<Return>", self._save_config)

        self._refresh_btn = ttk.Button(
            cfg_frame, text="Actualizar modelos", command=self._refresh_models,
            bootstyle="secondary-outline", width=18,
        )
        self._refresh_btn.grid(row=1, column=2, sticky="w", pady=3, padx=(8, 0))

        ttk.Label(cfg_frame, text="Chunk size:", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=3, padx=(0, 8))
        self._chunk_var = tk.IntVar(value=project.config.chunk_size)
        self._chunk_spin = ttk.Spinbox(
            cfg_frame, from_=10, to=1000, textvariable=self._chunk_var,
            width=10, increment=10,
        )
        self._chunk_spin.grid(row=2, column=1, sticky="w", pady=3)
        ttk.Label(cfg_frame, text="diálogos por petición", font=("Segoe UI", 9)).grid(
            row=2, column=2, sticky="w", pady=3, padx=(6, 0))
        self._chunk_spin.bind("<FocusOut>", self._save_config)
        self._chunk_spin.bind("<Return>", self._save_config)

        # Single-translate checkbox (only visible for Ollama)
        self._single_var = tk.BooleanVar(value=project.config.single_translate)
        self._single_check = ttk.Checkbutton(
            cfg_frame, text="Traducir diálogo por diálogo (para modelos Ollama pequeños)",
            variable=self._single_var, bootstyle="round-toggle",
            command=self._on_single_toggle,
        )
        self._single_check.grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self._single_label = ttk.Label(
            cfg_frame,
            text="Evita errores de formato JSON con modelos locales pequeños. "
                 "Cada diálogo se envía como texto plano, uno por uno.",
            font=("Segoe UI", 8),
            bootstyle="secondary",
        )
        self._single_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(0, 3))
        self._update_single_ui()

        # Fast mode: skip the 7s pause between cloud batches
        self._paused_var = tk.BooleanVar(value=not project.config.paused_mode)
        ttk.Checkbutton(
            cfg_frame,
            text="Desactivar pausa entre lotes (modo rápido)",
            variable=self._paused_var,
            bootstyle="round-toggle",
            command=self._on_pause_toggle,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))

        self._populate_providers()

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=5)

        # ── Progress ───────────────────────────────────────────
        self._progress_var = ttk.IntVar()
        self._progress_bar = ttk.Progressbar(
            self, variable=self._progress_var, maximum=100,
            bootstyle="success-striped",
        )
        self._progress_bar.pack(fill=X, pady=(0, 5))

        self._status_label = ttk.Label(self, text="Listo para traducir", font=("Segoe UI", 10))
        self._status_label.pack(anchor="w", pady=(0, 5))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(anchor="w", pady=(0, 10))

        self._start_btn = ttk.Button(
            btn_frame, text="Iniciar traducción",
            command=self._toggle_translation,
            bootstyle="success", width=20,
        )
        self._start_btn.pack(side=LEFT, padx=(0, 10))

        # ── Bottom notebook: Prompt + Logs ─────────────────────
        self._bottom_notebook = ttk.Notebook(self)
        self._bottom_notebook.pack(fill=BOTH, expand=True)

        self._build_prompt_tab()
        self._build_logs_tab()

    def _build_prompt_tab(self) -> None:
        prompt_frame = ttk.Frame(self._bottom_notebook, padding=10)
        prompt_frame.columnconfigure(0, weight=1)
        prompt_frame.rowconfigure(0, weight=1)
        self._bottom_notebook.add(prompt_frame, text="Prompt")

        sub = ttk.Notebook(prompt_frame)
        sub.grid(row=0, column=0, sticky="nsew")

        def _make_pane(label: str, text: str) -> None:
            f = ttk.Frame(sub, padding=5)
            f.columnconfigure(0, weight=1)
            f.rowconfigure(0, weight=1)
            sub.add(f, text=label)
            txt = tk.Text(
                f, wrap="word", font=("Consolas", 10),
                height=12, relief="flat", borderwidth=1,
                highlightthickness=1, highlightbackground="#444",
                state="disabled",
            )
            txt.grid(row=0, column=0, sticky="nsew")
            txt.configure(state="normal")
            txt.insert("1.0", text)
            txt.configure(state="disabled")
            scr = ttk.Scrollbar(f, orient=VERTICAL, command=txt.yview)
            txt.configure(yscrollcommand=scr.set)
            scr.grid(row=0, column=1, sticky="ns")

        _make_pane("Por lotes (batch)", DEFAULT_PROMPT)
        _make_pane("Individual (Ollama)", DEFAULT_OLLAMA_SINGLE_PROMPT)

    def _build_logs_tab(self) -> None:
        log_frame = ttk.Frame(self._bottom_notebook, padding=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self._bottom_notebook.add(log_frame, text="Logs")

        self._log_text = tk.Text(
            log_frame, wrap="word", font=("Consolas", 10),
            height=12, relief="flat", borderwidth=1,
            highlightthickness=1, highlightbackground="#444",
            state="disabled",
        )
        self._log_text.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

    # ── Provider / Model ───────────────────────────────────────

    def _populate_providers(self) -> None:
        app_cfg = load_app_settings()
        available = []
        for pname, pkeys in app_cfg.providers.items():
            if app_cfg.is_custom_provider(pname):
                continue
            if pname == "ollama":
                if self._detect_ollama():
                    available.append(pname)
            elif any(k.enabled and k.key for k in pkeys.keys):
                available.append(pname)

        # Enabled custom providers with at least one key
        for cp in app_cfg.custom_providers:
            if not cp.enabled:
                continue
            keys = app_cfg.get_active_keys(cp.name)
            if keys and cp.name not in available:
                available.append(cp.name)

        if not available:
            available = ["gemini", "ollama" if self._detect_ollama() else None]
            available = [p for p in available if p]
        self._provider_combo["values"] = available
        current = self._provider_var.get()
        if current not in available:
            self._provider_var.set(available[0])
        self._populate_models()

    def _on_provider_change(self, event=None) -> None:
        # Force-disable single_translate for non-Ollama providers
        if self._provider_var.get() != "ollama":
            self._single_var.set(False)
        self._update_single_ui()
        self._populate_models()
        self._save_config()

    def _static_models(self, provider: str) -> list[str]:
        """Models known without hitting the network."""
        if provider == "ollama":
            return self._detect_ollama_models() or PROVIDER_MODELS.get("ollama", [])
        app_cfg = load_app_settings()
        custom = app_cfg.get_custom_provider(provider)
        if custom is not None:
            return list(custom.models)
        return PROVIDER_MODELS.get(provider, [])

    def _populate_models(self) -> None:
        provider = self._provider_var.get()
        models = self._static_models(provider)
        self._model_combo["values"] = models
        current = self._model_var.get()
        if models and current not in models:
            self._model_var.set(models[0])
        self._save_config()

    def _refresh_models(self) -> None:
        """Ask the provider for its live model catalog (runs off the UI thread)."""
        provider = self._provider_var.get()
        app_cfg = load_app_settings()
        custom = app_cfg.get_custom_provider(provider)
        self._refresh_btn.configure(state=DISABLED, text="Cargando...")

        def worker() -> None:
            try:
                if provider == "ollama":
                    models = fetch_ollama_models(app_cfg.ollama.host, app_cfg.ollama.port)
                else:
                    if custom is not None:
                        keys = app_cfg.get_active_keys(custom.name)
                        models = fetch_models(
                            custom.api_type,
                            keys[0] if keys else "",
                            custom.base_url,
                        )
                    else:
                        keys = app_cfg.get_active_keys(provider)
                        if provider == "gemini":
                            api_type = "gemini"
                        elif provider == "anthropic":
                            api_type = "anthropic"
                        elif provider == "commandcode":
                            api_type = "commandcode"
                        else:
                            api_type = "openai"
                        models = fetch_models(
                            api_type,
                            keys[0] if keys else "",
                            _builtin_base_url(provider),
                        )
            except Exception as e:
                models = []
                logging.getLogger(__name__).warning("Refresh models failed: %s", e)

            def apply() -> None:
                try:
                    self._refresh_btn.configure(state=NORMAL, text="Actualizar modelos")
                    if models:
                        self._model_combo["values"] = models
                        if self._model_var.get() not in models:
                            self._model_var.set(models[0])
                        self._save_config()
                        # Cache discovered models on the custom provider
                        if custom is not None:
                            custom.models = list(models)
                            try:
                                save_app_settings(app_cfg)
                            except Exception:
                                pass
                        self._log(f"Modelos actualizados: {len(models)} disponibles")
                    else:
                        self._log("No se pudieron cargar modelos del proveedor", error=True)
                except tk.TclError:
                    pass

            self.after_idle(apply)

        threading.Thread(target=worker, daemon=True).start()

    def _update_single_ui(self) -> None:
        is_ollama = self._provider_var.get() == "ollama"
        active = is_ollama and self._single_var.get()
        if is_ollama:
            self._single_check.grid()
            self._single_label.grid()
        else:
            self._single_check.grid_remove()
            self._single_label.grid_remove()
        self._chunk_spin.configure(state="disabled" if active else "normal")

    def _on_single_toggle(self) -> None:
        self._update_single_ui()
        self._save_config()

    def _on_pause_toggle(self) -> None:
        project = self.state.project  # type: ignore
        if not project:
            return
        project.config.paused_mode = not self._paused_var.get()
        save_project(project)

    def _detect_ollama(self) -> bool:
        app_cfg = load_app_settings()
        try:
            import urllib.request
            url = f"{app_cfg.ollama.host}:{app_cfg.ollama.port}/api/tags"
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            return False

    def _detect_ollama_models(self) -> list[str]:
        app_cfg = load_app_settings()
        try:
            import urllib.request, json
            url = f"{app_cfg.ollama.host}:{app_cfg.ollama.port}/api/tags"
            resp = urllib.request.urlopen(url, timeout=3)
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def _save_config(self, event=None) -> None:
        project = self.state.project #type: ignore
        if not project:
            return
        project.config.provider = self._provider_var.get()
        project.config.model = self._model_var.get()
        project.config.chunk_size = self._chunk_var.get()
        project.config.single_translate = self._single_var.get()
        save_project(project)

    # ── Translation ────────────────────────────────────────────

    def _toggle_translation(self) -> None:
        if self._running:
            self._cancel()
        else:
            self._start_translation()

    def _cancel(self) -> None:
        self._cancel_event.set()
        self._log("Cancelando... (espera a que termine el lote actual)")
        self._start_btn.configure(state=DISABLED, text="Cancelando...")

    def _start_translation(self) -> None:
        project = self.state.project #type: ignore
        if not project:
            return
        if not project.input_file_path.exists():
            self._log("Ejecuta Extraer y generar input primero")
            self._status_label.configure(text="No hay input generado")
            return

        self._save_config()
        self._cancel_event.clear()
        self._running = True
        self._start_btn.configure(text="Cancelar", bootstyle="danger", state=NORMAL)
        self._status_label.configure(text="Iniciando traducción...")
        self._clear_log()

        # ── Hook Python logging into the GUI log ──
        self._log_handler = _GuiLogHandler(self._log)
        self._log_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
        logging.getLogger().addHandler(self._log_handler)

        self._log("=== Iniciando traducción ===")
        self._log(f"Proveedor: {getattr(project.config.provider, 'value', project.config.provider)}")
        self._log(f"Modelo: {project.config.model}")
        self._log(f"Chunk size: {project.config.chunk_size}")
        self._log(f"Modo: {'diálogo por diálogo' if project.config.single_translate else 'por lotes (batch)'}")
        self._log(f"Input: {project.input_file_path}")
        self._log(f"Output: {project.output_file_path}")

        app_cfg = load_app_settings()
        event_bus = self._event_bus

        cancel_event = self._cancel_event

        def worker():
            try:
                provider = create_provider(app_cfg, project.config)
                use_translate(
                    provider=provider,
                    config=project.config,
                    input_path=project.input_file_path,
                    output_path=project.output_file_path,
                    event_bus=event_bus,
                    is_cancelled=lambda: cancel_event.is_set(),
                )
            except Exception as e:
                self._finish(False, f"Error: {e}")
                self._log(f"ERROR: {e}", error=True)

        threading.Thread(target=worker, daemon=True).start()

    def _on_progress(self, current: int, total: int, **kw) -> None:
        pct = int((current / total) * 100) if total else 0
        self._progress_var.set(pct)
        self._status_label.configure(text=f"Traduciendo... {current} / {total}")

    def _on_log_event(self, level: str, message: str, **kw) -> None:
        self._log(f"[{level}] {message}")

    def _on_error_event(self, message: str, **kw) -> None:
        self._log(f"{message}", error=True)

    def _on_complete_event(self, result=None, **kw) -> None:
        msg = str(result) if result else "Traducción completada"
        self._finish(True, f"{msg}")

    def _finish(self, success: bool, msg: str) -> None:
        self._running = False
        self._start_btn.configure(
            text="Iniciar traducción", bootstyle="success", state=NORMAL)
        self._status_label.configure(text=msg)
        self._progress_var.set(100 if success else 0)
        self._log(msg)

        # ── Remove the GUI log handler ──
        if self._log_handler:
            logging.getLogger().removeHandler(self._log_handler)
            self._log_handler = None #type: ignore

    def _log(self, msg: str, error: bool = False) -> None:
        def _insert():
            try:
                self._log_text.configure(state="normal")
                tag = "error" if error else "info"
                self._log_text.insert("end", msg + "\n", tag)
                self._log_text.see("end")
                self._log_text.configure(state="disabled")
            except tk.TclError:
                pass  # widget destroyed
        # Thread-safe: schedule on the main thread
        if threading.current_thread() is threading.main_thread():
            _insert()
        else:
            self.after_idle(_insert)

    def _clear_log(self) -> None:
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")
