import tkinter as tk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from src.io.formats import AppConfig, OllamaConfig, ProviderKeys, ApiKeyEntry
from src.config.defaults import (
    PROVIDER_MODELS,
    GEMINI_MODELS as _GEMINI_MODELS,
    ANTHROPIC_MODELS as _ANTHROPIC_MODELS,
    OPENAI_MODELS as _OPENAI_MODELS,
    GROQ_MODELS as _GROQ_MODELS,
    DEEPINFRA_MODELS as _DEEPINFRA_MODELS,
    TOGETHER_MODELS as _TOGETHER_MODELS,
)


class ProviderTab(ttkb.Frame):
    def __init__(self, parent: ttkb.Window, config: AppConfig) -> None:
        super().__init__(parent, padding=10)
        self._config = config
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Left: provider list
        left = ttkb.Frame(self, width=140)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left.grid_propagate(False)

        ttkb.Label(left, text="Proveedores", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self._provider_listbox = tk.Listbox(
            left,
            font=("Segoe UI", 11),
            selectbackground="#375a7f",
            selectforeground="white",
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
            height=8,
        )
        self._provider_listbox.pack(fill=BOTH, expand=True, pady=(5, 0))
        self._provider_listbox.bind("<<ListboxSelect>>", self._on_provider_select)

        # Right: config area
        self._config_frame = ttkb.Frame(self)
        self._config_frame.grid(row=0, column=1, sticky="nsew")
        self._config_frame.columnconfigure(0, weight=1)
        self._config_frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(self._config_frame, highlightthickness=0)
        scrollbar = ttkb.Scrollbar(self._config_frame, orient=VERTICAL, command=canvas.yview)
        self._inner = ttkb.Frame(canvas)

        self._inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Provider list: cloud key-based first, then local
        self._provider_order = ["gemini", "groq", "deepinfra", "together", "anthropic", "openai", "ollama"]

        for pname in self._provider_order:
            if pname not in config.providers:
                config.providers[pname] = ProviderKeys()
            self._provider_listbox.insert(END, pname)

        if self._provider_listbox.size() > 0:
            self._provider_listbox.selection_set(0)
            self._on_provider_select()

    # ── Shared helpers ──────────────────────────────────────────

    def _build_api_key_section(self, provider_name: str, title: str) -> None:
        """Build the API key list UI. Stores vars under self._current_key_vars."""
        ttkb.Label(self._inner, text=title, font=("Segoe UI", 13, "bold")).pack(
            anchor="w", pady=(0, 10))

        header = ttkb.Frame(self._inner)
        header.pack(fill=X)
        ttkb.Label(header, text="Habilitada", width=10).pack(side=LEFT, padx=(0, 5))
        ttkb.Label(header, text="Nombre", width=18).pack(side=LEFT, padx=5)
        ttkb.Label(header, text="API Key", width=40).pack(side=LEFT, padx=5)

        self._current_key_rows = ttkb.Frame(self._inner)
        self._current_key_rows.pack(fill=X, pady=5)

        self._current_key_vars: list[dict] = []
        for entry in self._get_provider(provider_name).keys:
            self._add_key_row(entry)

        btn_row = ttkb.Frame(self._inner)
        btn_row.pack(fill=X, pady=(5, 15))

        ttkb.Button(
            btn_row, text="+ Agregar key",
            command=lambda: self._add_key_row(ApiKeyEntry()),
            bootstyle="success-outline", width=14,
        ).pack(side=LEFT, padx=(0, 6))
        ttkb.Button(
            btn_row, text="− Eliminar seleccionada",
            command=self._remove_current_key,
            bootstyle="danger-outline", width=20,
        ).pack(side=LEFT)

    def _build_model_section(self, models: list[tuple[str, str, str]]) -> None:
        """Build model checkbox list. Stores vars under self._current_model_vars."""
        ttkb.Label(self._inner, text="Modelos disponibles", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", pady=(10, 5))

        self._current_model_vars: dict[str, tk.BooleanVar] = {}
        for name, api_id, desc in models:
            var = tk.BooleanVar(value=True)
            row = ttkb.Frame(self._inner)
            row.pack(fill=X, padx=10, pady=2)
            ttkb.Checkbutton(row, variable=var, bootstyle="round-toggle").pack(side=LEFT)
            ttkb.Label(row, text=name, font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(6, 0))
            ttkb.Label(row, text=f"({api_id})", font=("Segoe UI", 9), bootstyle="secondary").pack(
                side=LEFT, padx=(4, 0))
            ttkb.Label(row, text=desc, font=("Segoe UI", 9), bootstyle="secondary").pack(
                side=LEFT, padx=(10, 0))
            self._current_model_vars[api_id] = var

    def _add_key_row(self, entry: ApiKeyEntry) -> None:
        row = ttkb.Frame(self._current_key_rows)
        row.pack(fill=X, pady=2)

        enabled_var = tk.BooleanVar(value=entry.enabled)
        ttkb.Checkbutton(row, variable=enabled_var, bootstyle="round-toggle").pack(
            side=LEFT, padx=(0, 5))

        name_var = tk.StringVar(value=entry.name)
        ttkb.Entry(row, textvariable=name_var, width=18).pack(side=LEFT, padx=5)

        key_var = tk.StringVar(value=entry.key)
        key_e = ttkb.Entry(row, textvariable=key_var, width=40, show="*")
        key_e.pack(side=LEFT, padx=5)

        def _toggle(e=None, entry=key_e):
            entry.configure(show="" if entry.cget("show") == "*" else "*")

        ttkb.Button(row, text="👁", command=_toggle, width=3, bootstyle="secondary-outline").pack(
            side=LEFT, padx=2)

        self._current_key_vars.append({
            "enabled": enabled_var, "name": name_var, "key": key_var, "frame": row,
        })

    def _remove_current_key(self) -> None:
        if self._current_key_vars:
            kv = self._current_key_vars.pop()
            kv["frame"].destroy()

    def _get_provider(self, name: str) -> ProviderKeys:
        return self._config.providers.setdefault(name, ProviderKeys())

    def _read_current_keys(self, provider_name: str) -> list[ApiKeyEntry]:
        """Read key vars into a list of ApiKeyEntry."""
        entries: list[ApiKeyEntry] = []
        for kv in self._current_key_vars:
            name = kv["name"].get().strip()
            key = kv["key"].get().strip()
            if name or key:
                entries.append(ApiKeyEntry(
                    name=name or f"key{len(entries)+1}",
                    key=key,
                    enabled=kv["enabled"].get(),
                ))
        return entries

    # ── Provider selection ─────────────────────────────────────

    def _on_provider_select(self, event=None) -> None:
        sel = self._provider_listbox.curselection()
        if not sel:
            return
        pname = self._provider_listbox.get(sel[0])

        for w in self._inner.winfo_children():
            w.destroy()

        self._current_key_vars = []
        self._current_model_vars = {}
        self._current_provider_name = pname

        if pname == "gemini":
            self._build_gemini()
        elif pname == "ollama":
            self._build_ollama()
        elif pname == "groq":
            self._build_api_key_section("groq", "Groq — Ultra Velocidad")
            self._build_model_section([
                ("GPT-OSS 20B", "openai/gpt-oss-20b",
                 "Superveloz, ideal para strings comunes."),
                ("GPT-OSS 120B", "openai/gpt-oss-120b",
                 "Alta capacidad para mantener formato JSON."),
                ("Qwen 3.6 27B", "qwen/qwen3.6-27b",
                 "Excelente con caracteres asiáticos y variables de código."),
            ])
        elif pname == "deepinfra":
            self._build_api_key_section("deepinfra", "DeepInfra — Bajo Coste")
            self._build_model_section([
                ("DeepSeek V4 Flash", "deepseek-ai/DeepSeek-V4-Flash",
                 "Rápido y económico para estructurar datos."),
                ("Llama 3.3 70B Turbo", "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                 "Gran comprensión de contextos y chistes."),
                ("Qwen 2.5 72B Instruct", "Qwen/Qwen2.5-72B-Instruct",
                 "Meticuloso respetando variables de formato."),
            ])
        elif pname == "together":
            self._build_api_key_section("together", "Together AI — Baja Latencia")
            self._build_model_section([
                ("Qwen 3.7 Plus", "together/Qwen3.7-Plus",
                 "Muy potente para coherencia de género y número."),
                ("Llama 3 8B Lite", "together/Llama-3-8B-Instruct-Lite",
                 "Modo económico de alta velocidad."),
            ])
        elif pname == "anthropic":
            self._build_api_key_section("anthropic", "Anthropic (Claude) — Casos Complejos")
            self._build_model_section([
                ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022",
                 "El mejor siguiendo reglas complejas. No rompe JSONs."),
                ("Claude 3.5 Haiku", "claude-3-5-haiku-20241022",
                 "Alternativa rápida y económica."),
            ])
        elif pname == "openai":
            self._build_api_key_section("openai", "OpenAI — Estándar Global")
            self._build_model_section([
                ("GPT-4o Mini", "gpt-4o-mini",
                 "Extremadamente barato. El caballo de batalla."),
                ("GPT-4o", "gpt-4o",
                 "Máxima inteligencia para textos enrevesados."),
            ])

    # ── Gemini ─────────────────────────────────────────────────

    def _build_gemini(self) -> None:
        self._build_api_key_section("gemini", "Gemini API Keys")
        self._build_model_section([
            ("Gemini 3.5 Flash (Recomendado)", "gemini-3.5-flash",
             "El más rápido e inteligente para código y automatización masiva."),
            ("Gemini 3.1 Pro (Preview)", "gemini-3.1-pro-preview",
             "Máxima capacidad para razonamiento complejo y lógica avanzada."),
            ("Gemini 3.1 Flash-Lite", "gemini-3.1-flash-lite",
             "Ultra rápido y ultra económico. Ideal para tareas sencillas."),
            ("Gemini 3.0 Deep Think", "gemini-3.0-deep-think",
             "Modelo especializado que piensa paso a paso antes de responder."),
            ("Gemini 2.5 Pro", "gemini-2.5-pro",
             "Modelo de razonamiento estable y de alta fiabilidad."),
            ("Gemini 2.5 Flash", "gemini-2.5-flash",
             "El caballo de batalla estándar para tareas generales del día a día."),
        ])

    # ── Ollama ─────────────────────────────────────────────────

    def _build_ollama(self) -> None:
        ttkb.Label(self._inner, text="Ollama (proveedor local)", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", pady=(0, 15))

        cfg = self._get_ollama_config()

        host_f = ttkb.Frame(self._inner); host_f.pack(fill=X, pady=5)
        ttkb.Label(host_f, text="Host:", width=12).pack(side=LEFT)
        self._ollama_host = tk.StringVar(value=cfg.host)
        ttkb.Entry(host_f, textvariable=self._ollama_host, width=30).pack(side=LEFT, padx=(10, 0))

        port_f = ttkb.Frame(self._inner); port_f.pack(fill=X, pady=5)
        ttkb.Label(port_f, text="Puerto:", width=12).pack(side=LEFT)
        self._ollama_port = tk.StringVar(value=str(cfg.port))
        ttkb.Entry(port_f, textvariable=self._ollama_port, width=10).pack(side=LEFT, padx=(10, 0))

        to_f = ttkb.Frame(self._inner); to_f.pack(fill=X, pady=5)
        ttkb.Label(to_f, text="Timeout (s):", width=12).pack(side=LEFT)
        self._ollama_timeout = tk.StringVar(value=str(cfg.timeout))
        ttkb.Entry(to_f, textvariable=self._ollama_timeout, width=10).pack(side=LEFT, padx=(10, 0))

        ttkb.Button(
            self._inner, text="Detectar modelos instalados",
            command=self._detect_models, bootstyle="info-outline",
        ).pack(anchor="w", pady=(15, 5))

        self._ollama_models = ttkb.Frame(self._inner)
        self._ollama_models.pack(fill=X, pady=(5, 0))

    def _detect_models(self) -> None:
        for w in self._ollama_models.winfo_children():
            w.destroy()

        host = self._ollama_host.get().strip()
        try:
            port = int(self._ollama_port.get().strip())
        except ValueError:
            port = 11434

        import urllib.request, json
        try:
            url = f"{host}:{port}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
                models = [m["name"] for m in data.get("models", [])]
        except Exception as e:
            ttkb.Label(self._ollama_models, text=f"Error: {e}", bootstyle="danger").pack(anchor="w")
            return

        if not models:
            ttkb.Label(self._ollama_models, text="No se encontraron modelos", bootstyle="warning").pack(anchor="w")
            return

        self._ollama_model_vars: dict[str, tk.BooleanVar] = {}
        for model in models:
            var = tk.BooleanVar(value=True)
            ttkb.Checkbutton(self._ollama_models, text=model,
                             variable=var, bootstyle="round-toggle").pack(anchor="w", padx=10, pady=1)
            self._ollama_model_vars[model] = var

        ttkb.Label(self._ollama_models, text=f"{len(models)} modelos encontrados",
                   font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w", pady=(5, 0))

    def _get_ollama_config(self) -> OllamaConfig:
        return self._config.ollama

    # ── Sync config from UI ────────────────────────────────────

    def update_config(self, config: AppConfig) -> None:
        # Save keys for the currently-selected provider
        if hasattr(self, "_current_key_vars") and hasattr(self, "_current_provider_name"):
            pname = self._current_provider_name
            # Skip ollama — it has no API keys
            if pname != "ollama":
                pkeys = config.providers.setdefault(pname, ProviderKeys())
                pkeys.keys = self._read_current_keys(pname)

        # Ollama (always saved, independent of current selection)
        try:
            port = int(self._ollama_port.get().strip())
        except (ValueError, AttributeError):
            port = 11434
        try:
            timeout = int(self._ollama_timeout.get().strip())
        except (ValueError, AttributeError):
            timeout = 120

        config.ollama = OllamaConfig(
            host=self._ollama_host.get().strip() if hasattr(self, "_ollama_host") else "http://localhost",
            port=port,
            timeout=timeout,
        )
