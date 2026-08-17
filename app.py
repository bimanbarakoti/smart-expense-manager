"""Entry point — Smart Personal Expense & Budget Manager."""

import tkinter as tk
from tkinter import ttk, messagebox

from utils.constants import APP_TITLE, APP_WIDTH, APP_HEIGHT
from database.database import init_db
from gui.dashboard import DashboardView
from gui.transaction_list import TransactionListView
from gui.category_view import CategoryView
from gui.budget_view import BudgetView
from gui.report_view import ReportView

# ── Colour palette ────────────────────────────────────────────────────────────
SIDEBAR_BG = "#1e2a38"
SIDEBAR_FG = "#cdd6e0"
SIDEBAR_ACTIVE_BG = "#2e4057"
SIDEBAR_ACTIVE_FG = "#ffffff"
CONTENT_BG = "#f4f6f9"
HEADER_BG = "#ffffff"


class App(tk.Tk):
    """Main application window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(900, 600)
        self.configure(bg=CONTENT_BG)

        self._init_database()
        self._active_button: tk.Button | None = None
        self._build_layout()
        self._show_view("Dashboard")

    def _init_database(self) -> None:
        """Initialise the database; show an error and exit on failure."""
        try:
            init_db()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Database Error", f"Failed to initialise database:\n{exc}")
            self.destroy()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        """Build the two-column layout: sidebar | content."""
        self._build_sidebar()
        self._build_content_area()

    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # App title / logo area
        tk.Label(
            sidebar,
            text="💰 Expense\nManager",
            bg=SIDEBAR_BG,
            fg=SIDEBAR_ACTIVE_FG,
            font=("Segoe UI", 13, "bold"),
            pady=20,
        ).pack(fill="x")

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=12, pady=(0, 10))

        # Navigation buttons
        nav_items = [
            ("🏠  Dashboard",    "Dashboard"),
            ("💳  Transactions", "Transactions"),
            ("🏷️  Categories",   "Categories"),
            ("📊  Budgets",      "Budgets"),
            ("📈  Reports",      "Reports"),
        ]
        self._nav_buttons: dict[str, tk.Button] = {}
        for label, view_name in nav_items:
            btn = tk.Button(
                sidebar,
                text=label,
                bg=SIDEBAR_BG,
                fg=SIDEBAR_FG,
                activebackground=SIDEBAR_ACTIVE_BG,
                activeforeground=SIDEBAR_ACTIVE_FG,
                font=("Segoe UI", 11),
                anchor="w",
                padx=20,
                pady=10,
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda v=view_name: self._show_view(v),
            )
            btn.pack(fill="x")
            self._nav_buttons[view_name] = btn

        # Version label at the bottom
        tk.Label(
            sidebar,
            text="v1.0.0",
            bg=SIDEBAR_BG,
            fg="#5a6a7a",
            font=("Segoe UI", 9),
        ).pack(side="bottom", pady=10)

    def _build_content_area(self):
        """Right-hand side: header bar + swappable view frame."""
        right = tk.Frame(self, bg=CONTENT_BG)
        right.pack(side="left", fill="both", expand=True)

        # Header bar
        self._header = tk.Frame(right, bg=HEADER_BG, height=50)
        self._header.pack(fill="x")
        self._header.pack_propagate(False)

        self._header_label = tk.Label(
            self._header,
            text="",
            bg=HEADER_BG,
            font=("Segoe UI", 14, "bold"),
            padx=20,
        )
        self._header_label.pack(side="left", fill="y")

        # Content frame — views are stacked here
        self._content = tk.Frame(right, bg=CONTENT_BG)
        self._content.pack(fill="both", expand=True)

        # Instantiate all views once and keep them in a dict
        dashboard = DashboardView(self._content)
        self._views: dict[str, ttk.Frame] = {
            "Dashboard":    dashboard,
            "Transactions": TransactionListView(self._content),
            "Categories":   CategoryView(self._content),
            "Budgets":      BudgetView(self._content),
            "Reports":      ReportView(self._content),
        }
        # Give the dashboard a reference to the navigation function
        dashboard.set_navigate(self._show_view)

        for view in self._views.values():
            view.place(relwidth=1, relheight=1)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_view(self, view_name: str):
        """Raise the selected view and update sidebar highlight."""
        self._header_label.config(text=view_name)

        if self._active_button:
            self._active_button.config(bg=SIDEBAR_BG, fg=SIDEBAR_FG)
        btn = self._nav_buttons[view_name]
        btn.config(bg=SIDEBAR_ACTIVE_BG, fg=SIDEBAR_ACTIVE_FG)
        self._active_button = btn

        self._views[view_name].lift()

        # Refresh data-driven views every time they are shown
        view = self._views[view_name]
        if hasattr(view, "refresh"):
            view.refresh()


if __name__ == "__main__":
    app = App()
    app.mainloop()
