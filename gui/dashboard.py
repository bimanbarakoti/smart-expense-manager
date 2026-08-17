"""Dashboard view — financial summary, budget status, recent transactions."""

import tkinter as tk
from tkinter import ttk
from datetime import date, datetime, timezone

from services.transaction_service import get_all_transactions
from services.budget_service import get_budget_status
from utils.calculations import (
    calculate_total_income,
    calculate_total_expenses,
    calculate_balance,
    calculate_monthly_summary,
)
from utils.constants import DISPLAY_DATE_FORMAT
from gui import theme as T

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

RECENT_COLS = [
    ("date",        "Date",        90,  "center"),
    ("type",        "Type",        68,  "center"),
    ("category",    "Category",   120,  "w"),
    ("description", "Description", 180, "w"),
    ("amount",      "Amount (£)",  95,  "e"),
]


class DashboardView(ttk.Frame):
    """Main dashboard panel — refreshed every time it is shown."""

    def __init__(self, parent, navigate=None):
        super().__init__(parent)
        self._navigate = navigate
        self.configure(style="TFrame")
        self._build_ui()

    def set_navigate(self, fn) -> None:
        self._navigate = fn

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build_cards_row()
        self._build_quick_actions()
        self._build_lower_section()

    def _build_cards_row(self) -> None:
        frame = tk.Frame(self, bg=T.CONTENT_BG)
        frame.grid(row=0, column=0, sticky="ew",
                   padx=T.PAD_PAGE, pady=(T.PAD_PAGE, 8))
        for i in range(4):
            frame.columnconfigure(i, weight=1)

        card_defs = [
            ("Total Income",        "£0.00", T.INCOME_CLR,  "_income_var"),
            ("Total Expenses",      "£0.00", T.EXPENSE_CLR, "_expense_var"),
            ("Net Balance",         "£0.00", T.BALANCE_CLR, "_balance_var"),
            ("This Month Expenses", "£0.00", T.MONTH_CLR,   "_month_var"),
        ]
        for col, (label, default, color, attr) in enumerate(card_defs):
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            self._make_stat_card(frame, col, label, var, color,
                                 last=(col == 3))

    def _make_stat_card(self, parent, col, label, var, color,
                        last=False) -> None:
        card = tk.Frame(parent, bg=T.PANEL_BG,
                        highlightbackground=T.CARD_BORDER,
                        highlightthickness=1)
        card.grid(row=0, column=col, sticky="ew",
                  padx=(0, 0 if last else 10))

        # Coloured top accent
        tk.Frame(card, bg=color, height=4).pack(fill="x")

        tk.Label(card, text=label, bg=T.PANEL_BG, fg=T.TEXT_SECONDARY,
                 font=T.FONT_STAT_LABEL).pack(pady=(10, 2))
        tk.Label(card, textvariable=var, bg=T.PANEL_BG, fg=color,
                 font=T.FONT_STAT_VALUE).pack(pady=(0, 12))

    def _build_quick_actions(self) -> None:
        frame = T.panel(self)
        frame.grid(row=1, column=0, sticky="ew",
                   padx=T.PAD_PAGE, pady=(0, 8))

        tk.Label(frame, text="Quick Actions", bg=T.PANEL_BG,
                 fg=T.TEXT_HEADER, font=T.FONT_H3,
                 padx=T.PAD_PAGE, pady=10).pack(side="left")

        btn_frame = tk.Frame(frame, bg=T.PANEL_BG)
        btn_frame.pack(side="left", padx=4, pady=8)

        actions = [
            ("＋  Add Transaction", "Transactions", T.INCOME_BTN),
            ("🏷   Categories",     "Categories",   T.BALANCE_CLR),
            ("📊  Budgets",         "Budgets",       T.MONTH_CLR),
            ("📈  Reports",         "Reports",       "#e65100"),
        ]
        for text, view, color in actions:
            T.make_button(btn_frame, text, color,
                          lambda v=view: self._go(v),
                          font=T.FONT_SMALL, padx=12, pady=5).pack(
                side="left", padx=(0, 8))

    def _build_lower_section(self) -> None:
        frame = tk.Frame(self, bg=T.CONTENT_BG)
        frame.grid(row=2, column=0, sticky="nsew",
                   padx=T.PAD_PAGE, pady=(0, T.PAD_PAGE))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(0, weight=1)
        self._build_budget_panel(frame)
        self._build_recent_panel(frame)

    def _build_budget_panel(self, parent) -> None:
        outer = T.panel(parent)
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        # Header
        hdr = tk.Frame(outer, bg=T.PANEL_BG)
        hdr.grid(row=0, column=0, sticky="ew",
                 padx=T.PAD_CARD, pady=(T.PAD_CARD, 4))
        self._budget_title_var = tk.StringVar(value="Budget Status")
        tk.Label(hdr, textvariable=self._budget_title_var,
                 bg=T.PANEL_BG, fg=T.TEXT_HEADER,
                 font=T.FONT_H2).pack(side="left")
        T.make_button(hdr, "Manage →", T.PANEL_BG,
                      lambda: self._go("Budgets"),
                      fg=T.BALANCE_CLR, font=T.FONT_SMALL,
                      padx=4, pady=2).pack(side="right")

        tk.Frame(outer, bg=T.CARD_BORDER, height=1).grid(
            row=1, column=0, sticky="ew", padx=T.PAD_CARD)

        # Scrollable budget list
        self._budget_scroll_frame = tk.Frame(outer, bg=T.PANEL_BG)
        self._budget_scroll_frame.grid(row=2, column=0, sticky="nsew",
                                       padx=T.PAD_CARD, pady=8)
        self._budget_scroll_frame.columnconfigure(0, weight=1)

    def _build_recent_panel(self, parent) -> None:
        outer = T.panel(parent)
        outer.grid(row=0, column=1, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        # Header
        hdr = tk.Frame(outer, bg=T.PANEL_BG)
        hdr.grid(row=0, column=0, sticky="ew",
                 padx=T.PAD_CARD, pady=(T.PAD_CARD, 4))
        tk.Label(hdr, text="Recent Transactions",
                 bg=T.PANEL_BG, fg=T.TEXT_HEADER,
                 font=T.FONT_H2).pack(side="left")
        T.make_button(hdr, "View All →", T.PANEL_BG,
                      lambda: self._go("Transactions"),
                      fg=T.BALANCE_CLR, font=T.FONT_SMALL,
                      padx=4, pady=2).pack(side="right")

        tk.Frame(outer, bg=T.CARD_BORDER, height=1).grid(
            row=1, column=0, sticky="ew", padx=T.PAD_CARD)

        tree_frame = tk.Frame(outer, bg=T.PANEL_BG)
        tree_frame.grid(row=2, column=0, sticky="nsew",
                        padx=8, pady=8)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        T.apply_treeview_style("Dash", row_height=26)
        col_ids = [c[0] for c in RECENT_COLS]
        self._recent_tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings",
            selectmode="none", style="Dash.Treeview",
        )
        for col_id, heading, width, anchor in RECENT_COLS:
            self._recent_tree.heading(col_id, text=heading)
            self._recent_tree.column(col_id, width=width, anchor=anchor,
                                     minwidth=50)

        self._recent_tree.tag_configure("income",  foreground=T.INCOME_CLR)
        self._recent_tree.tag_configure("expense", foreground=T.EXPENSE_CLR)
        self._recent_tree.tag_configure("odd",  background=T.ROW_ODD)
        self._recent_tree.tag_configure("even", background=T.ROW_EVEN)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._recent_tree.yview)
        self._recent_tree.configure(yscrollcommand=vsb.set)
        self._recent_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        today = datetime.now(timezone.utc).astimezone().date()
        transactions = get_all_transactions()
        self._refresh_cards(transactions, today)
        self._refresh_budget(today)
        self._refresh_recent(transactions)

    def _refresh_cards(self, transactions: list, today: date) -> None:
        income   = calculate_total_income(transactions)
        expenses = calculate_total_expenses(transactions)
        balance  = calculate_balance(transactions)
        monthly  = calculate_monthly_summary(transactions, today.year, today.month)

        self._income_var.set(f"£{income:,.2f}")
        self._expense_var.set(f"£{expenses:,.2f}")
        self._balance_var.set(f"£{balance:,.2f}")
        self._month_var.set(f"£{monthly['expenses']:,.2f}")
        self._budget_title_var.set(
            f"Budget Status — {MONTH_NAMES[today.month]} {today.year}")

        # Recolour balance card dynamically
        balance_color = T.EXPENSE_CLR if balance < 0 else T.BALANCE_CLR
        for widget in self.winfo_children():
            self._recolour_label(widget, self._balance_var, balance_color)

    def _recolour_label(self, widget, var: tk.StringVar, color: str) -> None:
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
        for w in self._budget_scroll_frame.winfo_children():
            w.destroy()

        status_list = get_budget_status(today.month, today.year)

        if not status_list:
            tk.Label(
                self._budget_scroll_frame,
                text="No budgets set for this month.\nClick 'Manage →' to add budgets.",
                bg=T.PANEL_BG, fg=T.TEXT_MUTED,
                font=T.FONT_BODY, justify="center",
            ).pack(pady=20)
            return

        for i, s in enumerate(status_list):
            self._make_budget_row(self._budget_scroll_frame, i, s)

    def _make_budget_row(self, parent, row: int, s: dict) -> None:
        pct   = min(s["percentage_used"], 100)
        color = (T.OVER_CLR if s["is_over_budget"]
                 else T.WARN_CLR if pct >= 80 else T.OK_CLR)

        f = tk.Frame(parent, bg=T.PANEL_BG)
        f.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        f.columnconfigure(0, weight=1)

        top = tk.Frame(f, bg=T.PANEL_BG)
        top.pack(fill="x")
        tk.Label(top, text=s["category_name"], bg=T.PANEL_BG,
                 fg=T.TEXT_HEADER, font=T.FONT_SMALL + ("bold",)).pack(
            side="left")

        status_text = (
            f"£{s['spent']:,.2f} / £{s['budget_amount']:,.2f}"
            + (" ⚠ OVER" if s["is_over_budget"] else "")
        )
        tk.Label(top, text=status_text, bg=T.PANEL_BG, fg=color,
                 font=T.FONT_SMALL).pack(side="right")

        bar_bg = tk.Frame(f, bg=T.PROGRESS_BG, height=6)
        bar_bg.pack(fill="x", pady=(2, 0))

        def _draw(event, pct=pct, color=color, bar_bg=bar_bg):
            w = bar_bg.winfo_width()
            fill_w = max(1, int(w * pct / 100))
            for child in bar_bg.winfo_children():
                child.destroy()
            tk.Frame(bar_bg, bg=color, height=6, width=fill_w).place(x=0, y=0)

        bar_bg.bind("<Configure>", _draw)

    def _refresh_recent(self, transactions: list) -> None:
        self._recent_tree.delete(*self._recent_tree.get_children())
        for i, tx in enumerate(transactions[:8]):
            tag_type = "income" if tx.type == "Income" else "expense"
            tag_row  = "odd" if i % 2 == 0 else "even"
            try:
                d = date.fromisoformat(tx.date)
                display_date = d.strftime(DISPLAY_DATE_FORMAT)
            except ValueError:
                display_date = tx.date

            self._recent_tree.insert(
                "", "end",
                values=(display_date, tx.type, tx.category_name,
                        tx.description, f"£{tx.amount:,.2f}"),
                tags=(tag_type, tag_row),
            )

    # ── Navigation ────────────────────────────────────────────────────────────

    def _go(self, view_name: str) -> None:
        if self._navigate:
            self._navigate(view_name)
