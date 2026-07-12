import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.gui.views.project.overview import OverviewTab
from src.gui.views.project.dialogs_tab import view_dialogs_popup
from src.gui.views.project.translate_tab import TranslateTab
from src.gui.views.project.review_tab import ReviewTab
from src.gui.views.project.export_tab import ExportTab


class ProjectView(ttk.Frame):
    def __init__(self, parent: ttk.Window, state, on_back) -> None:
        super().__init__(parent)
        self.state = state
        self.on_back = on_back

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_top_bar()
        self._build_content()

    def _build_top_bar(self) -> None:
        project = self.state.project #type: ignore
        name = project.directory.name if project else "Sin proyecto"

        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        bar.columnconfigure(1, weight=1)

        ttk.Button(
            bar, text="← Volver", command=self.on_back,
            bootstyle="secondary-outline",
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Label(
            bar, text=f"Proyecto: {name}",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=1, sticky="w")

        ttk.Button(
            bar, text="Config global",
            command=self._open_settings,
            bootstyle="info-outline",
        ).grid(row=0, column=2)

    def _build_content(self) -> None:
        self._notebook = ttk.Notebook(self)
        self._notebook.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        self._overview = OverviewTab(self._notebook, self.state) #type: ignore
        self._notebook.add(self._overview, text="Resumen")

        self._translate = TranslateTab(self._notebook, self.state) #type: ignore
        self._notebook.add(self._translate, text="Traducir")

        self._review = ReviewTab(self._notebook, self.state) #type: ignore
        self._notebook.add(self._review, text="Revisión")

        self._export = ExportTab(self._notebook, self.state) #type: ignore
        self._notebook.add(self._export, text="Exportar")

    def _open_settings(self) -> None:
        from src.gui.views.settings import SettingsDialog
        SettingsDialog(self.winfo_toplevel(), self.state) #type: ignore
