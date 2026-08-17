"""Transaction form — add/edit transaction dialog."""

import tkinter as tk
from tkinter import ttk


class TransactionForm(tk.Toplevel):
    """Placeholder add/edit transaction dialog."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add / Edit Transaction")
        self.geometry("420x380")
        ttk.Label(self, text="Transaction form will be implemented here.", font=("Segoe UI", 11)).pack(expand=True)
