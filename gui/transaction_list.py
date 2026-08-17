"""Transaction list view — browse, search, filter transactions."""

import tkinter as tk
from tkinter import ttk


class TransactionListView(ttk.Frame):
    """Placeholder transaction list panel."""

    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Transactions", font=("Segoe UI", 20, "bold")).pack(pady=(30, 10))
        ttk.Label(self, text="Transaction table, search, and filters will appear here.", font=("Segoe UI", 11)).pack()
