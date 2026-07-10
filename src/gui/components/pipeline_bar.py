import flet as ft

from src.gui.state import GUIState


class PipelineBar(ft.Row):
    def __init__(
        self,
        state: GUIState,
        on_action: callable,
    ) -> None:
        super().__init__()
        self.state = state
        self.on_action = on_action
        self.spacing = 6
        self.wrap = True

        buttons = [
            ("📂", "Abrir strings.json", "select_strings"),
            ("▶", "Input Generate", "input_generate"),
            ("▶", "Run", "run"),
            ("▶", "Normalice", "normalice"),
            ("▶", "Apply", "apply"),
            ("▶", "Fix", "fix"),
            ("▶", "Voids", "voids"),
            ("🧹", "Clean", "clean"),
            ("🔀", "Merge", "merge"),
            ("📋", "Pull Manual", "pull_manual"),
            ("📝", "Apply Manual", "apply_manual"),
            ("👁", "View", "view"),
        ]

        self.controls = [
            ft.ElevatedButton(
                content=f"{emoji} {label}",
                on_click=lambda e, a=action: self.on_action(a),
                height=36,
                style=ft.ButtonStyle(padding=ft.padding.Padding.all(8)),
            )
            for emoji, label, action in buttons
        ]
