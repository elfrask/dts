import tkinter as tk
from pathlib import Path
from tkinter import messagebox, filedialog

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from src.io.formats import AppConfig, UmtConfig


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

        # ── Manual ──
        path_frame = ttkb.Labelframe(self, text="Método manual", padding=10)
        path_frame.pack(fill=X, pady=(0, 15))

        ttkb.Label(path_frame, text="Si ya tienes UndertaleModTool CLI descargado, selecciona el ejecutable:",
                   font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))

        entry_row = ttkb.Frame(path_frame)
        entry_row.pack(fill=X)

        self._path_var = tk.StringVar(value=config.umt.cli_path)
        self._path_var.trace_add("write", lambda *_: self._update_status())
        self._update_status()


        ttkb.Entry(entry_row, textvariable=self._path_var, width=55).pack(
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
        path = self._path_var.get().strip()
        if not path:
            self._status_label.configure(
                text="⚠ No hay ruta configurada. Usa la descarga automática o selecciona el ejecutable manualmente.",
                bootstyle="warning")
        elif not Path(path).exists():
            self._status_label.configure(text=f"✗ La ruta no existe: {path}", bootstyle="danger")
        else:
            self._status_label.configure(text=f"✓ Ruta configurada: {path}", bootstyle="success")

    # ── Browse ─────────────────────────────────────────────────

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar UMT CLI",
            filetypes=[("Ejecutable", "*.exe"), ("Todos", "*.*")],
        )
        if path:
            self._path_var.set(path)

    # ── Verify ─────────────────────────────────────────────────

    def _verify(self) -> None:
        path = self._path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "No hay una ruta seleccionada.")
            return
        p = Path(path)
        if not p.exists() or not p.is_file():
            messagebox.showerror("Error", f"El archivo no existe:\n{path}")
            return

        import subprocess
        try:
            result = subprocess.run([str(p), "--version"], capture_output=True, text=True, timeout=10)
            version = result.stdout.strip() or result.stderr.strip()
            msg = f"UMT CLI encontrado en:\n{path}\n\n"
            msg += f"Versión: {version}" if version else "No se pudo obtener la versión."
            messagebox.showinfo("Verificación exitosa", msg)
            self._status_label.configure(text=f"✓ UMT CLI verificado: {version or path}", bootstyle="success")
        except FileNotFoundError:
            messagebox.showerror("Error", f"No se puede ejecutar:\n{path}\n\n¿Es un ejecutable válido?")
        except subprocess.TimeoutExpired:
            messagebox.showerror("Error", "El comando tardó demasiado. ¿Es un ejecutable de UMT?")

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

                extract_dir = Path(self._config.umt.cli_path or Path.cwd())
                if not extract_dir.exists() or not extract_dir.is_absolute():
                    extract_dir = Path.home() / ".dts" / "umt"
                extract_dir.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    z.extractall(path=str(extract_dir))

                exe_name = "UndertaleModTool.exe" if system == "windows" else "UndertaleModTool"
                found = list(extract_dir.rglob(exe_name))
                if found:
                    self._path_var.set(str(found[0]))
                    self._dl_status.configure(text=f"✓ Descargado en: {found[0]}", bootstyle="success")
                else:
                    self._dl_status.configure(
                        text="✓ Descargado pero no se encontró el ejecutable.", bootstyle="warning")
            except Exception as e:
                self._dl_status.configure(text=f"Error en descarga: {e}", bootstyle="danger")
            finally:
                self._dl_btn.configure(state=NORMAL, text="Descargar UMT CLI")

        threading.Thread(target=task, daemon=True).start()

    # ── Sync ───────────────────────────────────────────────────

    def update_config(self, config: AppConfig) -> None:
        config.umt = UmtConfig(
            cli_path=self._path_var.get().strip() if hasattr(self, "_path_var") else "",
            auto_download=False,
        )
