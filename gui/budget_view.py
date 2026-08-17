"""Budget view — set and track monthly category budgets."""

import tkinter as tk
from tkinter import ttk


class BudgetView(ttk.Frame):
    """Placeholder budget management panel."""

    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Budgets", font=("Segoe UI", 20, "bold")).pack(pady=(30, 10))
        ttk.Label(self, text="Budget setup and usage tracking will appear here.", font=("Segoe UI", 11)).pack()
