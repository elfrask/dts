import ttkbootstrap as ttkb
from ttkbootstrap.constants import *


class ProjectTab(ttkb.Frame):
    def __init__(self, parent: ttkb.Window, state) -> None:
        super().__init__(parent, padding=10)
        self.columnconfigure(0, weight=1)

        if state and state.project:
            cfg = state.project.config
            ttkb.Label(
                self,
                text=f"Configuración de: {state.project.directory.name}",
                font=("Segoe UI", 13, "bold"),
            ).pack(anchor="w", pady=(0, 15))

            items = [
                ("Proveedor:", cfg.provider.value),
                ("Modelo:", cfg.model),
                ("Chunk size:", str(cfg.chunk_size)),
                ("strings.json:", cfg.route_strings_file),
                ("Input:", cfg.route_input_file),
                ("Output:", cfg.route_output_file),
                ("Normalize:", cfg.route_normalize_file),
                ("Resultado:", cfg.route_strings_result_file),
            ]
            for label, value in items:
                row = ttkb.Frame(self)
                row.pack(fill=X, pady=2)
                ttkb.Label(row, text=label, width=16, anchor="e").pack(side=LEFT)
                ttkb.Label(row, text=value, anchor="w").pack(side=LEFT, padx=(10, 0))
        else:
            ttkb.Label(
                self,
                text="No hay ningún proyecto abierto.\nAbre o crea un proyecto para ver su configuración.",
                bootstyle="secondary",
            ).pack(anchor="w", pady=20)
