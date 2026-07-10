import json
from pathlib import Path


import flet as ft

from src.gui.state import GUIState
from src.io.formats import AppConfig, ProjectConfig, OllamaConfig, Project
from src.config.settings import load_app_settings, save_app_settings, load_project, save_project
from src.config.defaults import (
    DEFAULT_PROMPT,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
)


def recent_projects_path() -> Path:
    from src.config.defaults import DEFAULT_APP_CONFIG_DIR
    return DEFAULT_APP_CONFIG_DIR / "recent_projects.json"


def load_recent_projects() -> list[str]:
    path = recent_projects_path()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_recent_projects(projects: list[str]) -> None:
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
        self._page = page
        self.state = state
        self.on_project_selected = on_project_selected
        self.spacing = 20
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self._project_list = ft.Column(spacing=8)

        self._build()

    def _build(self) -> None:
        title = ft.Text(
            value="DTS v2 - Dialogue Translation System",
            size=28,
            weight=ft.FontWeight.BOLD,
        )
        subtitle = ft.Text(
            value="Traducción de diálogos de juegos Undertale y Deltarune por Frask Coffee",
            size=14,
            color=ft.Colors.GREY_400,
        )
        
        version = ft.Text(
            value="Frask Coffee - DTS v2.0",
            size=14,
            color=ft.Colors.GREY_400,
            top=2,
            right=2,
            
        )

        
        

        open_btn = ft.ElevatedButton(
            "Abrir proyecto",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._open_project_dialog,
        )
        create_btn = ft.ElevatedButton(
            "Crear nuevo proyecto",
            icon=ft.Icons.CREATE_NEW_FOLDER,
            on_click=self._start_create_project,
        )
        settings_btn = ft.ElevatedButton(
            "Configuración global",
            icon=ft.Icons.SETTINGS,
            on_click=self._open_global_settings,
        )

        self._refresh_recent()

        self.controls = [
            ft.Stack(
                [version],
                height=30
            ),
            ft.Container(height=60),
            title,
            subtitle,
            # version,
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

    def _open_project_dialog(self, e: ft.ControlEvent) -> None:
        """Dialog to type or paste a project directory path."""
        path_tf = ft.TextField(
            label="Ruta del proyecto",
            hint_text="C:\\Users\\...\\deltarune-ch1",
            width=400,
        )

        def _open() -> None:
            raw = path_tf.value.strip()
            if raw:
                p = Path(raw)
                if p.exists():
                    self._open_project(p)
                else:
                    path_tf.error_text = "La ruta no existe"
                    self._page.update()
                    return
            dlg.open = False
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Abrir proyecto"),
            content=path_tf,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, 'open', False) or self._page.update()),
                ft.ElevatedButton("Abrir", on_click=lambda e: _open()),
            ],
        )
        self._page.show_dialog(dlg)

    def _start_create_project(self, e: ft.ControlEvent) -> None:
        """Dialog to create a new project at a given path."""
        path_tf = ft.TextField(
            label="Ruta del nuevo proyecto",
            hint_text="C:\\Users\\...\\deltarune-ch1",
            width=400,
        )

        def _create() -> None:
            raw = path_tf.value.strip()
            if raw:
                self._create_project(Path(raw))
            dlg.open = False
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Crear proyecto"),
            content=path_tf,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, 'open', False) or self._page.update()),
                ft.ElevatedButton("Crear", on_click=lambda e: _create()),
            ],
        )
        self._page.show_dialog(dlg)

    def _create_project(self, path: Path) -> None:
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

    def _open_global_settings(self, e: ft.ControlEvent) -> None:
        from src.gui.views.settings_view import SettingsView
        dlg = SettingsView(self._page, self.state)
        self._page.show_dialog(dlg)
