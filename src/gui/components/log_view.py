import flet as ft

from src.gui.state import GUIState


COLORS = {
    "info": ft.Colors.BLUE_200,
    "warning": ft.Colors.AMBER_200,
    "error": ft.Colors.RED_200,
    "success": ft.Colors.GREEN_200,
    "debug": ft.Colors.GREY_400,
}


class LogView(ft.Column):
    def __init__(self, state: GUIState) -> None:
        super().__init__()
        self.state = state
        self.spacing = 2
        self.scroll = ft.ScrollMode.ALWAYS
        self.auto_scroll = True
        self.expand = True
        self._controls_ref: list[ft.Text] = []

    def refresh(self) -> None:
        self._controls_ref.clear()
        for entry in self.state.log_entries:
            color = COLORS.get(entry.level, ft.Colors.WHITE)
            self._controls_ref.append(
                ft.Text(entry.message, color=color, size=12, font_family="Consolas")
            )
        self.controls = self._controls_ref
        self.update()
