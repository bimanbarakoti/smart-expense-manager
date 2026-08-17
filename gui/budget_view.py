"""Budget view — create and track monthly category budgets."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services.budget_service import (
    get_budget_status,
    get_budgets_for_month,
    create_budget,
    update_budget,
    delete_budget,
    BudgetError,
)
from services.category_service import get_categories_by_type
from gui import theme as T

# Local aliases for readability
BG          = T.CONTENT_BG
WHITE       = T.PANEL_BG
CARD_BORDER = T.CARD_BORDER
OK_CLR      = T.OK_CLR
WARN_CLR    = T.WARN_CLR
OVER_CLR    = T.OVER_CLR
PROG_BG     = T.PROGRESS_BG
BTN_ADD     = T.BALANCE_CLR
BTN_EDIT    = T.TEXT_HEADER
BTN_DEL     = T.BTN_DELETE
BTN_FG      = T.BTN_FG
HEADER_FG   = T.TEXT_HEADER

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Warning threshold — show amber indicator when spending reaches this %
WARN_THRESHOLD = 80


class BudgetView(ttk.Frame):
    """Monthly budget management panel."""

    def __init__(self, parent):
        super().__init__(parent)
        today = date.today()
        self._month = today.month
        self._year  = today.year
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_toolbar()
        self._build_summary_bar()
        self._build_cards_area()

    def _build_toolbar(self) -> None:
        """Month navigator + Add Budget button."""
        bar = tk.Frame(self, bg=WHITE, pady=10,
                       highlightbackground=CARD_BORDER, highlightthickness=1)
        bar.grid(row=0, column=0, sticky="ew")

        nav = tk.Frame(bar, bg=WHITE)
        nav.pack(side="left", padx=T.PAD_PAGE)

        T.make_button(nav, "◀", WHITE, self._prev_month,
                      fg=HEADER_FG, font=(T.FONT_FAMILY, 11),
                      padx=8, pady=4).pack(side="left")

        self._month_label = tk.Label(
            nav, text=self._month_str(),
            bg=WHITE, fg=HEADER_FG,
            font=T.FONT_TITLE, width=18,
        )
        self._month_label.pack(side="left", padx=10)

        T.make_button(nav, "▶", WHITE, self._next_month,
                      fg=HEADER_FG, font=(T.FONT_FAMILY, 11),
                      padx=8, pady=4).pack(side="left")

        T.make_button(nav, "Today", T.FILTER_BG, self._go_today,
                      fg=HEADER_FG, font=T.FONT_SMALL,
                      padx=10, pady=3).pack(side="left", padx=(12, 0))

        T.make_button(
            bar, "＋  Add Budget", BTN_ADD, self._open_add_form,
            font=T.FONT_H3, padx=14,
        ).pack(side="right", padx=T.PAD_PAGE)

    def _build_summary_bar(self) -> None:
        """Three totals: budgeted / spent / remaining for the selected month."""
        bar = tk.Frame(self, bg=T.FILTER_BG, pady=8,
                       highlightbackground=CARD_BORDER, highlightthickness=1)
        bar.grid(row=1, column=0, sticky="ew")

        inner = tk.Frame(bar, bg=T.FILTER_BG)
        inner.pack(padx=T.PAD_PAGE)

        def stat(label, color, attr):
            f = tk.Frame(inner, bg=T.FILTER_BG)
            f.pack(side="left", padx=24)
            tk.Label(f, text=label, bg=T.FILTER_BG, fg=T.TEXT_SECONDARY,
                     font=T.FONT_SMALL).pack()
            var = tk.StringVar(value="£0.00")
            setattr(self, attr, var)
            tk.Label(f, textvariable=var, bg=T.FILTER_BG, fg=color,
                     font=(T.FONT_FAMILY, 13, "bold")).pack()

        stat("Total Budgeted",  T.BALANCE_CLR, "_sum_budget_var")
        stat("Total Spent",     OVER_CLR,      "_sum_spent_var")
        stat("Total Remaining", OK_CLR,        "_sum_remaining_var")

        self._count_var = tk.StringVar(value="0 categories")
        tk.Label(inner, textvariable=self._count_var,
                 bg=T.FILTER_BG, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL).pack(side="left", padx=24)

    def _build_cards_area(self) -> None:
        """Scrollable canvas holding one card per budgeted category."""
        container = tk.Frame(self, bg=BG)
        container.grid(row=2, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient="vertical",
                            command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._cards_frame = tk.Frame(self._canvas, bg=BG)
        self._cards_window = self._canvas.create_window(
            (0, 0), window=self._cards_frame, anchor="nw")

        self._cards_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>",      self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>",  self._on_mousewheel)

        # Empty-state label
        self._empty_label = tk.Label(
            self._cards_frame,
            text="No budgets set for this month.\nClick '＋ Add Budget' to get started.",
            bg=BG, fg="#90a4ae",
            font=("Segoe UI", 11), justify="center",
        )

    # ── Canvas scroll helpers ─────────────────────────────────────────────────

    def _on_frame_configure(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfig(self._cards_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Month navigation ──────────────────────────────────────────────────────

    def _month_str(self) -> str:
        return f"{MONTH_NAMES[self._month]}  {self._year}"

    def _prev_month(self) -> None:
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self.refresh()

    def _next_month(self) -> None:
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self.refresh()

    def _go_today(self) -> None:
        today = date.today()
        self._month, self._year = today.month, today.year
        self.refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload budget data for the selected month and redraw all cards."""
        self._month_label.config(text=self._month_str())

        # Clear existing cards
        for w in self._cards_frame.winfo_children():
            w.destroy()

        status_list = get_budget_status(self._month, self._year)
        self._refresh_summary(status_list)

        if not status_list:
            self._empty_label = tk.Label(
                self._cards_frame,
                text="No budgets set for this month.\nClick '＋ Add Budget' to get started.",
                bg=BG, fg="#90a4ae",
                font=("Segoe UI", 11), justify="center",
            )
            self._empty_label.pack(pady=60)
            return

        # Build a budget_id lookup so Edit/Delete buttons know which row to act on
        budgets = get_budgets_for_month(self._month, self._year)
        self._budget_id_map = {b.category_id: b.id for b in budgets}

        for s in status_list:
            self._make_card(s)

    def _refresh_summary(self, status_list: list[dict]) -> None:
        """Update the three summary totals from the status list."""
        total_budget    = sum(s["budget_amount"] for s in status_list)
        total_spent     = sum(s["spent"]         for s in status_list)
        total_remaining = sum(s["remaining"]     for s in status_list)

        self._sum_budget_var.set(f"£{total_budget:,.2f}")
        self._sum_spent_var.set(f"£{total_spent:,.2f}")
        self._sum_remaining_var.set(f"£{total_remaining:,.2f}")
        self._count_var.set(f"{len(status_list)} categor{'y' if len(status_list)==1 else 'ies'}")

    # ── Card builder ──────────────────────────────────────────────────────────

    def _make_card(self, s: dict) -> None:
        """Render one budget category card."""
        pct   = s["percentage_used"]
        over  = s["is_over_budget"]
        warn  = (not over) and pct >= WARN_THRESHOLD

        bar_color = OVER_CLR if over else (WARN_CLR if warn else OK_CLR)

        # ── Outer card frame ──
        card = tk.Frame(
            self._cards_frame, bg=WHITE,
            highlightbackground=bar_color if (over or warn) else CARD_BORDER,
            highlightthickness=2 if (over or warn) else 1,
        )
        card.pack(fill="x", padx=16, pady=(8, 0))
        card.columnconfigure(1, weight=1)

        # Left accent strip
        tk.Frame(card, bg=bar_color, width=6).grid(
            row=0, column=0, rowspan=3, sticky="ns")

        # ── Header row: category name + badge + buttons ──
        hdr = tk.Frame(card, bg=WHITE)
        hdr.grid(row=0, column=1, sticky="ew", padx=(12, 8), pady=(10, 2))
        hdr.columnconfigure(0, weight=1)

        tk.Label(hdr, text=s["category_name"], bg=WHITE, fg=HEADER_FG,
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")

        # Status badge
        if over:
            badge_text, badge_bg = "⚠  OVER BUDGET", OVER_CLR
        elif warn:
            badge_text, badge_bg = f"⚡  {pct:.0f}% — Approaching limit", WARN_CLR
        else:
            badge_text, badge_bg = f"{pct:.0f}% used", "#e8f5e9"
        badge_fg = WHITE if (over or warn) else OK_CLR

        tk.Label(hdr, text=badge_text, bg=badge_bg, fg=badge_fg,
                 font=("Segoe UI", 8, "bold"), padx=6, pady=2,
                 relief="flat").grid(row=0, column=1, padx=(8, 0))

        # Edit / Delete buttons
        btn_frame = tk.Frame(hdr, bg=WHITE)
        btn_frame.grid(row=0, column=2, padx=(8, 0))

        budget_id = self._budget_id_map.get(s["category_id"])

        tk.Button(
            btn_frame, text="Edit",
            bg=BTN_EDIT, fg=BTN_FG,
            font=("Segoe UI", 8), relief="flat",
            padx=8, pady=2, cursor="hand2",
            command=lambda bid=budget_id, amt=s["budget_amount"],
                           cat=s["category_name"]: self._open_edit_form(bid, amt, cat),
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            btn_frame, text="Delete",
            bg=BTN_DEL, fg=BTN_FG,
            font=("Segoe UI", 8), relief="flat",
            padx=8, pady=2, cursor="hand2",
            command=lambda bid=budget_id,
                           cat=s["category_name"]: self._delete_budget(bid, cat),
        ).pack(side="left")

        # ── Amounts row ──
        amounts = tk.Frame(card, bg=WHITE)
        amounts.grid(row=1, column=1, sticky="ew", padx=(12, 8), pady=(0, 6))

        def amt_label(parent, label, value, color):
            f = tk.Frame(parent, bg=WHITE)
            f.pack(side="left", padx=(0, 24))
            tk.Label(f, text=label, bg=WHITE, fg="#90a4ae",
                     font=("Segoe UI", 8)).pack(anchor="w")
            tk.Label(f, text=f"£{value:,.2f}", bg=WHITE, fg=color,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")

        amt_label(amounts, "Budget",    s["budget_amount"], "#1565c0")
        amt_label(amounts, "Spent",     s["spent"],         bar_color)
        remaining_color = OVER_CLR if s["remaining"] < 0 else OK_CLR
        amt_label(amounts, "Remaining", s["remaining"],     remaining_color)

        # ── Progress bar ──
        prog_outer = tk.Frame(card, bg=PROG_BG, height=10)
        prog_outer.grid(row=2, column=1, sticky="ew", padx=(12, 16), pady=(0, 10))
        prog_outer.columnconfigure(0, weight=1)
        prog_outer.pack_propagate(False)

        def _draw_bar(event, pct=min(pct, 100), color=bar_color):
            w = event.width
            fill_w = max(1, int(w * pct / 100))
            for child in prog_outer.winfo_children():
                child.destroy()
            tk.Frame(prog_outer, bg=color, height=10, width=fill_w).place(x=0, y=0)

        prog_outer.bind("<Configure>", _draw_bar)

    # ── Add / Edit forms ──────────────────────────────────────────────────────

    def _open_add_form(self) -> None:
        """Open the Add Budget modal dialog."""
        _BudgetForm(self, month=self._month, year=self._year, on_save=self.refresh)

    def _open_edit_form(self, budget_id: int, current_amount: float,
                        category_name: str) -> None:
        """Open the Edit Budget modal dialog."""
        _BudgetForm(
            self,
            month=self._month, year=self._year,
            on_save=self.refresh,
            budget_id=budget_id,
            current_amount=current_amount,
            category_name=category_name,
        )

    def _delete_budget(self, budget_id: int, category_name: str) -> None:
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Delete the budget for '{category_name}' "
            f"({MONTH_NAMES[self._month]} {self._year})?\n\n"
            "Existing transactions are not affected.",
            icon="warning",
        )
        if confirmed:
            try:
                delete_budget(budget_id)
                self.refresh()
            except BudgetError as exc:
                messagebox.showerror("Error", str(exc))


# ── Budget form dialog ────────────────────────────────────────────────────────

class _BudgetForm(tk.Toplevel):
    """Modal dialog for adding or editing a budget.

    In add mode:   shows a category combobox + amount field.
    In edit mode:  shows the category name (read-only) + amount field.
    """

    def __init__(
        self,
        parent,
        month: int,
        year: int,
        on_save,
        budget_id: int | None = None,
        current_amount: float | None = None,
        category_name: str | None = None,
    ):
        super().__init__(parent)
        self._month      = month
        self._year       = year
        self._on_save    = on_save
        self._budget_id  = budget_id
        self._edit_mode  = budget_id is not None
        self._cat_map: dict[str, int] = {}   # name → id

        title = "Edit Budget" if self._edit_mode else "Add Budget"
        self.title(title)
        self.geometry("380x280")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.transient(parent)

        # Centre over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 380) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 280) // 2
        self.geometry(f"+{px}+{py}")

        self._build_ui(current_amount, category_name)

    def _build_ui(self, current_amount, category_name) -> None:
        self.configure(bg=WHITE)

        # Title strip
        tk.Label(
            self,
            text=("Edit Budget" if self._edit_mode else "Add Budget") +
                 f"  —  {MONTH_NAMES[self._month]} {self._year}",
            bg=BTN_ADD, fg=BTN_FG,
            font=("Segoe UI", 11, "bold"), pady=10,
        ).pack(fill="x")

        form = tk.Frame(self, bg=WHITE)
        form.pack(fill="both", expand=True, padx=24, pady=16)
        form.columnconfigure(1, weight=1)

        def lbl(row, text):
            tk.Label(form, text=text, bg=WHITE, fg="#37474f",
                     font=("Segoe UI", 10), anchor="w").grid(
                row=row, column=0, sticky="w", pady=6, padx=(0, 16))

        # Row 0 — Category
        lbl(0, "Category *")
        if self._edit_mode:
            # Read-only in edit mode
            tk.Label(form, text=category_name, bg="#f5f5f5", fg="#37474f",
                     font=("Segoe UI", 10), relief="groove",
                     padx=8, pady=4, anchor="w").grid(
                row=0, column=1, sticky="ew", pady=6)
        else:
            expense_cats = get_categories_by_type("Expense")
            self._cat_map = {c.name: c.id for c in expense_cats}
            self._cat_var = tk.StringVar()
            cb = ttk.Combobox(form, textvariable=self._cat_var,
                              values=list(self._cat_map.keys()),
                              state="readonly", width=22)
            cb.grid(row=0, column=1, sticky="w", pady=6)
            if self._cat_map:
                self._cat_var.set(list(self._cat_map.keys())[0])

        # Row 1 — Amount
        lbl(1, "Amount (£) *")
        self._amount_var = tk.StringVar(
            value=str(current_amount) if current_amount is not None else "")
        ttk.Entry(form, textvariable=self._amount_var, width=16).grid(
            row=1, column=1, sticky="w", pady=6)

        # Row 2 — hint
        tk.Label(form, text="Enter the maximum spending limit for this category.",
                 bg=WHITE, fg="#90a4ae",
                 font=("Segoe UI", 8), wraplength=220, justify="left").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # Buttons
        btn_frame = tk.Frame(self, bg=WHITE)
        btn_frame.pack(fill="x", padx=24, pady=(0, 16))

        tk.Button(
            btn_frame, text="Save",
            bg=BTN_ADD, fg=BTN_FG,
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._save,
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_frame, text="Cancel",
            bg=BTN_EDIT, fg=BTN_FG,
            font=("Segoe UI", 10), relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self.destroy,
        ).pack(side="right")

    def _save(self) -> None:
        amount_str = self._amount_var.get().strip()

        try:
            if self._edit_mode:
                update_budget(self._budget_id, amount_str)
            else:
                cat_name = self._cat_var.get()
                cat_id   = self._cat_map.get(cat_name)
                if not cat_id:
                    messagebox.showerror("Error", "Please select a category.", parent=self)
                    return
                create_budget(cat_id, self._month, self._year, amount_str)

            self._on_save()
            self.destroy()

        except BudgetError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
