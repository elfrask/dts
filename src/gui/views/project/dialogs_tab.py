import tkinter as tk
from tkinter import ttk, messagebox

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from src.io.file_loader import load_translation_dict, load_json


def view_dialogs_popup(parent: ttkb.Window, state) -> None:
    project = state.project
    if not project:
        return

    try:
        data = load_translation_dict(project.input_file_path)
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró lang_input.json. Ejecuta 'Extraer y generar input' primero.")
        return

    try:
        translated = load_json(project.output_file_path)
    except FileNotFoundError:
        translated = {}

    win = tk.Toplevel(parent)
    win.title(f"Diálogos - {project.directory.name}")
    win.geometry("900x550")
    win.transient(parent)
    win.grab_set()

    main = ttkb.Frame(win, padding=10)
    main.pack(fill=BOTH, expand=True)
    main.columnconfigure(0, weight=1)
    main.rowconfigure(1, weight=1)

    info = ttkb.Label(
        main,
        text=f"Total: {len(data.data)} diálogos | Traducidos: {len(translated)} | Pendientes: {len(data.data) - len(translated)}",
        font=("Segoe UI", 11),
    )
    info.grid(row=0, column=0, sticky="w", pady=(0, 10))

    # Treeview
    cols = ("key", "original", "translated")
    tree = ttkb.Treeview(main, columns=cols, show="headings", height=25)
    tree.heading("key", text="Key ID")
    tree.heading("original", text="Original")
    tree.heading("translated", text="Traducción")
    tree.column("key", width=300, minwidth=200)
    tree.column("original", width=300, minwidth=200)
    tree.column("translated", width=300, minwidth=200)

    scroll_y = ttkb.Scrollbar(main, orient=VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scroll_y.set)

    tree.grid(row=1, column=0, sticky="nsew")
    scroll_y.grid(row=1, column=1, sticky="ns")

    for key, original in data.data.items():
        t = translated.get(key, "")
        tree.insert("", END, values=(key, original, t))

    close_btn = ttkb.Button(main, text="Cerrar", command=win.destroy, bootstyle="secondary")
    close_btn.grid(row=2, column=0, pady=(10, 0))
