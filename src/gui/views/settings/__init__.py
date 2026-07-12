import tkinter as tk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from src.config.settings import load_app_settings, save_app_settings
from src.gui.views.settings.provider_tab import ProviderTab
from src.gui.views.settings.umt_tab import UmtTab
from src.gui.views.settings.project_tab import ProjectTab


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent: ttkb.Window, state, initial_tab: int = 0) -> None:
        super().__init__(parent)
        self.state = state
        self.title("Configuración global")
        self.geometry("700x500")
        self.minsize(650, 400)
        self.transient(parent)
        self.grab_set()

        self._config = load_app_settings()

        main = ttkb.Frame(self, padding=10)
        main.pack(fill=BOTH, expand=True)

        self._notebook = ttkb.Notebook(main)
        self._notebook.pack(fill=BOTH, expand=True)

        self._provider_tab = ProviderTab(self._notebook, self._config)
        self._notebook.add(self._provider_tab, text="Proveedor de IA")

        self._umt_tab = UmtTab(self._notebook, self._config)
        self._notebook.add(self._umt_tab, text="Motor (UMT)")

        project_disable = False
        if not state.project:
            project_disable = True

        self._project_tab = ProjectTab(self._notebook, state)
        self._notebook.add(self._project_tab, text= ("Configuracion del Proyecto (no disponible)" if project_disable else "Configuracion del Proyecto"))

        if project_disable:
            self._notebook.tab(2, state="disabled")

        if 0 <= initial_tab < len(self._notebook.tabs()):
            self._notebook.select(initial_tab)

        btn_frame = ttkb.Frame(main)
        btn_frame.pack(fill=X, pady=(10, 0))

        ttkb.Button(
            btn_frame, text="Cancelar", command=self.destroy, bootstyle="secondary"
        ).pack(side=RIGHT, padx=(6, 0))

        ttkb.Button(
            btn_frame, text="Guardar", command=self._save, bootstyle="primary"
        ).pack(side=RIGHT)

    def _save(self) -> None:
        self._provider_tab.update_config(self._config)
        self._umt_tab.update_config(self._config)
        save_app_settings(self._config)
        self.state.app_config = self._config
        self.destroy()
