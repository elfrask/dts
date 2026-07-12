from pathlib import Path
from tkinter import filedialog, messagebox
from threading import Thread

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.config.settings import load_app_settings, save_project
from src.io.file_loader import load_strings, load_json
from src.io.file_writer import write_strings, write_json
from src.processors.matcher import apply_strings, generate_input
from src.processors.normalizer import normalice_text
from src.io.formats import TranslationDict
from src.processors.umt_extractor import (
    is_umt_configured,
    import_strings,
    extract_strings,
)


class ExportTab(ttk.Frame):
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

        self._normalize_var = ttk.BooleanVar(value=True)
        self._status_label = ttk.Label(self, text="", font=("Segoe UI", 10))
        self._status_label.pack(anchor="w", pady=(0, 10))

        # ── Mode 1: Export as strings_es.json ──────────────────
        m1 = ttk.Labelframe(self, text="Exportar como strings_es.json", padding=10)
        m1.pack(fill=X, pady=(0, 10))

        ttk.Label(m1, text="Genera el archivo strings_es.json fusionando las traducciones con los strings originales.",
                  font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Checkbutton(
            m1, text="Normalizar caracteres especiales (seguro para GML)",
            variable=self._normalize_var, bootstyle="round-toggle",
        ).pack(anchor="w", pady=(6, 0))
        ttk.Button(
            m1, text="Exportar strings_es.json...",
            command=self._export_strings_es,
            bootstyle="primary", width=28,
        ).pack(anchor="w", pady=(8, 0))

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=5)

        # ── Mode 2: Export as data.win ─────────────────────────
        m2 = ttk.Labelframe(self, text="Exportar como data.win (basado en el original)", padding=10)
        m2.pack(fill=X, pady=(0, 10))

        self._dw_status = ttk.Label(
            m2, text="", font=("Segoe UI", 10))
        self._dw_status.pack(anchor="w")
        self._update_dw_status(project)
        ttk.Button(
            m2, text="Exportar data.win...",
            command=self._export_data_win,
            bootstyle="warning", width=28,
        ).pack(anchor="w", pady=(8, 0))

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=5)

        # ── Mode 3: Export as patch ────────────────────────────
        m3 = ttk.Labelframe(self, text="Aplicar como parche a otro data.win", padding=10)
        m3.pack(fill=X)

        ttk.Label(m3, text="Selecciona un data.win diferente al original y las traducciones se fusionarán en él.",
                  font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Button(
            m3, text="Parchear otro data.win...",
            command=self._export_patch,
            bootstyle="danger", width=28,
        ).pack(anchor="w", pady=(8, 0))

    def _update_dw_status(self, project) -> None:
        app_cfg = load_app_settings()
        if not is_umt_configured(app_cfg.umt.directory):
            self._dw_status.configure(
                text="⚠ UMT no configurado. Ve a Config global > Motor (UMT)",
                bootstyle="warning")
            return
        dw = project.data_win_file_path
        if not dw.exists():
            self._dw_status.configure(
                text="⚠ No hay data.win seleccionado. Hazlo desde la pestaña Resumen.",
                bootstyle="warning")
            return
        self._dw_status.configure(
            text=f"✓ data.win: {dw}",
            bootstyle="success")

    # ── Helpers ────────────────────────────────────────────────

    def _resolve_translations(self) -> dict | None:
        """Return translations dict, or None if unavailable."""
        project = self.state.project
        if not project:
            return None
        source = project.output_file_path
        if not source.exists():
            source = project.normalize_file_path
        if not source.exists():
            self._status_label.configure(text="❌ No hay traducciones. Traduce primero.")
            return None
        return load_json(source)

    def _generate_strings_es(self, target: Path) -> bool:
        """Generate strings_es.json at target. Returns True on success."""
        project = self.state.project
        if not project:
            return False
        if not project.strings_file_path.exists():
            self._status_label.configure(text="❌ No se encuentra strings.json original")
            return False
        translations = self._resolve_translations()
        if translations is None:
            return False
        strings = load_strings(project.strings_file_path)
        if self._normalize_var.get():
            translations = {k: normalice_text(v) for k, v in translations.items()}
        result = apply_strings(strings, TranslationDict(data=translations))
        write_strings(target, result)
        return True

    # ── Mode 1: strings_es.json ────────────────────────────────

    def _export_strings_es(self) -> None:
        project = self.state.project
        if not project:
            return
        path = filedialog.asksaveasfilename(
            title="Guardar strings_es.json",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="strings_es.json",
        )
        if not path:
            return
        if self._generate_strings_es(Path(path)):
            self._status_label.configure(
                text=f"✅ strings_es.json guardado en:\n{path}")

    # ── Mode 2: data.win from original ─────────────────────────

    def _export_data_win(self) -> None:
        project = self.state.project
        if not project:
            return
        app_cfg = load_app_settings()
        if not is_umt_configured(app_cfg.umt.directory):
            messagebox.showerror("Error", "UMT no está configurado.\nVe a Config global > Motor (UMT)")
            return
        dw = project.data_win_file_path
        if not dw.exists():
            messagebox.showerror("Error", "No hay data.win seleccionado.\nHazlo desde la pestaña Resumen.")
            return

        output = filedialog.asksaveasfilename(
            title="Guardar data.win traducido",
            defaultextension=".win",
            filetypes=[("data.win", "*.win")],
            initialfile="data_es.win",
        )
        if not output:
            return

        self._status_label.configure(text="⏳ Generando strings_es.json...")
        strings_es = project.directory / "__dts_export_temp_strings.json"
        if not self._generate_strings_es(strings_es):
            return

        self._status_label.configure(text="⏳ Importando traducciones con UMT...")

        def worker():
            success, msg = import_strings(
                directory=app_cfg.umt.directory,
                data_win_path=str(dw),
                strings_json_path=str(strings_es),
                output_win_path=output,
            )
            self._cleanup_temp(str(strings_es))
            if success:
                self._status_label.configure(text=f"✅ data.win exportado:\n{output}")
                messagebox.showinfo("Exportación completada", f"data.win traducido guardado en:\n{output}")
            else:
                self._status_label.configure(text=f"❌ {msg}")

        Thread(target=worker, daemon=True).start()

    # ── Mode 3: patch another data.win ─────────────────────────

    def _export_patch(self) -> None:
        project = self.state.project
        if not project:
            return
        app_cfg = load_app_settings()
        if not is_umt_configured(app_cfg.umt.directory):
            messagebox.showerror("Error", "UMT no está configurado.\nVe a Config global > Motor (UMT)")
            return

        source = filedialog.askopenfilename(
            title="Seleccionar el data.win a parchear",
            filetypes=[("data.win", "*.win"), ("Todos", "*.*")],
        )
        if not source:
            return

        output = filedialog.asksaveasfilename(
            title="Guardar data.win parcheado",
            defaultextension=".win",
            filetypes=[("data.win", "*.win")],
            initialfile="data_patched.win",
        )
        if not output:
            return

        self._status_label.configure(text="⏳ Extrayendo strings del data.win destino...")

        temp_dir = project.directory / "__dts_export_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_strings = temp_dir / "strings.json"
        temp_strings_es = temp_dir / "strings_es.json"

        def worker():
            # 1. Extract strings from source data.win
            success, msg = extract_strings(
                directory=app_cfg.umt.directory,
                data_win_path=source,
                output_path=str(temp_strings),
            )
            if not success:
                self._status_label.configure(text=f"❌ Error al extraer: {msg}")
                self._cleanup_temp_dir(temp_dir)
                return

            # 2. Generate strings_es.json merging original + translations
            try:
                strings = load_strings(temp_strings)
                translations = self._resolve_translations()
                if translations is None:
                    self._cleanup_temp_dir(temp_dir)
                    return
                self._status_label.configure(text="⏳ Fusionando traducciones...")
                tdict = translations
                if self._normalize_var.get():
                    tdict = {k: normalice_text(v) for k, v in translations.items()}
                result = apply_strings(strings, TranslationDict(data=tdict))
                write_strings(temp_strings_es, result)
            except Exception as e:
                self._status_label.configure(text=f"❌ Error al fusionar: {e}")
                self._cleanup_temp_dir(temp_dir)
                return

            # 3. Import into source data.win
            self._status_label.configure(text="⏳ Importando traducciones con UMT...")
            success, msg = import_strings(
                directory=app_cfg.umt.directory,
                data_win_path=source,
                strings_json_path=str(temp_strings_es),
                output_win_path=output,
            )
            self._cleanup_temp_dir(temp_dir)
            if success:
                self._status_label.configure(text=f"✅ Parche aplicado:\n{output}")
                messagebox.showinfo(
                    "Parche completado",
                    f"Traducciones aplicadas al data.win.\nGuardado en:\n{output}",
                )
            else:
                self._status_label.configure(text=f"❌ {msg}")

        Thread(target=worker, daemon=True).start()

    # ── Cleanup ────────────────────────────────────────────────

    def _cleanup_temp(self, path: str) -> None:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass

    def _cleanup_temp_dir(self, directory: Path) -> None:
        try:
            import shutil
            shutil.rmtree(directory, ignore_errors=True)
        except OSError:
            pass
