import json
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.config.settings import load_project, save_project
from src.config.defaults import DEFAULT_PROMPT, DEFAULT_CHUNK_SIZE, DEFAULT_MODEL
from src.io.formats import ProjectConfig, Project


def _recent_projects_path() -> Path:
    from src.config.defaults import DEFAULT_APP_CONFIG_DIR
    return DEFAULT_APP_CONFIG_DIR / "recent_projects.json"


def _load_recent() -> list[str]:
    path = _recent_projects_path()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_recent(projects: list[str]) -> None:
    path = _recent_projects_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(projects[:10], f, indent=2)


class WelcomeView(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Window,
        state,
        on_project_selected,
        on_show_settings,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.on_project_selected = on_project_selected
        self.on_show_settings = on_show_settings

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        _header = ttk.Frame(self)
        _header.grid(row=0, column=0, pady=(40, 10))

        ttk.Label(
            _header,
            text="DTS v2 (2.1 dev-20260722)",
            font=("Segoe UI", 28, "bold"),
        ).pack()
        ttk.Label(
            _header,
            text="Dialogue Translation System",
            font=("Segoe UI", 14),
            # bootstyle="secondary",
        ).pack()
        ttk.Label(
            _header,
            text="by Frask Coffee",
            font=("Segoe UI", 14, "bold"),
            # cursor="0px 0px"
            # bootstyle="secondary",
        ).pack()
        

        _btn_row = ttk.Frame(self)
        _btn_row.grid(row=1, column=0, pady=20)

        ttk.Button(
            _btn_row,
            text="Abrir proyecto",
            command=self._open_project,
            bootstyle="primary",
            width=18,
        ).pack(side=LEFT, padx=6)

        ttk.Button(
            _btn_row,
            text="Crear proyecto",
            command=self._create_project,
            bootstyle="success",
            width=18,
        ).pack(side=LEFT, padx=6)

        ttk.Button(
            _btn_row,
            text="Configuración global",
            command=on_show_settings,
            bootstyle="info-outline",
            width=18,
        ).pack(side=LEFT, padx=6)

        _recent_frame = ttk.Labelframe(self, text="Proyectos recientes", padding=10)
        _recent_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=(0, 20))
        _recent_frame.columnconfigure(0, weight=1)
        _recent_frame.rowconfigure(0, weight=1)

        self._recent_listbox = tk.Listbox(
            _recent_frame,
            font=("Segoe UI", 11),
            selectbackground="#375a7f",
            selectforeground="white",
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
        )
        self._recent_listbox.pack(fill=BOTH, expand=True)
        self._recent_listbox.bind("<Double-Button-1>", self._on_recent_click)

        self._refresh_recent()

    def _refresh_recent(self) -> None:
        self._recent_listbox.delete(0, END)
        for p in _load_recent():
            path = Path(p)
            if path.exists():
                self._recent_listbox.insert(END, str(path))

    def _on_recent_click(self, event=None) -> None:
        sel = self._recent_listbox.curselection()
        if not sel:
            return
        raw = self._recent_listbox.get(sel[0])
        path = Path(raw)
        if path.exists():
            self._open_project_at(path)
        else:
            messagebox.showerror("Error", f"La ruta no existe:\n{raw}")

    def _open_project(self) -> None:
        raw = filedialog.askdirectory(title="Seleccionar directorio del proyecto")
        if not raw:
            return
        path = Path(raw)
        if not path.exists():
            messagebox.showerror("Error", "El directorio seleccionado no existe")
            return
        if not (path / "settings.json").exists():
            ret = messagebox.askyesno(
                "Abrir proyecto",
                "Este directorio no contiene un proyecto DTS. ¿Crear uno nuevo aquí?",
            )
            if ret:
                self._create_project_at(path)
            return
        self._open_project_at(path)

    def _create_project(self) -> None:
        raw = filedialog.askdirectory(title="Seleccionar directorio padre")
        if not raw:
            return
        parent = Path(raw)
        if not parent.exists():
            return
        self._ask_project_name(parent)

    def _ask_project_name(self, parent: Path) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Crear proyecto")
        dialog.geometry("400x200")
        dialog.transient(self) #type: ignore
        dialog.grab_set()

        ttk.Label(dialog, text="Nombre del proyecto:", font=("Segoe UI", 11)).pack(
            pady=(20, 5)
        )
        name_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=name_var, font=("Segoe UI", 11))
        entry.pack(padx=20, fill=X)
        entry.focus()

        def _confirm() -> None:
            name = name_var.get().strip()
            if not name:
                return
            dialog.destroy()
            self._create_project_at(parent / name)

        ttk.Button(dialog, text="Crear", command=_confirm, bootstyle="success").pack(
            pady=10
        )
        dialog.bind("<Return>", lambda e: _confirm())

    def _open_project_at(self, path: Path) -> None:
        project = load_project(path)
        self.state.project = project #type: ignore
        self.state.clear_log() #type: ignore
        recent = _load_recent()
        pstr = str(path)
        if pstr in recent:
            recent.remove(pstr)
        recent.insert(0, pstr)
        _save_recent(recent)
        self.on_project_selected(project)

    def _create_project_at(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        config = ProjectConfig(
            prompt=DEFAULT_PROMPT,
            chunk_size=DEFAULT_CHUNK_SIZE,
            model=DEFAULT_MODEL,
        )
        project = Project(directory=path, config=config)
        save_project(project)
        self.state.project = project #type: ignore
        self.state.clear_log() #type: ignore

        strings_path = path / "strings.json"
        if strings_path.exists():
            project.config.route_strings_file = str(strings_path)
            save_project(project)

        recent = _load_recent()
        pstr = str(path)
        if pstr in recent:
            recent.remove(pstr)
        recent.insert(0, pstr)
        _save_recent(recent)

        self.on_project_selected(project)
