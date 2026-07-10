import flet as ft

from src.gui.state import GUIState
from src.io.formats import ProviderType


class SidebarConfig(ft.Column):
    def __init__(
        self,
        state: GUIState,
        on_change: callable,
    ) -> None:
        super().__init__()
        self.state = state
        self.on_change = on_change
        self.spacing = 10
        self.width = 280
        self.scroll = ft.ScrollMode.ALWAYS

        config = state.project.config if state.project else None

        self.provider_dd = ft.Dropdown(
            label="Proveedor",
            value=config.provider.value if config else "gemini",
            options=[
                ft.dropdown.Option("gemini", "Gemini"),
                ft.dropdown.Option("ollama", "Ollama"),
            ],
            on_change=self._changed,
        )

        self.model_tf = ft.TextField(
            label="Modelo",
            value=config.model if config else "gemini-2.5-flash",
            on_change=self._changed,
            width=260,
        )

        self.chunk_tf = ft.TextField(
            label="Chunk size",
            value=str(config.chunk_size) if config else "200",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._changed,
            width=260,
        )

        self.secure_switch = ft.Switch(
            label="Modo seguro (normalice)",
            value=False,
            on_change=self._changed,
        )

        self.prompt_tf = ft.TextField(
            label="Prompt",
            value=config.prompt if config else "",
            multiline=True,
            min_lines=4,
            max_lines=10,
            on_change=self._changed,
            width=260,
        )

        self.controls = [
            ft.Text("Configuración", weight=ft.FontWeight.BOLD, size=16),
            self.provider_dd,
            self.model_tf,
            self.chunk_tf,
            self.secure_switch,
            ft.Text("Prompt", weight=ft.FontWeight.BOLD, size=14),
            self.prompt_tf,
        ]

    def _changed(self, e: ft.ControlEvent) -> None:
        if not self.state.project:
            return
        cfg = self.state.project.config
        cfg.provider = ProviderType(self.provider_dd.value)
        cfg.model = self.model_tf.value
        try:
            cfg.chunk_size = int(self.chunk_tf.value)
        except ValueError:
            pass
        cfg.prompt = self.prompt_tf.value
        self.on_change()

    def refresh(self) -> None:
        if not self.state.project:
            return
        cfg = self.state.project.config
        self.provider_dd.value = cfg.provider.value
        self.model_tf.value = cfg.model
        self.chunk_tf.value = str(cfg.chunk_size)
        self.prompt_tf.value = cfg.prompt
        self.update()
