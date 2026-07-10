import logging
from pathlib import Path

import flet as ft

from src.gui.state import GUIState
from src.gui.components.pipeline_bar import PipelineBar
from src.gui.components.log_view import LogView
from src.gui.components.sidebar_config import SidebarConfig
from src.config.settings import save_project, load_app_settings
from src.io.file_loader import load_strings, load_translation_dict, load_json, ensure_json
from src.io.file_writer import write_strings, write_translation_dict, write_json
from src.io.formats import Project
from src.processors.matcher import (
    generate_input,
    apply_strings,
    merge_dicts,
    manual_generate,
    manual_apply,
)
from src.processors.normalizer import clean_normalice_new
from src.processors.cleaner import clean_values, clean_void
from src.core.provider import create_provider
from src.core.translator import use_translate

logger = logging.getLogger(__name__)


class ProjectView(ft.Column):
    def __init__(self, page: ft.Page, state: GUIState) -> None:
        super().__init__()
        self._page = page
        self.state = state
        self.spacing = 0
        self.expand = True

        self.log_view = LogView(state)
        self.sidebar = SidebarConfig(state, on_change=self._save_config)
        self.pipeline_bar = PipelineBar(state, on_action=self._handle_action)
        self._build()

    def _build(self) -> None:
        project = self.state.project
        name = project.directory.name if project else "Sin proyecto"

        app_bar = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        ft.Icons.ARROW_BACK,
                        on_click=self._go_back,
                    ),
                    ft.Text(f"Proyecto: {name}", weight=ft.FontWeight.BOLD, size=18),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Config global",
                        icon=ft.Icons.SETTINGS,
                        on_click=self._open_global_settings,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=10,
            bgcolor=ft.Colors.SURFACE,
        )

        main_area = ft.Column(
            [
                ft.Container(
                    content=self.pipeline_bar,
                    padding=10,
                ),
                ft.Container(
                    content=self.log_view,
                    padding=10,
                    expand=True,
                ),
            ],
            expand=True,
        )

        body = ft.Row(
            [
                ft.Container(
                    content=self.sidebar,
                    width=280,
                    padding=10,
                    bgcolor=ft.Colors.SURFACE,
                ),
                ft.Container(content=main_area, expand=True),
            ],
            expand=True,
        )

        self.controls = [app_bar, body]

    def _go_back(self, e: ft.ControlEvent) -> None:
        from src.gui.views.welcome_view import WelcomeView
        self.state.project = None
        page = self._page
        page.clean()
        page.add(
            WelcomeView(page, self.state, on_project_selected=lambda p: self._reload(p))
        )

    def _reload(self, project: Project) -> None:
        self.state.project = project
        page = self._page
        page.clean()
        page.add(ProjectView(page, self.state))

    def _save_config(self) -> None:
        if self.state.project:
            save_project(self.state.project)

    def _open_global_settings(self, e: ft.ControlEvent) -> None:
        from src.gui.views.settings_view import SettingsView
        dlg = SettingsView(self._page, self.state)
        self._page.show_dialog(dlg)

    def _select_strings_file(self) -> None:
        path_tf = ft.TextField(
            label="Ruta de strings.json",
            hint_text="C:\\...\\deltarune-ch1\\strings.json",
            width=400,
        )

        def _set_path() -> None:
            raw = path_tf.value.strip()
            if raw:
                path = Path(raw)
                if path.exists():
                    if self.state.project:
                        self.state.project.config.route_strings_file = str(path)
                        save_project(self.state.project)
                        self.state.add_log("info", f"strings.json seleccionado: {path}")
                        self.log_view.refresh()
                else:
                    path_tf.error_text = "El archivo no existe"
                    self._page.update()
                    return
            dlg.open = False
            self._page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Seleccionar strings.json"),
            content=path_tf,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, 'open', False) or self._page.update()),
                ft.ElevatedButton("Aceptar", on_click=lambda e: _set_path()),
            ],
        )
        self._page.show_dialog(dlg)

    def _handle_action(self, action: str) -> None:
        project = self.state.project
        if not project:
            self.state.add_log("error", "No hay proyecto abierto")
            self.log_view.refresh()
            return

        if action == "select_strings":
            self._select_strings_file()
            return

        try:
            handler = getattr(self, f"_action_{action}", None)
            if handler:
                handler(project)
            else:
                self.state.add_log("warning", f"Acción desconocida: {action}")
                self.log_view.refresh()
        except Exception as e:
            self.state.add_log("error", f"Error en {action}: {e}")
            logger.exception(f"Action {action} failed")
            self.log_view.refresh()

    def _action_input_generate(self, project: Project) -> None:
        self.state.add_log("info", "Generando input...")
        strings = load_strings(project.strings_file_path)
        result = generate_input(strings)
        write_translation_dict(project.input_file_path, result)
        self.state.add_log(
            "success",
            f"Input generado: {len(result.data)} pares en {project.input_file_path}",
        )
        self.log_view.refresh()

    def _action_run(self, project: Project) -> None:
        app_config = load_app_settings()
        provider = create_provider(app_config, project.config)

        if not provider.is_available():
            self.state.add_log("error", "Proveedor no disponible.")
            self.log_view.refresh()
            return

        self.state.add_log("info", f"Iniciando traducción con {provider.name}...")
        ensure_json(project.output_file_path)

        try:
            use_translate(
                provider=provider,
                config=project.config,
                input_path=project.input_file_path,
                output_path=project.output_file_path,
            )
        except Exception as e:
            self.state.add_log("error", f"Traducción fallida: {e}")
        self.log_view.refresh()

    def _action_normalice(self, project: Project) -> None:
        self.state.add_log("info", "Normalizando...")
        ensure_json(project.output_file_path)
        data = load_json(project.output_file_path)
        secure = self.sidebar.secure_switch.value
        result = clean_normalice_new(data, secure=secure)
        write_json(project.normalize_file_path, result)
        self.state.add_log("success", f"Normalizado: {project.normalize_file_path}")
        self.log_view.refresh()

    def _action_apply(self, project: Project) -> None:
        self.state.add_log("info", "Aplicando traducciones...")
        strings = load_strings(project.strings_file_path)
        translations = load_translation_dict(project.normalize_file_path)
        result = apply_strings(strings, translations)
        write_strings(project.result_file_path, result)
        self.state.add_log("success", f"Aplicado: {project.result_file_path}")
        self.log_view.refresh()

    def _action_fix(self, project: Project) -> None:
        self.state.add_log("info", "Aplicando fix...")
        strings = load_strings(project.result_file_path)
        translations = load_translation_dict(project.normalize_file_path)
        result = apply_strings(strings, translations, fix_mode=True)
        write_strings(project.result_file_path, result)
        self.state.add_log("success", f"Fix aplicado: {project.result_file_path}")
        self.log_view.refresh()

    def _action_voids(self, project: Project) -> None:
        self.state.add_log("info", "Limpiando vacíos...")
        ensure_json(project.output_file_path)
        data = load_json(project.output_file_path)
        original = load_json(project.input_file_path)
        result = clean_void(data, original)
        write_json(project.output_file_path, result)
        self.state.add_log("success", "Vacíos eliminados")
        self.log_view.refresh()

    def _action_clean(self, project: Project) -> None:
        self.state.add_log("info", "Limpiando claves...")
        ensure_json(project.output_file_path)
        data = load_json(project.output_file_path)
        result = clean_values(data)
        write_json(project.output_file_path, result)
        self.state.add_log("success", "Claves limpiadas")
        self.log_view.refresh()

    def _action_merge(self, project: Project) -> None:
        self.state.add_log("info", "Fusionando...")
        original = load_json(project.input_file_path)
        overlay = load_json(project.output_file_path)
        result = merge_dicts(original, overlay)
        write_json(project.output_file_path, result)
        self.state.add_log("success", "Fusionado completado")
        self.log_view.refresh()

    def _action_pull_manual(self, project: Project) -> None:
        self.state.add_log("info", "Generando edición manual...")
        original = load_translation_dict(project.input_file_path)
        ensure_json(project.output_file_path)
        translated = load_translation_dict(project.output_file_path)
        result = manual_generate(original, translated)
        write_translation_dict(project.manual_file_path, result)
        self.state.add_log(
            "success",
            f"Manual: {len(result.data)} diálogos pendientes en {project.manual_file_path}",
        )
        self.log_view.refresh()

    def _action_apply_manual(self, project: Project) -> None:
        self.state.add_log("info", "Aplicando edición manual...")
        ensure_json(project.output_file_path)
        current = load_translation_dict(project.output_file_path)
        manual = load_translation_dict(project.manual_file_path)
        result = manual_apply(current, manual)
        write_translation_dict(project.output_file_path, result)
        self.state.add_log("success", "Edición manual aplicada")
        self.log_view.refresh()

    def _action_view(self, project: Project) -> None:
        try:
            original = load_json(project.input_file_path)
        except FileNotFoundError:
            self.state.add_log("error", "No se encuentra lang_input.json")
            self.log_view.refresh()
            return
        try:
            translated = load_json(project.output_file_path)
        except FileNotFoundError:
            translated = {}

        total = len(original)
        done = len(translated)
        missing = total - done
        self.state.add_log("info", f"Total: {total} | Traducidos: {done} | Restantes: {missing}")
        self.log_view.refresh()
