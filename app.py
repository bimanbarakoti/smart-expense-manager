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
from gui import theme as T

# Sidebar dimensions
_SIDEBAR_W = 210

# Nav item definitions: (display label, view key, subtitle shown in header)
_NAV_ITEMS = [
    ("🏠  Dashboard",     "Dashboard",    "Overview of your finances"),
    ("💳  Transactions",  "Transactions", "Add, edit and search transactions"),
    ("🏷   Categories",   "Categories",   "Manage income & expense categories"),
    ("📊  Budgets",       "Budgets",      "Set and track monthly budgets"),
    ("📈  Reports",       "Reports",      "Charts and financial summaries"),
]


class App(tk.Tk):
    """Main application window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(960, 620)
        self.configure(bg=T.CONTENT_BG)

        # Centre on screen
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (sw - APP_WIDTH) // 2
        y = (sh - APP_HEIGHT) // 2
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{x}+{y}")

        self._init_database()
        self._active_btn: tk.Frame | None = None
        self._build_layout()
        self._show_view("Dashboard")

    # ── Database ──────────────────────────────────────────────────────────────

    def _init_database(self) -> None:
        try:
            init_db()
        except Exception as exc:
            messagebox.showerror(
                "Startup Error",
                f"Could not initialise the database:\n\n{exc}\n\n"
                "The application will now close.",
            )
            self.destroy()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        self._build_sidebar()
        self._build_content_area()

    def _build_sidebar(self):
        self._sidebar = tk.Frame(self, bg=T.SIDEBAR_BG, width=_SIDEBAR_W)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # ── Logo / app name ──
        logo_frame = tk.Frame(self._sidebar, bg=T.SIDEBAR_BG)
        logo_frame.pack(fill="x", pady=(20, 4))
        tk.Label(
            logo_frame, text="💰",
            bg=T.SIDEBAR_BG, fg=T.SIDEBAR_ACTIVE_FG,
            font=(T.FONT_FAMILY, 22),
        ).pack()
        tk.Label(
            logo_frame, text="Expense Manager",
            bg=T.SIDEBAR_BG, fg=T.SIDEBAR_ACTIVE_FG,
            font=(T.FONT_FAMILY, 12, "bold"),
        ).pack()

        # Thin divider
        tk.Frame(self._sidebar, bg="#2e3f52", height=1).pack(
            fill="x", padx=16, pady=(12, 8))

        # ── Nav section label ──
        tk.Label(
            self._sidebar, text="NAVIGATION",
            bg=T.SIDEBAR_BG, fg="#4a6278",
            font=(T.FONT_FAMILY, 7, "bold"),
        ).pack(anchor="w", padx=20, pady=(4, 6))

        # ── Nav buttons ──
        self._nav_btns: dict[str, tk.Frame] = {}
        for label, view_name, _ in _NAV_ITEMS:
            self._nav_btns[view_name] = self._make_nav_btn(label, view_name)

        # ── Version at bottom ──
        tk.Label(
            self._sidebar, text="v1.0.0",
            bg=T.SIDEBAR_BG, fg="#3d5166",
            font=(T.FONT_FAMILY, 8),
        ).pack(side="bottom", pady=12)

    def _make_nav_btn(self, label: str, view_name: str) -> tk.Frame:
        """Build one sidebar nav item (Frame containing indicator + label)."""
        container = tk.Frame(self._sidebar, bg=T.SIDEBAR_BG, cursor="hand2")
        container.pack(fill="x")

        # Left active-indicator bar (hidden by default)
        indicator = tk.Frame(container, bg=T.SIDEBAR_BG, width=4)
        indicator.pack(side="left", fill="y")

        lbl = tk.Label(
            container, text=label,
            bg=T.SIDEBAR_BG, fg=T.SIDEBAR_FG,
            font=(T.FONT_FAMILY, 10),
            anchor="w", padx=14, pady=11,
        )
        lbl.pack(side="left", fill="x", expand=True)

        # Store references for state changes
        container._indicator = indicator
        container._label     = lbl

        # Bind click and hover on both container and label
        for widget in (container, lbl):
            widget.bind("<Button-1>", lambda e, v=view_name: self._show_view(v))
            widget.bind("<Enter>",    lambda e, c=container: self._nav_hover(c, True))
            widget.bind("<Leave>",    lambda e, c=container: self._nav_hover(c, False))

        return container

    def _nav_hover(self, container: tk.Frame, entering: bool) -> None:
        """Highlight nav item on hover (unless it is already active)."""
        if container is self._active_btn:
            return
        bg = T.SIDEBAR_HOVER_BG if entering else T.SIDEBAR_BG
        container.config(bg=bg)
        container._label.config(bg=bg)
        container._indicator.config(bg=bg)

    def _build_content_area(self):
        right = tk.Frame(self, bg=T.CONTENT_BG)
        right.pack(side="left", fill="both", expand=True)

        # ── Header bar ──
        self._header = tk.Frame(right, bg=T.PANEL_BG, height=56)
        self._header.pack(fill="x")
        self._header.pack_propagate(False)

        # Left accent line
        tk.Frame(self._header, bg=T.BALANCE_CLR, width=4).pack(side="left", fill="y")

        hdr_text = tk.Frame(self._header, bg=T.PANEL_BG)
        hdr_text.pack(side="left", padx=16, fill="y", expand=False)

        self._header_title = tk.Label(
            hdr_text, text="",
            bg=T.PANEL_BG, fg=T.TEXT_PRIMARY,
            font=(T.FONT_FAMILY, 13, "bold"),
        )
        self._header_title.pack(anchor="w", pady=(10, 0))

        self._header_sub = tk.Label(
            hdr_text, text="",
            bg=T.PANEL_BG, fg=T.TEXT_SECONDARY,
            font=(T.FONT_FAMILY, 8),
        )
        self._header_sub.pack(anchor="w")

        # Thin bottom border on header
        tk.Frame(right, bg=T.CARD_BORDER, height=1).pack(fill="x")

        # ── Content frame ──
        self._content = tk.Frame(right, bg=T.CONTENT_BG)
        self._content.pack(fill="both", expand=True)

        # Instantiate all views
        dashboard = DashboardView(self._content)
        self._views: dict[str, ttk.Frame] = {
            "Dashboard":   dashboard,
            "Transactions": TransactionListView(self._content),
            "Categories":  CategoryView(self._content),
            "Budgets":     BudgetView(self._content),
            "Reports":     ReportView(self._content),
        }
        dashboard.set_navigate(self._show_view)

        for view in self._views.values():
            view.place(relwidth=1, relheight=1)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_view(self, view_name: str):
        """Raise the selected view and update sidebar highlight."""
        # Find subtitle
        subtitle = next(
            (sub for _, v, sub in _NAV_ITEMS if v == view_name), "")

        self._header_title.config(text=view_name)
        self._header_sub.config(text=subtitle)

        # Deactivate previous button
        if self._active_btn is not None:
            self._active_btn.config(bg=T.SIDEBAR_BG)
            self._active_btn._label.config(bg=T.SIDEBAR_BG, fg=T.SIDEBAR_FG,
                                           font=(T.FONT_FAMILY, 10))
            self._active_btn._indicator.config(bg=T.SIDEBAR_BG)

        # Activate new button
        btn = self._nav_btns[view_name]
        btn.config(bg=T.SIDEBAR_ACTIVE_BG)
        btn._label.config(bg=T.SIDEBAR_ACTIVE_BG, fg=T.SIDEBAR_ACTIVE_FG,
                          font=(T.FONT_FAMILY, 10, "bold"))
        btn._indicator.config(bg="#4fc3f7")   # bright blue active indicator
        self._active_btn = btn

        self._views[view_name].lift()

        view = self._views[view_name]
        if hasattr(view, "refresh"):
            view.refresh()


if __name__ == "__main__":
    app = App()
    app.mainloop()
