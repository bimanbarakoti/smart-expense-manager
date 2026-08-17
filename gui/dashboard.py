"""Dashboard view — summary of balance, income, expenses, recent transactions."""

import tkinter as tk
from tkinter import ttk


class DashboardView(ttk.Frame):
    """Placeholder dashboard panel."""

    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Dashboard", font=("Segoe UI", 20, "bold")).pack(pady=(30, 10))
        ttk.Label(self, text="Summary cards and recent transactions will appear here.", font=("Segoe UI", 11)).pack()
