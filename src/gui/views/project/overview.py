import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.config.settings import save_project, load_app_settings
from src.io.file_loader import load_strings, load_json
from src.io.file_writer import write_translation_dict
from src.io.formats import Project
from src.processors.matcher import generate_input
from src.processors.umt_extractor import is_umt_configured, extract_strings


class OverviewTab(ttk.Frame):
    def __init__(self, parent: ttk.Window, state) -> None:
        super().__init__(parent, padding=15)
        self.state = state
        self.columnconfigure(0, weight=1)

        self._build()

    def _build(self) -> None:
        project = self.state.project
        if not project:
            ttk.Label(self, text="No hay proyecto abierto").pack()
            return

        # ── Project info ──
        info = ttk.Labelframe(self, text="Información del proyecto", padding=10)
        info.pack(fill=X, pady=(0, 15))
        info.columnconfigure(1, weight=1)

        rows = [
            ("Directorio:", str(project.directory)),
            ("Proveedor:", project.config.provider.value),
            ("Modelo:", project.config.model),
            ("Chunk size:", str(project.config.chunk_size)),
        ]

        dw_path = project.data_win_file_path
        strings_path = project.strings_file_path
        input_path = project.input_file_path
        output_path = project.output_file_path

        dw_ok = dw_path.exists() and dw_path.suffix.lower() in (".win",)
        strings_ok = strings_path.exists()
        input_ok = input_path.exists()
        output_ok = output_path.exists()

        if dw_ok:
            rows.append(("data.win:", str(dw_path)))
        if strings_ok:
            s = load_strings(strings_path)
            rows.append(("Strings totales:", str(int(len(s.Strings) / 2)) + " diálogos"))
        if input_ok:
            d = load_json(input_path)
            rows.append(("Diálogos a traducir:", str(len(d))))

        for i, (label, value) in enumerate(rows):
            ttk.Label(info, text=label, font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", pady=2)
            ttk.Label(info, text=value, font=("Segoe UI", 10)).grid(
                row=i, column=1, sticky="w", padx=(10, 0), pady=2)

        # ── Estado del pipeline ──
        status_frame = ttk.Labelframe(self, text="Estado del pipeline", padding=10)
        status_frame.pack(fill=X, pady=(0, 15))

        status_parts = []
        if dw_ok:
            status_parts.append("✓ data.win seleccionado")
        else:
            status_parts.append("✗ data.win (seleccionar)")
        if strings_ok:
            status_parts.append("✓ strings.json extraído")
        else:
            status_parts.append("✗ strings.json (extraer)")
        if input_ok:
            status_parts.append("✓ lang_input.json generado")
        else:
            status_parts.append("✗ lang_input.json (generar)")
        if output_ok:
            status_parts.append("✓ lang_es_out.json traducido")
        else:
            status_parts.append("✗ lang_es_out.json (traducir)")

        self._status_label = ttk.Label(
            status_frame, text=" | ".join(status_parts),
            font=("Segoe UI", 10),
        )
        self._status_label.pack(anchor="w")

        # ── Actions ──
        actions = ttk.Labelframe(self, text="Acciones", padding=10)
        actions.pack(fill=X)

        ttk.Button(
            actions, text="Seleccionar data.win",
            command=self._select_data_win,
            bootstyle="primary",
            width=24,
        ).pack(anchor="w", pady=3)

        ttk.Button(
            actions, text="Cargar strings.json manualmente",
            command=self._load_strings_manual,
            bootstyle="secondary-outline",
        ).pack(anchor="w", pady=3)

        ttk.Button(
            actions, text="Ver diálogos",
            command=self._show_dialogs,
            bootstyle="info-outline",
        ).pack(anchor="w", pady=3)

    # ── data.win flow ───────────────────────────────────────────

    def _select_data_win(self) -> None:
        app_cfg = load_app_settings()

        if not is_umt_configured(app_cfg.umt.directory):
            self._ask_umt_or_manual()
            return

        path = filedialog.askopenfilename(
            title="Seleccionar data.win",
            filetypes=[("data.win", "*.win"), ("Todos", "*.*")],
        )
        if not path:
            return

        self._process_data_win(path)

    def _ask_umt_or_manual(self) -> None:
        resp = messagebox.askquestion(
            "UMT no configurado",
            "No hay una instalación de UMT CLI configurada.\n\n"
            "¿Quieres cargar un archivo strings.json ya extraído?\n\n"
            "• Presiona 'Sí' para seleccionar un strings.json existente.\n"
            "• Presiona 'No' para ir a Configuración global > Motor (UMT)\n"
            "  y descargar/configurar UMT CLI.",
            icon="warning",
        )
        if resp == "yes":
            self._load_strings_manual()
        else:
            self._open_umt_settings()

    def _open_umt_settings(self) -> None:
        from src.gui.views.settings import SettingsDialog
        SettingsDialog(self.winfo_toplevel(), self.state, initial_tab=1)

    def _process_data_win(self, data_win_path: str) -> None:
        project = self.state.project
        if not project:
            return

        project.config.route_data_win = data_win_path
        save_project(project)

        app_cfg = load_app_settings()
        strings_out = str(project.strings_file_path)

        self._status_label.configure(
            text="⏳ Extrayendo strings con UMT CLI...",
            bootstyle="info",
        )

        def worker():
            success, msg = extract_strings(
                directory=app_cfg.umt.directory,
                data_win_path=data_win_path,
                output_path=strings_out,
            )
            if not success:
                self._show_extract_error(msg)
                return

            self._generate_input_after_extract()

        threading.Thread(target=worker, daemon=True).start()

    def _show_extract_error(self, msg: str) -> None:
        messagebox.showerror("Error de extracción", msg)
        self._rebuild()

    def _generate_input_after_extract(self) -> None:
        project = self.state.project
        if not project:
            return
        try:
            strings = load_strings(project.strings_file_path)
            result = generate_input(strings)
            write_translation_dict(project.input_file_path, result)
            self._finish_extract(len(result.data))
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar input:\n{e}")
            self._rebuild()

    def _finish_extract(self, dialog_count: int) -> None:
        self._status_label.configure(
            text=f"✅ Extracción completada. {dialog_count} diálogos listos para traducir.",
            bootstyle="success",
        )
        messagebox.showinfo(
            "Extracción completada",
            f"data.win procesado exitosamente.\n\n"
            f"{dialog_count} diálogos extraídos y listos para traducir.\n\n"
            f"Ve a la pestaña 'Traducir' para comenzar.",
        )
        self._rebuild()

    # ── Manual strings.json load ────────────────────────────────

    def _load_strings_manual(self) -> None:
        project = self.state.project
        if not project:
            return

        path = filedialog.askopenfilename(
            title="Seleccionar strings.json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        project.config.route_strings_file = path
        save_project(project)

        try:
            strings = load_strings(Path(path))
            result = generate_input(strings)
            write_translation_dict(project.input_file_path, result)
            messagebox.showinfo(
                "Strings cargados",
                f"Se cargaron {len(result.data)} diálogos desde:\n{path}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar strings.json:\n{e}")
        self._rebuild()

    # ── Dialogs popup ───────────────────────────────────────────

    def _show_dialogs(self) -> None:
        from src.gui.views.project.dialogs_tab import view_dialogs_popup
        view_dialogs_popup(self.winfo_toplevel(), self.state)

    # ── Rebuild ─────────────────────────────────────────────────

    def _rebuild(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._build()
