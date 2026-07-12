import tkinter as tk
from pathlib import Path
from tkinter import messagebox, filedialog

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from src.io.formats import AppConfig, UmtConfig
from src.processors.umt_extractor import (
    is_umt_configured,
    umt_status,
    verify_umt,
    _find_cli,
    _find_export_script,
    _find_import_script,
    EXPORT_SCRIPT_REL,
    IMPORT_SCRIPT_REL,
)


class UmtTab(ttkb.Frame):
    def __init__(self, parent: ttkb.Window, config: AppConfig) -> None:
        super().__init__(parent, padding=10)
        self._config = config
        self.columnconfigure(0, weight=1)

        ttkb.Label(self, text="UndertaleModTool CLI", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(0, 5))
        ttkb.Label(self, text="Herramienta para extraer y reinsertar strings en archivos data.win de GameMaker.",
                   font=("Segoe UI", 10), bootstyle="secondary").pack(anchor="w", pady=(0, 15))

        # ── Status ──
        status_frame = ttkb.Labelframe(self, text="Estado", padding=10)
        status_frame.pack(fill=X, pady=(0, 15))

        self._status_label = ttkb.Label(status_frame, text="", font=("Segoe UI", 10))
        self._status_label.pack(anchor="w")
        self._cli_status = ttkb.Label(status_frame, text="", font=("Segoe UI", 10))
        self._cli_status.pack(anchor="w")
        self._script_status = ttkb.Label(status_frame, text="", font=("Segoe UI", 10))
        self._script_status.pack(anchor="w")

        # ── Manual ──
        path_frame = ttkb.Labelframe(self, text="Método manual", padding=10)
        path_frame.pack(fill=X, pady=(0, 15))

        ttkb.Label(path_frame, text="Selecciona la carpeta donde está instalado UMT:",
                   font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))

        entry_row = ttkb.Frame(path_frame)
        entry_row.pack(fill=X)

        self._dir_var = tk.StringVar(value=config.umt.directory)
        self._dir_var.trace_add("write", lambda *_: self._update_status())
        self._update_status()

        ttkb.Entry(entry_row, textvariable=self._dir_var, width=55).pack(
            side=LEFT, padx=(0, 6))
        ttkb.Button(entry_row, text="Examinar...", command=self._browse,
                    bootstyle="secondary", width=12).pack(side=LEFT, padx=(0, 6))
        ttkb.Button(entry_row, text="Verificar", command=self._verify,
                    bootstyle="info-outline", width=10).pack(side=LEFT)

        # ── Download ──
        dl_frame = ttkb.Labelframe(self, text="Descarga automática", padding=10)
        dl_frame.pack(fill=X)

        ttkb.Label(dl_frame, text="Descargar la última versión de UndertaleModTool CLI desde GitHub.",
                   font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 5))
        ttkb.Label(dl_frame, text="Al descargar, aceptas los términos de la licencia GPLv3.",
                   font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w", pady=(0, 10))

        self._dl_btn = ttkb.Button(dl_frame, text="Descargar UMT CLI",
                                   command=self._download, bootstyle="warning", width=20)
        self._dl_btn.pack(anchor="w")

        self._dl_status = ttkb.Label(dl_frame, text="", font=("Segoe UI", 9), bootstyle="secondary")
        self._dl_status.pack(anchor="w", pady=(5, 0))

        ttkb.Label(self, text="Repositorio: github.com/UnderminersTeam/UndertaleModTool",
                   font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w", pady=(15, 0))

    # ── Status ─────────────────────────────────────────────────

    def _update_status(self) -> None:
        directory = self._dir_var.get().strip()
        if not directory:
            self._status_label.configure(text="⚠ No hay carpeta configurada.", bootstyle="warning")
            self._cli_status.configure(text="")
            self._script_status.configure(text="")
            return

        d = Path(directory)
        if not d.exists():
            self._status_label.configure(text=f"✗ La carpeta no existe: {directory}", bootstyle="danger")
            self._cli_status.configure(text="")
            self._script_status.configure(text="")
            return
        if not d.is_dir():
            self._status_label.configure(text="✗ La ruta no es una carpeta", bootstyle="danger")
            self._cli_status.configure(text="")
            self._script_status.configure(text="")
            return

        cli = _find_cli(directory)
        export = _find_export_script(directory)
        import_ = _find_import_script(directory)

        self._status_label.configure(
            text=f"✓ Carpeta encontrada: {directory}",
            bootstyle="success" if (cli and export) else "warning",
        )
        self._cli_status.configure(
            text=f"  CLI: {'✓' if cli else '✗'} UndertaleModCli"
        )
        self._script_status.configure(
            text=(
                f"  Exportar: {'✓' if export else '✗'} ExportAllStringsJSON.csx"
                f"  |  Importar: {'✓' if import_ else '✗'} ImportAllStringsJSON.csx"
            )
        )

    # ── Browse ─────────────────────────────────────────────────

    def _browse(self) -> None:
        path = filedialog.askdirectory(
            title="Seleccionar carpeta de UMT",
        )
        if path:
            self._dir_var.set(path)

    # ── Verify ─────────────────────────────────────────────────

    def _verify(self) -> None:
        directory = self._dir_var.get().strip()
        if not directory:
            messagebox.showerror("Error", "No hay una carpeta seleccionada.")
            return
        d = Path(directory)
        if not d.exists() or not d.is_dir():
            messagebox.showerror("Error", f"La carpeta no existe:\n{directory}")
            return

        ok, info = verify_umt(directory)
        if ok:
            _, export_ok, detail = umt_status(directory)
            import_ = _find_import_script(directory)
            msg = f"✓ UMT CLI verificado: {info}\n\n"
            msg += f"  Export script: {'✓' if export_ok else '✗'}\n"
            msg += f"  Import script: {'✓' if import_ else '✗'}\n\n"
            msg += f"  {detail}"
            messagebox.showinfo("Verificación exitosa", msg)
        else:
            messagebox.showerror("Error de verificación", info)

    # ── Download ───────────────────────────────────────────────

    def _download(self) -> None:
        import platform, urllib.request, zipfile, io, threading

        self._dl_btn.configure(state=DISABLED, text="Descargando...")
        self._dl_status.configure(text="Iniciando descarga...", bootstyle="info")

        system = platform.system().lower()

        asset_map = {
            "windows": "UTMT_CLI_v0.9.1.1-Windows.zip",
            "linux": "UTMT_CLI_v0.9.1.1-Linux.zip",
            "darwin": "UTMT_CLI_v0.9.1.1-MacOS.zip",
        }
        asset_name = asset_map.get(system)
        if not asset_name:
            self._dl_status.configure(text=f"Plataforma no soportada: {system}", bootstyle="danger")
            self._dl_btn.configure(state=NORMAL, text="Descargar UMT CLI")
            return

        url = (f"https://github.com/UnderminersTeam/UndertaleModTool/releases/"
               f"download/0.9.1.1/{asset_name}")

        def task():
            try:
                self._dl_status.configure(text=f"Descargando {asset_name}...", bootstyle="info")
                resp = urllib.request.urlopen(url, timeout=60)
                data = resp.read()

                extract_dir = Path(self._config.umt.directory or Path.cwd())
                if not extract_dir.exists() or not extract_dir.is_absolute():
                    extract_dir = Path.home() / ".dts" / "umt"
                extract_dir.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    z.extractall(path=str(extract_dir))

                self._dir_var.set(str(extract_dir))
                self._dl_status.configure(text=f"✓ Descargado y extraído en: {extract_dir}", bootstyle="success")
            except Exception as e:
                self._dl_status.configure(text=f"Error en descarga: {e}", bootstyle="danger")
            finally:
                self._dl_btn.configure(state=NORMAL, text="Descargar UMT CLI")

        threading.Thread(target=task, daemon=True).start()

    # ── Sync ───────────────────────────────────────────────────

    def update_config(self, config: AppConfig) -> None:
        dir_val = self._dir_var.get().strip() if hasattr(self, "_dir_var") else ""
        config.umt = UmtConfig(
            directory=dir_val,
            auto_download=False,
        )
