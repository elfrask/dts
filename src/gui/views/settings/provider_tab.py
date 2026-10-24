import re
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from src.io.formats import (
    AppConfig, OllamaConfig, ProviderKeys, ApiKeyEntry, CustomProviderConfig,
)
from src.config.defaults import BUILTIN_PROVIDERS, API_TYPES
from src.core.model_catalog import fetch_models


class ProviderTab(ttkb.Frame):
    def __init__(self, parent: ttkb.Window, config: AppConfig) -> None:
        super().__init__(parent, padding=10)
        self._config = config
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._current_provider_name: str | None = None
        self._current_custom_name: str | None = None
        self._current_key_vars: list[dict] = []
        self._current_model_vars: dict[str, tk.BooleanVar] = {}
        self._custom_models: list[str] = []

        # Left: provider list
        left = ttkb.Frame(self, width=160)
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
            height=10,
        )
        self._provider_listbox.pack(fill=BOTH, expand=True, pady=(5, 6))
        self._provider_listbox.bind("<<ListboxSelect>>", self._on_provider_select)

        ttkb.Button(
            left, text="+ Nuevo proveedor", command=self._add_custom_provider,
            bootstyle="success-outline", width=18,
        ).pack(fill=X, pady=(0, 4))
        ttkb.Button(
            left, text="− Eliminar", command=self._delete_custom_provider,
            bootstyle="danger-outline", width=18,
        ).pack(fill=X)

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

        self._refresh_provider_list()
        if self._provider_listbox.size() > 0:
            self._provider_listbox.selection_set(0)
            self._on_provider_select()

    # ── Provider list management ───────────────────────────────

    def _refresh_provider_list(self, select: str | None = None) -> None:
        self._provider_listbox.delete(0, END)
        names = list(BUILTIN_PROVIDERS)
        for cp in self._config.custom_providers:
            names.append(cp.name)
        for pname in names:
            if pname not in self._config.providers:
                self._config.providers[pname] = ProviderKeys()
            self._provider_listbox.insert(END, pname)

        if select and select in names:
            idx = names.index(select)
            self._provider_listbox.selection_clear(0, END)
            self._provider_listbox.selection_set(idx)
            self._provider_listbox.see(idx)
            self._on_provider_select()

    def _add_custom_provider(self) -> None:
        label = simpledialog.askstring(
            "Nuevo proveedor",
            "Nombre del proveedor (ej: Mi servidor local):",
            parent=self.winfo_toplevel(),
        )
        if not label:
            return
        name = self._slugify(label)
        if not name:
            messagebox.showerror("Error", "Nombre inválido.", parent=self.winfo_toplevel())
            return
        if name in BUILTIN_PROVIDERS or self._config.get_custom_provider(name):
            messagebox.showerror(
                "Error", f"Ya existe un proveedor llamado '{name}'.",
                parent=self.winfo_toplevel())
            return

        self._commit_custom_form()
        self._config.custom_providers.append(
            CustomProviderConfig(name=name, label=label.strip(), api_type="openai")
        )
        self._config.providers.setdefault(name, ProviderKeys())
        self._refresh_provider_list(select=name)

    def _delete_custom_provider(self) -> None:
        sel = self._provider_listbox.curselection()
        if not sel:
            return
        name = self._provider_listbox.get(sel[0])
        cp = self._config.get_custom_provider(name)
        if cp is None:
            messagebox.showinfo(
                "Proveedor integrado",
                "Solo puedes eliminar proveedores personalizados.",
                parent=self.winfo_toplevel(),
            )
            return
        if not messagebox.askyesno(
            "Eliminar proveedor",
            f"¿Eliminar '{cp.display_name}' y sus API keys?",
            parent=self.winfo_toplevel(),
        ):
            return

        self._config.custom_providers = [
            p for p in self._config.custom_providers if p.name != name
        ]
        self._config.providers.pop(name, None)
        self._current_custom_name = None
        self._refresh_provider_list()
        if self._provider_listbox.size() > 0:
            self._provider_listbox.selection_set(0)
            self._on_provider_select()

    @staticmethod
    def _slugify(text: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
        return slug

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

        self._current_key_vars = []
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

        self._current_model_vars = {}
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

        # Persist whatever the previously selected provider had on screen
        self._commit_custom_form()

        for w in self._inner.winfo_children():
            w.destroy()

        self._current_key_vars = []
        self._current_model_vars = {}
        self._current_provider_name = pname
        self._current_custom_name = None

        if self._config.get_custom_provider(pname) is not None:
            self._build_custom(pname)
            return

        if pname == "commandcode":
            self._build_api_key_section(
                "commandcode", "CommandCode — Todos los modelos, una API")
            self._build_model_section([
                ("DeepSeek V4.1 Flash", "deepseek/deepseek-v4.1-flash",
                 "Rápido y económico. Recomendado."),
                ("DeepSeek V4 Pro", "deepseek/deepseek-v4-pro",
                 "Razonamiento de contexto largo."),
                ("Claude Sonnet 5.5", "claude-sonnet-5-5",
                 "El mejor siguiendo instrucciones complejas."),
                ("Claude Haiku 5.5", "claude-haiku-5-5",
                 "Rápido y compacto."),
                ("GPT-5.6 Sol", "gpt-5.6-sol",
                 "Modelo frontera de OpenAI."),
                ("Gemini 3.8 Flash", "google/gemini-3.8-flash",
                 "Rápido y capaz."),
                ("GLM-5.3 Flash", "z-ai/glm-5.3-flash",
                 "Económico con 1M de contexto."),
            ])
            ttkb.Label(
                self._inner,
                text="Los modelos Claude se enrutan automáticamente por el endpoint "
                     "Anthropic (/v1/messages) y el resto por /v1/chat/completions. "
                     "El catálogo real se carga con «Actualizar modelos».",
                font=("Segoe UI", 9), bootstyle="secondary",
            ).pack(anchor="w", pady=(10, 0))
        elif pname == "gemini":
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

    # ── Custom provider form ───────────────────────────────────

    def _build_custom(self, name: str) -> None:
        cp = self._config.get_custom_provider(name)
        if cp is None:
            return
        self._current_custom_name = name
        self._custom_models = list(cp.models)

        ttkb.Label(
            self._inner, text="Proveedor personalizado",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        ttkb.Label(
            self._inner,
            text="Conecta cualquier endpoint compatible con OpenAI o Anthropic. "
                 "La API key se guarda en la configuración global.",
            font=("Segoe UI", 9), bootstyle="secondary",
        ).pack(anchor="w", pady=(0, 10))

        form = ttkb.Frame(self._inner)
        form.pack(fill=X, pady=(0, 12))
        form.columnconfigure(1, weight=1)

        self._cp_label_var = tk.StringVar(value=cp.label or cp.name)
        self._cp_api_var = tk.StringVar(value=cp.api_type or "openai")
        self._cp_url_var = tk.StringVar(value=cp.base_url)

        ttkb.Label(form, text="Nombre:").grid(row=0, column=0, sticky="w", pady=3)
        ttkb.Entry(form, textvariable=self._cp_label_var, width=38).grid(
            row=0, column=1, sticky="w", padx=(8, 0), pady=3)

        ttkb.Label(form, text="Tipo de API:").grid(row=1, column=0, sticky="w", pady=3)
        ttkb.Combobox(
            form, textvariable=self._cp_api_var, state="readonly", width=36,
            values=list(API_TYPES.keys()),
        ).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=3)

        ttkb.Label(form, text="Base URL:").grid(row=2, column=0, sticky="w", pady=3)
        ttkb.Entry(form, textvariable=self._cp_url_var, width=38).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=3)
        ttkb.Label(
            form,
            text="Ej: https://api.miservidor.com/v1  ·  Anthropic: https://api.anthropic.com",
            font=("Segoe UI", 8), bootstyle="secondary",
        ).grid(row=3, column=1, sticky="w", padx=(8, 0))

        # API keys reuse the standard section
        self._build_api_key_section(name, "API Keys")

        # Models manager
        ttkb.Label(self._inner, text="Modelos disponibles", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", pady=(10, 5))

        models_row = ttkb.Frame(self._inner)
        models_row.pack(fill=X, pady=(0, 6))

        self._models_listbox = tk.Listbox(
            models_row, height=6, font=("Segoe UI", 10),
            relief="flat", highlightthickness=1, highlightbackground="#444",
        )
        self._models_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self._render_custom_models()

        side = ttkb.Frame(models_row)
        side.pack(side=LEFT, padx=(8, 0), fill=Y)

        self._new_model_var = tk.StringVar()
        ttkb.Entry(side, textvariable=self._new_model_var, width=26).pack(fill=X, pady=(0, 4))
        ttkb.Button(
            side, text="+ Agregar", command=self._add_custom_model,
            bootstyle="success-outline", width=12,
        ).pack(fill=X, pady=(0, 4))
        ttkb.Button(
            side, text="− Quitar", command=self._remove_custom_model,
            bootstyle="danger-outline", width=12,
        ).pack(fill=X, pady=(0, 10))
        self._load_models_btn = ttkb.Button(
            side, text="Cargar del proveedor", command=self._load_custom_models,
            bootstyle="info-outline", width=18,
        )
        self._load_models_btn.pack(fill=X)

        self._custom_status = ttkb.Label(
            self._inner, text="", font=("Segoe UI", 9), bootstyle="secondary")
        self._custom_status.pack(anchor="w", pady=(6, 0))

    def _render_custom_models(self) -> None:
        if not hasattr(self, "_models_listbox"):
            return
        self._models_listbox.delete(0, END)
        for m in self._custom_models:
            self._models_listbox.insert(END, m)

    def _add_custom_model(self) -> None:
        value = self._new_model_var.get().strip()
        if not value:
            return
        if value not in self._custom_models:
            self._custom_models.append(value)
            self._render_custom_models()
        self._new_model_var.set("")

    def _remove_custom_model(self) -> None:
        if not hasattr(self, "_models_listbox"):
            return
        sel = self._models_listbox.curselection()
        if not sel:
            return
        value = self._models_listbox.get(sel[0])
        self._custom_models = [m for m in self._custom_models if m != value]
        self._render_custom_models()

    def _load_custom_models(self) -> None:
        if not self._current_custom_name:
            return
        api_type = self._cp_api_var.get().strip() or "openai"
        base_url = self._cp_url_var.get().strip()
        keys = self._read_current_keys(self._current_custom_name)
        key = next((k.key for k in keys if k.enabled and k.key), "")

        if not key:
            self._custom_status.configure(
                text="⚠ Agrega una API key para consultar los modelos.", bootstyle="warning")
            return

        self._load_models_btn.configure(state=DISABLED, text="Cargando...")
        self._custom_status.configure(text="Consultando modelos...", bootstyle="info")
        target = self._current_custom_name

        def worker() -> None:
            models = fetch_models(api_type, key, base_url)

            def apply() -> None:
                if target != self._current_custom_name:
                    return
                try:
                    self._load_models_btn.configure(state=NORMAL, text="Cargar del proveedor")
                    if models:
                        self._custom_models = models
                        self._render_custom_models()
                        self._custom_status.configure(
                            text=f"✓ {len(models)} modelos cargados.", bootstyle="success")
                    else:
                        self._custom_status.configure(
                            text="No se pudieron cargar modelos. Agrégalos manualmente.",
                            bootstyle="warning")
                except tk.TclError:
                    pass

            self.after_idle(apply)

        threading.Thread(target=worker, daemon=True).start()

    def _commit_custom_form(self) -> None:
        """Write the custom provider form back into the config object."""
        if not self._current_custom_name:
            return
        cp = self._config.get_custom_provider(self._current_custom_name)
        if cp is None:
            return
        try:
            cp.label = self._cp_label_var.get().strip() or cp.name
            cp.api_type = self._cp_api_var.get().strip() or "openai"
            cp.base_url = self._cp_url_var.get().strip()
            cp.models = list(self._custom_models)
            if hasattr(self, "_current_key_vars"):
                self._config.providers.setdefault(cp.name, ProviderKeys()).keys = (
                    self._read_current_keys(cp.name)
                )
        except (tk.TclError, AttributeError):
            pass

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

        self._ollama_model_vars = {}
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
        # Persist custom provider edits first
        self._commit_custom_form()

        # Save keys for the currently-selected built-in provider
        if not self._current_custom_name and self._current_provider_name:
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
