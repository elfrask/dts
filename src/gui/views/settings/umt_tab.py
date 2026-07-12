import threading
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


class _DownloadProgressDialog:
    """Modal progress dialog for UMT download."""

    def __init__(self, parent: tk.Widget, asset_name: str) -> None:
        self._parent = parent
        self._cancelled = False

        self._win = tk.Toplevel(parent)
        self._win.title("Descargando UMT CLI")
        self._win.transient(parent) #type: ignore
        self._win.grab_set()
        self._win.resizable(False, False)

        # Center on parent
        self._win.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = 480, 200
        self._win.geometry(f"{w}x{h}+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

        frame = ttkb.Frame(self._win, padding=20)
        frame.pack(fill=BOTH, expand=True)

        ttkb.Label(frame, text="Descargando UMT CLI",
                   font=("Segoe UI", 13, "bold")).pack(anchor="w")

        self._file_label = ttkb.Label(frame, text=asset_name,
                                      font=("Segoe UI", 10))
        self._file_label.pack(anchor="w", pady=(8, 4))

        self._progress = ttkb.Progressbar(frame, length=440, mode="determinate", value=0)
        self._progress.pack(fill=X, pady=(0, 4))

        self._size_label = ttkb.Label(frame, text="Iniciando...",
                                      font=("Segoe UI", 9), bootstyle="secondary")
        self._size_label.pack(anchor="w")

        self._status_label = ttkb.Label(frame, text="",
                                        font=("Segoe UI", 9), bootstyle="secondary")
        self._status_label.pack(anchor="w", pady=(4, 0))

        self._close_btn = ttkb.Button(frame, text="Cerrar", state=DISABLED,
                                      command=self._win.destroy, width=12)
        self._close_btn.pack(anchor="e", pady=(12, 0))

        self._win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        if self._close_btn.cget("state") == "disabled":
            return
        self._win.destroy()

    def _schedule(self, fn, *args) -> None:
        self._win.after_idle(fn, *args)

    def update_progress(self, downloaded: int, total: int) -> None:
        def _do():
            if total:
                pct = int(downloaded / total * 100)
                self._progress.configure(value=pct)
                self._size_label.configure(
                    text=f"{downloaded // 1024} KB / {total // 1024} KB")
            else:
                self._size_label.configure(text=f"{downloaded // 1024} KB descargados")
        self._win.after_idle(_do)

    def set_status(self, text: str, error: bool = False) -> None:
        def _do():
            self._status_label.configure(
                text=text,
                bootstyle="danger" if error else "info",
            )
        self._win.after_idle(_do)

    def set_complete(self, success: bool, msg: str) -> None:
        def _do():
            if success:
                self._size_label.configure(text="✓ " + msg, bootstyle="success")
            else:
                self._size_label.configure(text="✗ " + msg, bootstyle="danger")
            self._close_btn.configure(state=NORMAL, text="Cerrar")
        self._win.after_idle(_do)

    def close(self) -> None:
        self._win.after_idle(self._win.destroy)

    def is_cancelled(self) -> bool:
        return self._cancelled


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
        import platform
        import urllib.request
        import zipfile

        system = platform.system().lower()

        asset_map = {
            "windows": "UTMT_CLI_v0.9.1.1-Windows.zip",
            "linux": "UTMT_CLI_v0.9.1.1-Linux.zip",
            "darwin": "UTMT_CLI_v0.9.1.1-MacOS.zip",
        }
        asset_name = asset_map.get(system)
        if not asset_name:
            self._dl_status.configure(text=f"Plataforma no soportada: {system}", bootstyle="danger")
            return

        url = (f"https://github.com/UnderminersTeam/UndertaleModTool/releases/"
               f"download/0.9.1.1/{asset_name}")

        # Determine target directory
        extract_dir = Path(self._config.umt.directory or "")
        if not extract_dir or not extract_dir.is_absolute():
            extract_dir = Path.home() / ".dts" / "umt"

        # Disable the download button
        self._dl_btn.configure(state=DISABLED, text="Descargando...")

        # Create the progress dialog
        dialog = _DownloadProgressDialog(self, asset_name)

        def reporthook(block_count: int, block_size: int, total_size: int) -> None:
            downloaded = block_count * block_size
            if total_size > 0:
                downloaded = min(downloaded, total_size)
            dialog.update_progress(downloaded, total_size)

        def task():
            try:
                extract_dir.mkdir(parents=True, exist_ok=True)
                tmp = extract_dir / asset_name

                dialog.set_status(f"Descargando {asset_name}...")
                urllib.request.urlretrieve(url, str(tmp), reporthook)

                dialog.set_status("Extrayendo archivos...")
                with zipfile.ZipFile(str(tmp)) as z:
                    z.extractall(path=str(extract_dir))
                tmp.unlink(missing_ok=True)

                self._dir_var.set(str(extract_dir))
                self._dl_status.configure(
                    text=f"✓ Descargado y extraído en: {extract_dir}",
                    bootstyle="success",
                )
                dialog.set_complete(True, f"Extraído en: {extract_dir}")

            except Exception as e:
                self._dl_status.configure(text=f"Error: {e}", bootstyle="danger")
                dialog.set_complete(False, str(e))
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
