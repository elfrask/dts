import tkinter as tk
from tkinter import scrolledtext

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

LEVEL_TAGS = {
    "info": ("blue",),
    "warning": ("orange",),
    "error": ("red",),
    "success": ("green",),
}


class LogView(ttk.Frame):
    def __init__(self, parent: ttk.Window) -> None:
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        lbl = ttk.Label(self, text="Log", font=("Segoe UI", 11, "bold"))
        lbl.grid(row=0, column=0, sticky="w", pady=(0, 3))

        self.text = scrolledtext.ScrolledText(
            self,
            font=("Consolas", 10),
            state=tk.DISABLED,
            wrap=tk.WORD,
            height=15,
        )
        self.text.grid(row=1, column=0, sticky="nsew")

        self.text.tag_config("info", foreground="#5dade2")
        self.text.tag_config("warning", foreground="#f39c12")
        self.text.tag_config("error", foreground="#e74c3c")
        self.text.tag_config("success", foreground="#2ecc71")
        self.text.tag_config("bold", font=("Consolas", 10, "bold"))

    def log(self, level: str, message: str) -> None:
        self.text.config(state=tk.NORMAL)
        tag = level if level in LEVEL_TAGS else "info"
        self.text.insert(tk.END, f"[{level.upper()}] ", tag)
        self.text.insert(tk.END, f"{message}\n", tag)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self) -> None:
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)
