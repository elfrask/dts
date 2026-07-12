import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.config.settings import save_project
from src.io.file_loader import load_json, ensure_json
from src.io.file_writer import write_json, write_translation_dict
from src.io.formats import TranslationDict
from src.processors.matcher import manual_generate, manual_apply
from src.processors.cleaner import clean_void


class ReviewTab(ttk.Frame):
    def __init__(self, parent: ttk.Window, state) -> None:
        super().__init__(parent, padding=10)
        self.state = state
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._rebuild_data()
        self._build()

    def _rebuild_data(self) -> None:
        project = self.state.project #type: ignore
        if not project:
            self._originals = {}
            self._translated = {}
            self._manual = {}
            self._pending_keys: set[str] = set()
            return

        try:
            self._originals = load_json(project.input_file_path)
        except FileNotFoundError:
            self._originals = {}
        try:
            self._translated = load_json(project.output_file_path)
        except FileNotFoundError:
            self._translated = {}
        try:
            self._manual = load_json(project.manual_file_path)
        except FileNotFoundError:
            self._manual = {}

        # ── Determine pending keys ──
        pending: set[str] = set()

        # 1. Untranslated keys (from manual_generate logic)
        for key in self._originals:
            if key not in self._translated:
                pending.add(key)

        # 2. Void keys (from clean_void logic)
        cleaned = clean_void(dict(self._translated), dict(self._originals))
        for key in self._translated:
            if key not in cleaned:
                pending.add(key)

        # 3. Keys with manual edits pending
        for key in self._manual:
            pending.add(key)

        self._pending_keys = pending

    def _build(self) -> None:
        project = self.state.project #type: ignore
        if not project:
            ttk.Label(self, text="No hay proyecto abierto").pack()
            return

        merged = dict(self._translated)
        merged.update(self._manual)

        # ── Top bar ──
        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        bar.columnconfigure(0, weight=1)

        ttk.Label(
            bar,
            text=f"Total: {len(self._originals)}  |  Traducidas: {len(self._translated)}  |  Pendientes: {len(self._pending_keys)}",
            font=("Segoe UI", 11),
        ).grid(row=0, column=0, sticky="w")

        btn_row = ttk.Frame(bar)
        btn_row.grid(row=0, column=1, sticky="e")

        ttk.Button(
            btn_row, text="Pull pendientes",
            command=self._pull_manual,
            bootstyle="info-outline",
        ).pack(side=LEFT, padx=(0, 6))
        ttk.Button(
            btn_row, text="Guardar cambios",
            command=self._apply_edits,
            bootstyle="success",
        ).pack(side=LEFT)

        # ── Filter toggle ──
        self._filter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self, text="Mostrar solo pendientes de revisión",
            variable=self._filter_var,
            command=self._repopulate,
            bootstyle="round-toggle",
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        # ── Treeview ──
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=3, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("key", "original", "translation")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        self._tree.heading("key", text="Key ID")
        self._tree.heading("original", text="Original")
        self._tree.heading("translation", text="Traducción")
        self._tree.column("key", width=280, minwidth=180)
        self._tree.column("original", width=300, minwidth=200)
        self._tree.column("translation", width=300, minwidth=200)

        self._tree.tag_configure("pending", background="#3d2a1f")
        self._tree.tag_configure("void", background="#3a1a1a")

        scroll_v = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_v.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll_v.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<Double-1>", self._on_double_click)

        self._repopulate()

    def _repopulate(self) -> None:
        self._tree.delete(*self._tree.get_children())
        only_pending = self._filter_var.get()
        merged = dict(self._translated)
        merged.update(self._manual)

        cleaned = clean_void(dict(self._translated), dict(self._originals))

        for key, original in self._originals.items():
            if only_pending and key not in self._pending_keys:
                continue

            trans = merged.get(key, "")
            tags = []
            if key not in self._translated:
                tags.append("pending")
            elif key not in cleaned:
                tags.append("void")
            elif key in self._manual:
                tags.append("pending")

            item_id = self._tree.insert("", "end", values=(key, original, trans))
            if tags:
                self._tree.item(item_id, tags=tags)

    # ── Pull untranslated ───────────────────────────────────────

    def _pull_manual(self) -> None:
        project = self.state.project #type: ignore
        if not project:
            return
        orig = TranslationDict(data=self._originals)
        tran = TranslationDict(data=self._translated)
        result = manual_generate(orig, tran)
        write_translation_dict(project.manual_file_path, result)

        count = len(result.data)
        if count:
            messagebox.showinfo(
                "Pull completado",
                f"Se encontraron {count} diálogos pendientes.\n"
                f"Archivo: {project.manual_file_path}",
            )
        else:
            messagebox.showinfo("Pull completado", "No hay diálogos pendientes.")
        self._rebuild()

    # ── Double-click edit ───────────────────────────────────────

    def _on_double_click(self, event) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self._tree.item(item, "values")
        if not values:
            return
        key, original, current_trans = values

        dialog = tk.Toplevel(self)
        dialog.title(f"Editar traducción — {key}")
        dialog.geometry("650x300") 
        dialog.transient(self) #type: ignore
        dialog.grab_set()
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(1, weight=1)

        ttk.Label(dialog, text=f"Original: {original}", font=("Segoe UI", 10),
                  bootstyle="primary").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        text = tk.Text(dialog, wrap="word", font=("Consolas", 10), height=10,
                       relief="flat", borderwidth=1,
                       highlightthickness=1, highlightbackground="#444")
        text.insert("1.0", current_trans)
        text.grid(row=1, column=0, sticky="nsew", padx=10)
        text.focus()

        scroll = ttk.Scrollbar(dialog, orient=VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.grid(row=1, column=1, sticky="ns", pady=(0, 10))

        def save():
            new_trans = text.get("1.0", "end-1c")
            self._tree.item(item, values=(key, original, new_trans))
            project = self.state.project #type: ignore
            if project:
                try:
                    manual = load_json(project.manual_file_path)
                except FileNotFoundError:
                    manual = {}
                manual[key] = new_trans
                write_json(project.manual_file_path, manual)
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=10, padx=10)

        ttk.Button(btn_frame, text="Guardar", command=save, bootstyle="success"
                   ).pack(side=RIGHT, padx=(6, 0))
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy, bootstyle="secondary"
                   ).pack(side=RIGHT)

        dialog.bind("<Control-Return>", lambda e: save())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    # ── Apply edits ─────────────────────────────────────────────

    def _apply_edits(self) -> None:
        project = self.state.project #type: ignore
        if not project:
            return
        try:
            manual = load_json(project.manual_file_path)
        except FileNotFoundError:
            messagebox.showerror("Error", "No hay archivo de edición manual.\nHaz 'Pull pendientes' primero.")
            return

        if not manual:
            messagebox.showinfo("Sin cambios", "No hay ediciones pendientes para aplicar.")
            return

        current = TranslationDict(data=self._translated)
        manual_dt = TranslationDict(data=manual)
        result = manual_apply(current, manual_dt)
        write_json(project.output_file_path, result.data)

        messagebox.showinfo(
            "Cambios aplicados",
            f"Se aplicaron {len(manual)} ediciones a:\n{project.output_file_path}",
        )
        self._rebuild()

    # ── Rebuild ─────────────────────────────────────────────────

    def _rebuild(self) -> None:
        self._rebuild_data()
        for w in self.winfo_children():
            w.destroy()
        self._build()
