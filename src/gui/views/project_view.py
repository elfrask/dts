from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.config.settings import save_project
from src.gui.components.log_view import LogView


class ProjectView(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Window,
        state,
        on_back,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.on_back = on_back

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_top_bar()
        self._build_log_view()

    def _build_top_bar(self) -> None:
        project = self.state.project
        name = project.directory.name if project else "Sin proyecto"

        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        bar.columnconfigure(1, weight=1)

        ttk.Button(
            bar,
            text="← Volver",
            command=self._go_back,
            bootstyle="secondary-outline",
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Label(
            bar,
            text=f"Proyecto: {name}",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=1, sticky="w")

        ttk.Button(
            bar,
            text="Config global",
            command=self._open_settings,
            bootstyle="info-outline",
        ).grid(row=0, column=2)

    def _build_log_view(self) -> None:
        self.log_view = LogView(self)
        self.log_view.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    def _go_back(self) -> None:
        self.on_back()

    def _open_settings(self) -> None:
        from src.gui.views.settings import SettingsDialog
        SettingsDialog(self.winfo_toplevel(), self.state)
