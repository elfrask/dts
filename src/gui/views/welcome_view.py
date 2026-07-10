from pathlib import Path
from typing import Optional

import flet as ft

from src.gui.state import GUIState
from src.io.formats import AppConfig, ProjectConfig, OllamaConfig
from src.config.settings import (
    load_app_settings,
    save_app_settings,
    load_project,
    save_project,
)
from src.config.defaults import (
    DEFAULT_PROMPT,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_TIMEOUT,
)
from src.io.formats import Project


def recent_projects_path() -> Path:
    from src.config.defaults import DEFAULT_APP_CONFIG_DIR
    return DEFAULT_APP_CONFIG_DIR / "recent_projects.json"


def load_recent_projects() -> list[str]:
    import json
    path = recent_projects_path()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_recent_projects(projects: list[str]) -> None:
    import json
    path = recent_projects_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(projects[:10], f, indent=2)


class WelcomeView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        state: GUIState,
        on_project_selected: callable,
    ) -> None:
        super().__init__()
        self.page = page
        self.state = state
        self.on_project_selected = on_project_selected
        self.spacing = 20
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self._file_picker = ft.FilePicker(on_result=self._on_pick_dir)
        self._strings_picker = ft.FilePicker(on_result=self._on_pick_strings)
        page.overlay.extend([self._file_picker, self._strings_picker])

        self._pending_create = False
        self._project_list = ft.Column(spacing=8)

        self._build()

    def _build(self) -> None:
        title = ft.Text(
            "DTS v2 - Dialogue Translation System",
            size=28,
            weight=ft.FontWeight.BOLD,
        )
        subtitle = ft.Text(
            "Traducción de diálogos de juegos GameMaker",
            size=14,
            color=ft.Colors.GREY_400,
        )

        open_btn = ft.ElevatedButton(
            "Abrir proyecto",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self._file_picker.get_directory_path(),
        )
        create_btn = ft.ElevatedButton(
            "Crear nuevo proyecto",
            icon=ft.Icons.CREATE_NEW_FOLDER,
            on_click=lambda _: self._start_create_project(),
        )
        settings_btn = ft.ElevatedButton(
            "Configuración global",
            icon=ft.Icons.SETTINGS,
            on_click=lambda _: self._open_global_settings(),
        )

        self._refresh_recent()

        self.controls = [
            ft.Container(height=60),
            title,
            subtitle,
            ft.Container(height=20),
            ft.Row(
                [open_btn, create_btn, settings_btn],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            ft.Container(height=20),
            ft.Text("Proyectos recientes", weight=ft.FontWeight.BOLD, size=16),
            self._project_list,
        ]

    def _refresh_recent(self) -> None:
        self._project_list.controls.clear()
        for p in load_recent_projects():
            path = Path(p)
            if path.exists():
                self._project_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(path.name),
                        subtitle=ft.Text(str(path)),
                        on_click=lambda _, pp=p: self._open_project(Path(pp)),
                    )
                )
        if not self._project_list.controls:
            self._project_list.controls.append(
                ft.Text("No hay proyectos recientes", color=ft.Colors.GREY_500)
            )

    def _open_project(self, path: Path) -> None:
        project = load_project(path)
        self.state.project = project
        recent = load_recent_projects()
        pstr = str(path)
        if pstr in recent:
            recent.remove(pstr)
        recent.insert(0, pstr)
        save_recent_projects(recent)
        self.on_project_selected(project)

    def _on_pick_dir(self, e: ft.FilePickerResultEvent) -> None:
        if e.path:
            path = Path(e.path)
            if self._pending_create:
                self._create_project(path)
            else:
                self._open_project(path)

    def _on_pick_strings(self, e: ft.FilePickerResultEvent) -> None:
        if e.files and len(e.files) > 0:
            path = Path(e.files[0].path)
            if self.state.project:
                self.state.project.config.route_strings_file = str(path)
                save_project(self.state.project)

    def _start_create_project(self) -> None:
        self._pending_create = True
        self._file_picker.get_directory_path()

    def _create_project(self, path: Path) -> None:
        self._pending_create = False
        path.mkdir(parents=True, exist_ok=True)
        config = ProjectConfig(
            prompt=DEFAULT_PROMPT,
            chunk_size=DEFAULT_CHUNK_SIZE,
            model=DEFAULT_MODEL,
        )
        project = Project(directory=path, config=config)
        save_project(project)
        self.state.project = project
        recent = load_recent_projects()
        pstr = str(path)
        if pstr in recent:
            recent.remove(pstr)
        recent.insert(0, pstr)
        save_recent_projects(recent)

        strings_path = path / "strings.json"
        if strings_path.exists():
            project.config.route_strings_file = str(strings_path)
            save_project(project)

        self.on_project_selected(project)

    def _open_global_settings(self) -> None:
        from src.gui.views.settings_view import SettingsView
        dialog = SettingsView(self.page, self.state, on_close=self._refresh)
        self.page.open(dialog)
