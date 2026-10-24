import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.core.events import Signal, get_event_bus
from src.io.file_loader import load_json
from src.io.formats import AuditEntry


class AuditTab(ttk.Frame):
    """Token/cost audit trail, persisted in the project's audit.json."""

    def __init__(self, parent, state) -> None:
        super().__init__(parent, padding=15)
        self.state = state
        self._entries: list[AuditEntry] = []
        self._build()
        self._load_from_disk()
        get_event_bus().on(Signal.AUDIT, self._on_audit)
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event) -> None:
        if event.widget is not self:
            return
        try:
            get_event_bus().off(Signal.AUDIT, self._on_audit)
        except Exception:
            pass

    # ── Build ──────────────────────────────────────────────────

    def _build(self) -> None:
        project = self.state.project  # type: ignore
        if not project:
            ttk.Label(self, text="No hay proyecto abierto").pack()
            return

        header = ttk.Frame(self)
        header.pack(fill=X, pady=(0, 8))

        ttk.Label(
            header, text="Auditoría de consumo",
            font=("Segoe UI", 14, "bold"),
        ).pack(side=LEFT)

        ttk.Label(
            self,
            text="Cada fila es una solicitud enviada al proveedor. "
                 "Los datos se guardan en audit.json dentro del proyecto.",
            font=("Segoe UI", 9), bootstyle="secondary",
        ).pack(anchor="w", pady=(0, 8))

        # ── Totals ────────────────────────────────────────────
        self._totals = ttk.Labelframe(self, text="Consumo total", padding=10)
        self._totals.pack(fill=X, pady=(0, 10))
        self._totals_labels: dict[str, ttk.Label] = {}
        for i, (key, label) in enumerate([
            ("requests", "Solicitudes"),
            ("input", "Tokens entrada"),
            ("output", "Tokens salida"),
            ("total", "Tokens totales"),
            ("cost", "Costo estimado"),
        ]):
            cell = ttk.Frame(self._totals)
            cell.grid(row=0, column=i, padx=(0, 24), sticky="w")
            ttk.Label(cell, text=label, font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")
            value = ttk.Label(cell, text="0", font=("Segoe UI", 12, "bold"))
            value.pack(anchor="w")
            self._totals_labels[key] = value

        # ── Table ─────────────────────────────────────────────
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=BOTH, expand=True)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = (
            "time", "provider", "model", "input", "output",
            "total", "dialogs", "attempts", "cost",
        )
        self._tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse",
        )
        headings = {
            "time": ("Hora", 140),
            "provider": ("Proveedor", 120),
            "model": ("Modelo", 230),
            "input": ("Tokens entrada", 110),
            "output": ("Tokens salida", 110),
            "total": ("Total tokens", 100),
            "dialogs": ("Diálogos", 80),
            "attempts": ("Intentos", 70),
            "cost": ("Costo est.", 100),
        }
        for col, (text, width) in headings.items():
            self._tree.heading(col, text=text)
            self._tree.column(col, width=width, anchor="center")
        self._tree.column("model", anchor="w")

        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        self._empty_label = ttk.Label(
            table_frame, text="Aún no hay solicitudes registradas.",
            font=("Segoe UI", 10), bootstyle="secondary",
        )
        self._empty_label.grid(row=1, column=0, pady=10)

    # ── Persistence ───────────────────────────────────────────

    def _audit_path(self):
        project = self.state.project  # type: ignore
        return project.audit_file_path if project else None

    def _load_from_disk(self) -> None:
        path = self._audit_path()
        if path is None or not path.exists():
            self._refresh_view()
            return
        try:
            data = load_json(path)
            raw = data.get("entries", []) if isinstance(data, dict) else []
            self._entries = [
                AuditEntry.from_dict(e) for e in raw if isinstance(e, dict)
            ]
        except Exception:
            self._entries = []
        self._refresh_view()

    # ── Events ────────────────────────────────────────────────

    def _on_audit(self, entry: AuditEntry, **kw) -> None:
        self.after_idle(self._append_entry, entry)

    def _append_entry(self, entry: AuditEntry) -> None:
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        self._entries.append(entry)
        self._insert_row(entry)
        self._update_totals()
        # The translator is the single writer; audit.json is already updated.

    # ── View ──────────────────────────────────────────────────

    def _refresh_view(self) -> None:
        if not hasattr(self, "_tree"):
            return
        for item in self._tree.get_children():
            self._tree.delete(item)
        for entry in self._entries:
            self._insert_row(entry)
        self._update_totals()

    def _insert_row(self, entry: AuditEntry) -> None:
        if not hasattr(self, "_tree"):
            return
        self._tree.insert(
            "", "end",
            values=(
                entry.timestamp,
                entry.provider,
                entry.model,
                f"{entry.input_tokens:,}",
                f"{entry.output_tokens:,}",
                f"{entry.total_tokens:,}",
                entry.dialogs,
                entry.attempts,
                f"${entry.cost:.6f}",
            ),
        )
        if hasattr(self, "_empty_label"):
            self._empty_label.grid_remove()

    def _update_totals(self) -> None:
        if not hasattr(self, "_totals_labels"):
            return
        total_in = sum(e.input_tokens for e in self._entries)
        total_out = sum(e.output_tokens for e in self._entries)
        total_cost = sum(e.cost for e in self._entries)
        self._totals_labels["requests"].configure(text=f"{len(self._entries):,}")
        self._totals_labels["input"].configure(text=f"{total_in:,}")
        self._totals_labels["output"].configure(text=f"{total_out:,}")
        self._totals_labels["total"].configure(text=f"{total_in + total_out:,}")
        self._totals_labels["cost"].configure(text=f"${total_cost:.4f}")
