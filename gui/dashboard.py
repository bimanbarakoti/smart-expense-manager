"""Dashboard view — financial summary, budget status, recent transactions."""

import tkinter as tk
from tkinter import ttk
from datetime import date

from services.transaction_service import get_all_transactions
from services.budget_service import get_budget_status
from utils.calculations import (
    calculate_total_income,
    calculate_total_expenses,
    calculate_balance,
    calculate_monthly_summary,
)
from utils.constants import DISPLAY_DATE_FORMAT

# ── Palette ───────────────────────────────────────────────────────────────────
BG           = "#f4f6f9"
WHITE        = "#ffffff"
INCOME_CLR   = "#2e7d32"
EXPENSE_CLR  = "#c62828"
BALANCE_CLR  = "#1565c0"
MONTH_CLR    = "#6a1b9a"
CARD_SHADOW  = "#e0e4ea"
OVER_CLR     = "#c62828"
OK_CLR       = "#2e7d32"
WARN_CLR     = "#e65100"
PROGRESS_BG  = "#e0e0e0"

RECENT_COLS = [
    ("date",        "Date",        88,  "center"),
    ("type",        "Type",        68,  "center"),
    ("category",    "Category",   120,  "w"),
    ("description", "Description",170,  "w"),
    ("amount",      "Amount",      90,  "e"),
]

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class DashboardView(ttk.Frame):
    """Main dashboard panel — refreshed every time it is shown."""

    def __init__(self, parent, navigate=None):
        """
        Args:
            parent:   Parent widget.
            navigate: Callable(view_name: str) provided by App to switch views.
        """
        super().__init__(parent)
        self._navigate = navigate  # set later by App via set_navigate()
        self.configure(style="TFrame")
        self._build_ui()

    def set_navigate(self, fn) -> None:
        """Inject the navigation callback from App after construction."""
        self._navigate = fn

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        # rows: cards, quick-actions, lower section (budget + recent)
        self.rowconfigure(2, weight=1)

        self._build_cards_row()
        self._build_quick_actions()
        self._build_lower_section()

    def _build_cards_row(self) -> None:
        """Four summary stat cards across the top."""
        frame = tk.Frame(self, bg=BG)
        frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        for i in range(4):
            frame.columnconfigure(i, weight=1)

        card_defs = [
            ("Total Income",        "£0.00", INCOME_CLR,  "income_var"),
            ("Total Expenses",      "£0.00", EXPENSE_CLR, "expense_var"),
            ("Balance",             "£0.00", BALANCE_CLR, "balance_var"),
            ("This Month Expenses", "£0.00", MONTH_CLR,   "month_var"),
        ]
        for col, (label, default, color, attr) in enumerate(card_defs):
            var = tk.StringVar(value=default)
            setattr(self, f"_{attr}", var)
            self._make_card(frame, col, label, var, color)

    def _make_card(self, parent, col: int, label: str,
                   var: tk.StringVar, color: str) -> None:
        card = tk.Frame(parent, bg=WHITE, relief="flat",
                        highlightbackground=CARD_SHADOW, highlightthickness=1)
        card.grid(row=0, column=col, sticky="ew", padx=(0, 12) if col < 3 else 0)

        # Coloured top accent bar
        tk.Frame(card, bg=color, height=4).pack(fill="x")

        tk.Label(card, text=label, bg=WHITE, fg="#607d8b",
                 font=("Segoe UI", 9), pady=(8, 0)).pack(pady=(8, 2))
        tk.Label(card, textvariable=var, bg=WHITE, fg=color,
                 font=("Segoe UI", 18, "bold")).pack(pady=(0, 12))

    def _build_quick_actions(self) -> None:
        """Row of shortcut buttons to other views."""
        frame = tk.Frame(self, bg=WHITE,
                         highlightbackground=CARD_SHADOW, highlightthickness=1)
        frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        tk.Label(frame, text="Quick Actions", bg=WHITE, fg="#37474f",
                 font=("Segoe UI", 10, "bold"), padx=16, pady=10).pack(side="left")

        actions = [
            ("＋ Add Transaction", "Transactions", "#43a047"),
            ("🏷  Categories",      "Categories",   "#1565c0"),
            ("📊  Budgets",         "Budgets",       "#6a1b9a"),
            ("📈  Reports",         "Reports",       "#e65100"),
        ]
        btn_frame = tk.Frame(frame, bg=WHITE)
        btn_frame.pack(side="left", padx=8, pady=8)

        for text, view, color in actions:
            tk.Button(
                btn_frame, text=text,
                bg=color, fg=WHITE,
                font=("Segoe UI", 9, "bold"),
                relief="flat", padx=12, pady=5,
                cursor="hand2",
                command=lambda v=view: self._go(v),
            ).pack(side="left", padx=(0, 8))

    def _build_lower_section(self) -> None:
        """Two-column lower area: budget status (left) + recent transactions (right)."""
        frame = tk.Frame(self, bg=BG)
        frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(0, weight=1)

        self._build_budget_panel(frame)
        self._build_recent_panel(frame)

    def _build_budget_panel(self, parent) -> None:
        """Left panel — current-month budget progress bars."""
        outer = tk.Frame(parent, bg=WHITE,
                         highlightbackground=CARD_SHADOW, highlightthickness=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(outer, bg=WHITE)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        self._budget_title_var = tk.StringVar(value="Budget Status")
        tk.Label(hdr, textvariable=self._budget_title_var, bg=WHITE, fg="#37474f",
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Button(hdr, text="Manage →", bg=WHITE, fg="#1565c0",
                  font=("Segoe UI", 9), relief="flat", cursor="hand2",
                  command=lambda: self._go("Budgets")).pack(side="right")

        ttk.Separator(outer, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=12)

        # Scrollable budget list
        self._budget_scroll_frame = tk.Frame(outer, bg=WHITE)
        self._budget_scroll_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)
        self._budget_scroll_frame.columnconfigure(0, weight=1)

        # Placeholder shown when no budgets exist
        self._no_budget_lbl = tk.Label(
            self._budget_scroll_frame,
            text="No budgets set for this month.\nClick 'Manage →' to add budgets.",
            bg=WHITE, fg="#90a4ae",
            font=("Segoe UI", 10), justify="center",
        )

    def _build_recent_panel(self, parent) -> None:
        """Right panel — last 8 transactions."""
        outer = tk.Frame(parent, bg=WHITE,
                         highlightbackground=CARD_SHADOW, highlightthickness=1)
        outer.grid(row=0, column=1, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        # Header
        hdr = tk.Frame(outer, bg=WHITE)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        tk.Label(hdr, text="Recent Transactions", bg=WHITE, fg="#37474f",
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Button(hdr, text="View All →", bg=WHITE, fg="#1565c0",
                  font=("Segoe UI", 9), relief="flat", cursor="hand2",
                  command=lambda: self._go("Transactions")).pack(side="right")

        ttk.Separator(outer, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=12)

        # Treeview
        tree_frame = tk.Frame(outer, bg=WHITE)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Dashboard.Treeview",
                        rowheight=26, font=("Segoe UI", 9))
        style.configure("Dashboard.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"))
        style.map("Dashboard.Treeview",
                  background=[("selected", "#bbdefb")],
                  foreground=[("selected", "#000000")])

        col_ids = [c[0] for c in RECENT_COLS]
        self._recent_tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings",
            selectmode="none", style="Dashboard.Treeview",
        )
        for col_id, heading, width, anchor in RECENT_COLS:
            self._recent_tree.heading(col_id, text=heading)
            self._recent_tree.column(col_id, width=width, anchor=anchor, minwidth=50)

        self._recent_tree.tag_configure("income",  foreground=INCOME_CLR)
        self._recent_tree.tag_configure("expense", foreground=EXPENSE_CLR)
        self._recent_tree.tag_configure("odd",  background=WHITE)
        self._recent_tree.tag_configure("even", background="#f8f9fa")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._recent_tree.yview)
        self._recent_tree.configure(yscrollcommand=vsb.set)
        self._recent_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload all data from the service layer and redraw every widget."""
        today = date.today()
        transactions = get_all_transactions()

        self._refresh_cards(transactions, today)
        self._refresh_budget(today)
        self._refresh_recent(transactions)

    def _refresh_cards(self, transactions: list, today: date) -> None:
        """Update the four summary stat cards."""
        income   = calculate_total_income(transactions)
        expenses = calculate_total_expenses(transactions)
        balance  = calculate_balance(transactions)
        monthly  = calculate_monthly_summary(transactions, today.year, today.month)

        self._income_var.set(f"£{income:,.2f}")
        self._expense_var.set(f"£{expenses:,.2f}")

        self._balance_var.set(f"£{balance:,.2f}")
        # Colour balance red when negative
        balance_color = EXPENSE_CLR if balance < 0 else BALANCE_CLR
        # Find the balance card label and recolour it
        for widget in self.winfo_children():
            self._recolour_label(widget, self._balance_var, balance_color)

        self._month_var.set(f"£{monthly['expenses']:,.2f}")
        self._budget_title_var.set(
            f"Budget Status — {MONTH_NAMES[today.month]} {today.year}"
        )

    def _recolour_label(self, widget, var: tk.StringVar, color: str) -> None:
        """Recursively find a Label bound to var and update its foreground."""
        if isinstance(widget, tk.Label):
            try:
                if widget.cget("textvariable") == str(var):
                    widget.config(fg=color)
                    return
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._recolour_label(child, var, color)

    def _refresh_budget(self, today: date) -> None:
        """Rebuild the budget progress-bar list for the current month."""
        # Clear previous widgets
        for w in self._budget_scroll_frame.winfo_children():
            w.destroy()

        status_list = get_budget_status(today.month, today.year)

        if not status_list:
            self._no_budget_lbl = tk.Label(
                self._budget_scroll_frame,
                text="No budgets set for this month.\nClick 'Manage →' to add budgets.",
                bg=WHITE, fg="#90a4ae",
                font=("Segoe UI", 10), justify="center",
            )
            self._no_budget_lbl.pack(pady=20)
            return

        for i, s in enumerate(status_list):
            self._make_budget_row(self._budget_scroll_frame, i, s)

    def _make_budget_row(self, parent, row: int, s: dict) -> None:
        """Render one budget category with a progress bar."""
        pct   = min(s["percentage_used"], 100)
        color = OVER_CLR if s["is_over_budget"] else (
                WARN_CLR if pct >= 80 else OK_CLR)

        f = tk.Frame(parent, bg=WHITE)
        f.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        f.columnconfigure(0, weight=1)

        # Category name + amounts
        top = tk.Frame(f, bg=WHITE)
        top.pack(fill="x")
        tk.Label(top, text=s["category_name"], bg=WHITE, fg="#37474f",
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        status_text = (
            f"£{s['spent']:,.2f} / £{s['budget_amount']:,.2f}"
            + (" ⚠ OVER" if s["is_over_budget"] else "")
        )
        tk.Label(top, text=status_text, bg=WHITE, fg=color,
                 font=("Segoe UI", 9)).pack(side="right")

        # Progress bar (canvas-drawn)
        bar_bg = tk.Frame(f, bg=PROGRESS_BG, height=8)
        bar_bg.pack(fill="x", pady=(2, 0))
        bar_bg.update_idletasks()

        # Draw fill after the frame has a real width
        def _draw(event, pct=pct, color=color, bar_bg=bar_bg):
            w = bar_bg.winfo_width()
            fill_w = max(1, int(w * pct / 100))
            fill = tk.Frame(bar_bg, bg=color, height=8, width=fill_w)
            fill.place(x=0, y=0)

        bar_bg.bind("<Configure>", _draw)

    def _refresh_recent(self, transactions: list) -> None:
        """Populate the recent-transactions Treeview with the latest 8 rows."""
        self._recent_tree.delete(*self._recent_tree.get_children())
        recent = transactions[:8]   # already sorted newest-first by service

        for i, tx in enumerate(recent):
            tag_type = "income" if tx.type == "Income" else "expense"
            tag_row  = "odd" if i % 2 == 0 else "even"
            # Format date for display
            try:
                d = date.fromisoformat(tx.date)
                display_date = d.strftime(DISPLAY_DATE_FORMAT)
            except ValueError:
                display_date = tx.date

            self._recent_tree.insert(
                "", "end",
                values=(
                    display_date,
                    tx.type,
                    tx.category_name,
                    tx.description,
                    f"£{tx.amount:,.2f}",
                ),
                tags=(tag_type, tag_row),
            )

    # ── Navigation ────────────────────────────────────────────────────────────

    def _go(self, view_name: str) -> None:
        """Navigate to another view via the callback supplied by App."""
        if self._navigate:
            self._navigate(view_name)
