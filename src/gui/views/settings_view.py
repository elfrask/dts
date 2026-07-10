import flet as ft

from typing import Optional, Callable

from src.gui.state import GUIState
from src.config.settings import load_app_settings, save_app_settings
from src.io.formats import AppConfig, OllamaConfig


class SettingsView(ft.AlertDialog):
    def __init__(
        self,
        page: ft.Page,
        state: GUIState,
        on_close: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self._page = page
        self.state = state
        self._on_close_cb = on_close
        self.modal = True
        self.title = ft.Text("Configuración global")

        app_config = load_app_settings()

        self.api_keys_tf = ft.TextField(
            label="API Keys (una por línea)",
            value="\n".join(app_config.api_keys),
            multiline=True,
            min_lines=5,
            max_lines=10,
            width=400,
        )

        self.ollama_host_tf = ft.TextField(
            label="Ollama host",
            value=app_config.ollama.host,
            width=400,
        )

        self.ollama_timeout_tf = ft.TextField(
            label="Ollama timeout (segundos)",
            value=str(app_config.ollama.timeout),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
        )

        self.content = ft.Column(
            [
                ft.Text("Keys de Gemini", weight=ft.FontWeight.BOLD, size=14),
                self.api_keys_tf,
                ft.Container(height=10),
                ft.Text("Ollama", weight=ft.FontWeight.BOLD, size=14),
                self.ollama_host_tf,
                self.ollama_timeout_tf,
            ],
            width=420,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancel),
            ft.ElevatedButton("Guardar", on_click=self._save),
        ]

    def _save(self, e: ft.ControlEvent) -> None:
        keys = [
            k.strip()
            for k in self.api_keys_tf.value.split("\n")
            if k.strip()
        ]
        try:
            timeout = int(self.ollama_timeout_tf.value)
        except ValueError:
            timeout = 120

        config = AppConfig(
            api_keys=keys,
            ollama=OllamaConfig(
                host=self.ollama_host_tf.value.strip(),
                timeout=timeout,
            ),
        )
        save_app_settings(config)
        self.state.app_config = config
        self.open = False
        self.update()

    def _cancel(self, e: ft.ControlEvent) -> None:
        self.open = False
        self.update()
