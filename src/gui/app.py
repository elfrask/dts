import logging

import flet as ft

from src.config.settings import load_app_settings
from src.gui.state import GUIState
from src.gui.views.welcome_view import WelcomeView
from src.gui.views.project_view import ProjectView
from src.io.formats import Project

logger = logging.getLogger(__name__)


def gui_main() -> None:
    ft.app(target=main)


def main(page: ft.Page) -> None:
    page.title = "DTS v2 - Dialogue Translation System"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window.width = 1280
    page.window.height = 800

    app_config = load_app_settings()
    state = GUIState(app_config)

    def on_project_selected(project: Project) -> None:
        state.project = project
        state.clear_log()
        page.clean()
        page.add(ProjectView(page, state))

    page.clean()
    page.add(WelcomeView(page, state, on_project_selected=on_project_selected))
