import json
from pathlib import Path

import flet as ft

from src.gui.state import GUIState
from src.io.file_loader import load_translation_dict
from src.io.file_writer import write_translation_dict
from src.io.formats import TranslationDict


class ManualEditView(ft.AlertDialog):
    def __init__(self, page: ft.Page, state: GUIState) -> None:
        super().__init__()
        self._page = page
        self.state = state
        self.modal = True
        self.title = ft.Text("Edición manual de diálogos")

        project = state.project
        if not project:
            self.content = ft.Text("No hay proyecto abierto")
            return

        try:
            data = load_translation_dict(project.manual_file_path)
        except FileNotFoundError:
            data = TranslationDict(data={})

        self._original: dict[str, str] = dict(data.data)
        self._rows: list[ManualEditRow] = []
        self._table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Key", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Original", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Traducción", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )

        for key, value in self._original.items():
            row = ManualEditRow(key, value)
            self._rows.append(row)
            self._table.rows.append(row.build())

        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"{len(self._original)} diálogos pendientes",
                        size=12,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Container(
                        content=self._table,
                        expand=True,
                    ),
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=900,
            height=500,
        )

        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancel),
            ft.ElevatedButton("Guardar cambios", on_click=self._save),
        ]

    def _save(self, e: ft.ControlEvent) -> None:
        if not self.state.project:
            return
        output: dict[str, str] = {}
        for row in self._rows:
            text = row.text_field.value.strip()
            if text:
                output[row.key] = text
        write_translation_dict(
            self.state.project.manual_file_path,
            TranslationDict(data=output),
        )
        self.state.add_log("success", f"Guardados {len(output)} diálogos manuales")
        self.open = False
        self.update()

    def _cancel(self, e: ft.ControlEvent) -> None:
        self.open = False
        self.update()


class ManualEditRow:
    def __init__(self, key: str, original: str) -> None:
        self.key = key
        self.original = original
        self.text_field = ft.TextField(
            value="",
            multiline=True,
            min_lines=1,
            max_lines=3,
            width=300,
            text_size=12,
        )

    def build(self) -> ft.DataRow:
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(self.key, size=11, font_family="Consolas")),
                ft.DataCell(ft.Text(self.original, size=12)),
                ft.DataCell(self.text_field),
            ]
        )
