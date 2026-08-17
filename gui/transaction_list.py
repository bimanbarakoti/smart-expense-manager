"""Transaction list view — browse, search, and manage all transactions."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services.transaction_service import (
    get_all_transactions,
    search_transactions,
    delete_transaction,
    TransactionError,
)
from services.category_service import get_all_categories
from services.export_service import export_transactions_csv, generate_pdf_report, ExportError
from gui.transaction_form import TransactionForm
from utils.constants import TRANSACTION_TYPES
from utils.calculations import calculate_total_income, calculate_total_expenses

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#f4f6f9"
WHITE       = "#ffffff"
INCOME_CLR  = "#2e7d32"
EXPENSE_CLR = "#c62828"
BTN_INCOME  = "#43a047"
BTN_EXPENSE = "#e53935"
BTN_EDIT    = "#1565c0"
BTN_DELETE  = "#b71c1c"
BTN_EXPORT  = "#6a1b9a"
BTN_FG      = "#ffffff"
HEADER_BG   = "#37474f"
HEADER_FG   = "#ffffff"
ROW_ODD     = "#ffffff"
ROW_EVEN    = "#f1f3f5"
SEL_BG      = "#bbdefb"

# Treeview column definitions: (id, heading, width, anchor)
COLUMNS = [
    ("date",        "Date",           90,  "center"),
    ("type",        "Type",           75,  "center"),
    ("category",    "Category",      130,  "w"),
    ("description", "Description",   200,  "w"),
    ("amount",      "Amount (£)",    100,  "e"),
    ("payment",     "Payment",       110,  "center"),
]


class TransactionListView(ttk.Frame):
    """Full transaction management panel."""

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")
        self._all_categories = []   # list[Category] — refreshed on load
        self._transactions   = []   # list[Transaction] — currently displayed

        self._build_ui()
        self.refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.configure(padding=0)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_toolbar()
        self._build_filter_bar()
        self._build_table()
        self._build_summary_bar()

    def _build_toolbar(self) -> None:
        """Top bar: Add Income / Add Expense buttons."""
        bar = tk.Frame(self, bg=WHITE, pady=10)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)

        btn_frame = tk.Frame(bar, bg=WHITE)
        btn_frame.pack(side="left", padx=16)

        tk.Button(
            btn_frame, text="＋  Add Income",
            bg=BTN_INCOME, fg=BTN_FG,
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=14, pady=6, cursor="hand2",
            command=self._add_income,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_frame, text="＋  Add Expense",
            bg=BTN_EXPENSE, fg=BTN_FG,
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=14, pady=6, cursor="hand2",
            command=self._add_expense,
        ).pack(side="left")

        # Edit / Delete on the right
        action_frame = tk.Frame(bar, bg=WHITE)
        action_frame.pack(side="right", padx=16)

        self._edit_btn = tk.Button(
            action_frame, text="✏  Edit",
            bg=BTN_EDIT, fg=BTN_FG,
            font=("Segoe UI", 10), relief="flat",
            padx=12, pady=6, cursor="hand2",
            state="disabled",
            command=self._edit_selected,
        )
        self._edit_btn.pack(side="left", padx=(0, 8))

        self._delete_btn = tk.Button(
            action_frame, text="🗑  Delete",
            bg=BTN_DELETE, fg=BTN_FG,
            font=("Segoe UI", 10), relief="flat",
            padx=12, pady=6, cursor="hand2",
            state="disabled",
            command=self._delete_selected,
        )
        self._delete_btn.pack(side="left")

        # Export buttons
        export_frame = tk.Frame(bar, bg=WHITE)
        export_frame.pack(side="right", padx=(0, 8))

        tk.Button(
            export_frame, text="📄  Export CSV",
            bg=BTN_EXPORT, fg=BTN_FG,
            font=("Segoe UI", 10), relief="flat",
            padx=12, pady=6, cursor="hand2",
            command=self._export_csv,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            export_frame, text="📑  Generate PDF",
            bg=BTN_EXPORT, fg=BTN_FG,
            font=("Segoe UI", 10), relief="flat",
            padx=12, pady=6, cursor="hand2",
            command=self._generate_pdf,
        ).pack(side="left")

    def _build_filter_bar(self) -> None:
        """Search box + type filter + category filter + date range."""
        bar = tk.Frame(self, bg="#eceff1", pady=8)
        bar.grid(row=1, column=0, sticky="ew")

        inner = tk.Frame(bar, bg="#eceff1")
        inner.pack(padx=16, fill="x")

        # Search
        tk.Label(inner, text="Search:", bg="#eceff1",
                 font=("Segoe UI", 9)).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filters())
        ttk.Entry(inner, textvariable=self._search_var, width=18).pack(
            side="left", padx=(4, 12))

        # Type filter
        tk.Label(inner, text="Type:", bg="#eceff1",
                 font=("Segoe UI", 9)).pack(side="left")
        self._type_var = tk.StringVar(value="All")
        ttk.Combobox(
            inner, textvariable=self._type_var,
            values=["All"] + TRANSACTION_TYPES,
            state="readonly", width=10,
        ).pack(side="left", padx=(4, 12))
        self._type_var.trace_add("write", lambda *_: self._apply_filters())

        # Category filter
        tk.Label(inner, text="Category:", bg="#eceff1",
                 font=("Segoe UI", 9)).pack(side="left")
        self._cat_var = tk.StringVar(value="All")
        self._cat_cb = ttk.Combobox(
            inner, textvariable=self._cat_var,
            state="readonly", width=16,
        )
        self._cat_cb.pack(side="left", padx=(4, 12))
        self._cat_var.trace_add("write", lambda *_: self._apply_filters())

        # Date from
        tk.Label(inner, text="From:", bg="#eceff1",
                 font=("Segoe UI", 9)).pack(side="left")
        self._date_from_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self._date_from_var, width=11).pack(
            side="left", padx=(4, 4))

        # Date to
        tk.Label(inner, text="To:", bg="#eceff1",
                 font=("Segoe UI", 9)).pack(side="left", padx=(4, 0))
        self._date_to_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self._date_to_var, width=11).pack(
            side="left", padx=(4, 12))

        # Apply / Clear buttons
        ttk.Button(inner, text="Apply", command=self._apply_filters).pack(
            side="left", padx=(0, 4))
        ttk.Button(inner, text="Clear", command=self._clear_filters).pack(
            side="left")

    def _build_table(self) -> None:
        """Treeview with scrollbars."""
        frame = tk.Frame(self, bg=BG)
        frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(8, 0))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Style
        style = ttk.Style()
        style.configure("Transactions.Treeview",
                        rowheight=28, font=("Segoe UI", 10))
        style.configure("Transactions.Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=HEADER_BG, foreground=HEADER_FG)
        style.map("Transactions.Treeview",
                  background=[("selected", SEL_BG)],
                  foreground=[("selected", "#000000")])

        col_ids = [c[0] for c in COLUMNS]
        self._tree = ttk.Treeview(
            frame,
            columns=col_ids,
            show="headings",
            selectmode="browse",
            style="Transactions.Treeview",
        )

        for col_id, heading, width, anchor in COLUMNS:
            self._tree.heading(col_id, text=heading,
                               command=lambda c=col_id: self._sort_by(c))
            self._tree.column(col_id, width=width, anchor=anchor, minwidth=60)

        self._tree.tag_configure("income",  foreground=INCOME_CLR)
        self._tree.tag_configure("expense", foreground=EXPENSE_CLR)
        self._tree.tag_configure("odd",  background=ROW_ODD)
        self._tree.tag_configure("even", background=ROW_EVEN)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>",         lambda _: self._edit_selected())

        self._sort_col = "date"
        self._sort_asc = False

    def _build_summary_bar(self) -> None:
        """Bottom bar showing income / expense / balance totals."""
        bar = tk.Frame(self, bg=WHITE, pady=8)
        bar.grid(row=3, column=0, sticky="ew")

        inner = tk.Frame(bar, bg=WHITE)
        inner.pack(padx=16)

        def stat(label, color):
            f = tk.Frame(inner, bg=WHITE)
            f.pack(side="left", padx=20)
            tk.Label(f, text=label, bg=WHITE, fg="#607d8b",
                     font=("Segoe UI", 9)).pack()
            var = tk.StringVar(value="£0.00")
            tk.Label(f, textvariable=var, bg=WHITE, fg=color,
                     font=("Segoe UI", 12, "bold")).pack()
            return var

        self._income_var  = stat("Total Income",  INCOME_CLR)
        self._expense_var = stat("Total Expenses", EXPENSE_CLR)
        self._balance_var = stat("Balance",        "#1565c0")
        self._count_var   = stat("Transactions",   "#546e7a")

    # ── Data loading ──────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload categories and transactions from the database."""
        self._all_categories = get_all_categories()
        self._refresh_category_filter()
        self._apply_filters()

    def _refresh_category_filter(self) -> None:
        """Rebuild the category combobox values."""
        names = ["All"] + [c.name for c in self._all_categories]
        self._cat_cb["values"] = names
        if self._cat_var.get() not in names:
            self._cat_var.set("All")

    def _apply_filters(self) -> None:
        """Read filter widgets and reload the table."""
        keyword   = self._search_var.get().strip()
        type_sel  = self._type_var.get()
        cat_sel   = self._cat_var.get()
        date_from = self._date_from_var.get().strip()
        date_to   = self._date_to_var.get().strip()

        type_filter = "" if type_sel == "All" else type_sel

        cat_id = None
        if cat_sel != "All":
            match = next((c for c in self._all_categories if c.name == cat_sel), None)
            if match:
                cat_id = match.id

        try:
            self._transactions = search_transactions(
                keyword=keyword,
                type_filter=type_filter,
                category_id=cat_id,
                date_from=date_from,
                date_to=date_to,
            )
        except TransactionError as exc:
            messagebox.showerror("Filter Error", str(exc))
            return

        self._populate_table()
        self._update_summary()

    def _clear_filters(self) -> None:
        """Reset all filter widgets and reload."""
        self._search_var.set("")
        self._type_var.set("All")
        self._cat_var.set("All")
        self._date_from_var.set("")
        self._date_to_var.set("")
        self._apply_filters()

    # ── Table population ──────────────────────────────────────────────────────

    def _populate_table(self) -> None:
        """Clear and refill the Treeview from self._transactions."""
        self._tree.delete(*self._tree.get_children())
        self._edit_btn.config(state="disabled")
        self._delete_btn.config(state="disabled")

        for i, tx in enumerate(self._transactions):
            tag_type = "income" if tx.type == "Income" else "expense"
            tag_row  = "odd" if i % 2 == 0 else "even"
            self._tree.insert(
                "", "end",
                iid=str(tx.id),
                values=(
                    tx.date,
                    tx.type,
                    tx.category_name,
                    tx.description,
                    f"£{tx.amount:,.2f}",
                    tx.payment_method,
                ),
                tags=(tag_type, tag_row),
            )

    def _update_summary(self) -> None:
        """Recalculate and display totals for the currently visible rows."""
        txs = [t.to_dict() for t in self._transactions]
        income   = calculate_total_income(txs)
        expenses = calculate_total_expenses(txs)
        balance  = income - expenses

        self._income_var.set(f"£{income:,.2f}")
        self._expense_var.set(f"£{expenses:,.2f}")
        self._balance_var.set(f"£{balance:,.2f}")
        self._count_var.set(str(len(self._transactions)))

    # ── Sorting ───────────────────────────────────────────────────────────────

    def _sort_by(self, col: str) -> None:
        """Sort the table by the clicked column header."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key_map = {
            "date":        lambda t: t.date,
            "type":        lambda t: t.type,
            "category":    lambda t: t.category_name,
            "description": lambda t: t.description.lower(),
            "amount":      lambda t: t.amount,
            "payment":     lambda t: t.payment_method,
        }
        self._transactions.sort(
            key=key_map.get(col, lambda t: t.date),
            reverse=not self._sort_asc,
        )
        self._populate_table()

    # ── Selection ─────────────────────────────────────────────────────────────

    def _on_select(self, _event=None) -> None:
        """Enable/disable Edit and Delete buttons based on selection."""
        has_sel = bool(self._tree.selection())
        state   = "normal" if has_sel else "disabled"
        self._edit_btn.config(state=state)
        self._delete_btn.config(state=state)

    def _selected_transaction(self):
        """Return the Transaction object for the selected row, or None."""
        sel = self._tree.selection()
        if not sel:
            return None
        tx_id = int(sel[0])
        return next((t for t in self._transactions if t.id == tx_id), None)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_income(self) -> None:
        TransactionForm(self, on_save=self.refresh, initial_type="Income")

    def _add_expense(self) -> None:
        TransactionForm(self, on_save=self.refresh, initial_type="Expense")

    def _edit_selected(self) -> None:
        tx = self._selected_transaction()
        if tx:
            TransactionForm(self, on_save=self.refresh, transaction=tx)

    def _export_csv(self) -> None:
        try:
            path = export_transactions_csv(self._transactions or None)
            messagebox.showinfo("Export Successful",
                                f"CSV exported to:\n{path}")
        except ExportError as exc:
            messagebox.showerror("Export Failed", str(exc))

    def _generate_pdf(self) -> None:
        try:
            path = generate_pdf_report(self._transactions or None)
            messagebox.showinfo("PDF Generated",
                                f"PDF report saved to:\n{path}")
        except ExportError as exc:
            messagebox.showerror("Export Failed", str(exc))

    def _delete_selected(self) -> None:
        tx = self._selected_transaction()
        if not tx:
            return
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Delete transaction:\n\n"
            f"  {tx.date}  |  {tx.type}  |  £{tx.amount:,.2f}\n"
            f"  {tx.description}\n\n"
            "This cannot be undone.",
            icon="warning",
        )
        if confirmed:
            try:
                delete_transaction(tx.id)
                self.refresh()
            except TransactionError as exc:
                messagebox.showerror("Error", str(exc))
