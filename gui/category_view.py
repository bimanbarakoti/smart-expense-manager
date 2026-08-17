"""Category view — manage income/expense categories."""

import tkinter as tk
from tkinter import ttk


class CategoryView(ttk.Frame):
    """Placeholder category management panel."""

    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Categories", font=("Segoe UI", 20, "bold")).pack(pady=(30, 10))
        ttk.Label(self, text="Category list and management controls will appear here.", font=("Segoe UI", 11)).pack()
