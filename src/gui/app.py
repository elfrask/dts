import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.config.settings import load_app_settings
from src.gui.state import GUIState
from src.gui.views.welcome_view import WelcomeView


class DTSApp(ttk.Window):
    def __init__(self) -> None:
        super().__init__(themename="darkly")
        self.title("DTS v2 - Dialogue Translation System by Frask Coffee")
        self.geometry("1200x800")
        self.minsize(900, 600)

        app_config = load_app_settings()
        self.state = GUIState(app_config)

        self._current_view: Optional[ttk.Frame] = None
        self._main_container = ttk.Frame(self)
        self._main_container.pack(fill=BOTH, expand=True)

        self._show_welcome()

    def _show_welcome(self) -> None:
        self._clear_view()
        self._current_view = WelcomeView(
            self._main_container, #type: ignore
            self.state,
            on_project_selected=self._on_project_selected,
            on_show_settings=self._show_settings,
        )
        self._current_view.pack(fill=BOTH, expand=True)

    def _on_project_selected(self, project) -> None:
        from src.gui.views.project import ProjectView
        self._clear_view()
        self._current_view = ProjectView(
            self._main_container, #type: ignore
            self.state,
            on_back=self._show_welcome,
        )
        self._current_view.pack(fill=BOTH, expand=True)

    def _show_settings(self, initial_tab: int = 0) -> None:
        from src.gui.views.settings import SettingsDialog
        SettingsDialog(self, self.state, initial_tab=initial_tab)

    def _clear_view(self) -> None:
        if self._current_view:
            self._current_view.destroy()
            self._current_view = None


def gui_main() -> None:
    app = DTSApp()
    app.mainloop()
