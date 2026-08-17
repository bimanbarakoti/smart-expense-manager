"""Report view — Matplotlib charts and financial summaries."""

import tkinter as tk
from tkinter import ttk


class ReportView(ttk.Frame):
    """Placeholder reports panel."""

    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Reports", font=("Segoe UI", 20, "bold")).pack(pady=(30, 10))
        ttk.Label(self, text="Income vs expense charts and spending trends will appear here.", font=("Segoe UI", 11)).pack()
