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
from gui import theme as T
from utils.constants import TRANSACTION_TYPES
from utils.calculations import calculate_total_income, calculate_total_expenses

COLUMNS = [
    ("date",        "Date",          95,  "center"),
    ("type",        "Type",          72,  "center"),
    ("category",    "Category",     130,  "w"),
    ("description", "Description",  210,  "w"),
    ("amount",      "Amount (£)",   105,  "e"),
    ("payment",     "Payment Method", 120, "center"),
]


class TransactionListView(ttk.Frame):
    """Full transaction management panel."""

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")
        self._all_categories = []
        self._transactions   = []
        self._build_ui()
        self.refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.configure(padding=0)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_action_bar()
        self._build_export_bar()
        self._build_filter_bar()
        self._build_table()
        self._build_summary_bar()

    def _build_action_bar(self) -> None:
        """Row 0 — Add / Edit / Delete buttons."""
        bar = tk.Frame(self, bg=T.PANEL_BG,
                       highlightbackground=T.CARD_BORDER,
                       highlightthickness=1)
        bar.grid(row=0, column=0, sticky="ew")

        left = tk.Frame(bar, bg=T.PANEL_BG)
        left.pack(side="left", padx=T.PAD_PAGE, pady=10)

        T.make_button(left, "＋  Add Income",
                      T.INCOME_BTN, self._add_income,
                      font=T.FONT_H3).pack(side="left", padx=(0, 8))
        T.make_button(left, "＋  Add Expense",
                      T.EXPENSE_BTN, self._add_expense,
                      font=T.FONT_H3).pack(side="left")

        right = tk.Frame(bar, bg=T.PANEL_BG)
        right.pack(side="right", padx=T.PAD_PAGE, pady=10)

        self._edit_btn = T.make_button(right, "✏  Edit",
                                       T.BTN_EDIT, self._edit_selected,
                                       state="disabled")
        self._edit_btn.pack(side="left", padx=(0, 8))

        self._delete_btn = T.make_button(right, "🗑  Delete",
                                         T.BTN_DELETE, self._delete_selected,
                                         state="disabled")
        self._delete_btn.pack(side="left")

    def _build_export_bar(self) -> None:
        """Row 1 — Export CSV / Generate PDF buttons with context label."""
        bar = tk.Frame(self, bg=T.FILTER_BG,
                       highlightbackground=T.CARD_BORDER,
                       highlightthickness=1)
        bar.grid(row=1, column=0, sticky="ew")

        inner = tk.Frame(bar, bg=T.FILTER_BG)
        inner.pack(padx=T.PAD_PAGE, pady=6, fill="x")

        tk.Label(inner, text="Export:", bg=T.FILTER_BG,
                 fg=T.TEXT_SECONDARY, font=T.FONT_SMALL).pack(side="left")

        T.make_button(inner, "📄  Export CSV",
                      T.EXPORT_CLR, self._export_csv,
                      font=T.FONT_SMALL, padx=12, pady=4).pack(
            side="left", padx=(8, 6))

        T.make_button(inner, "📑  Generate PDF Report",
                      T.EXPORT_CLR, self._generate_pdf,
                      font=T.FONT_SMALL, padx=12, pady=4).pack(side="left")

        self._export_note = tk.Label(
            inner,
            text="Exports the currently filtered transactions.",
            bg=T.FILTER_BG, fg=T.TEXT_MUTED, font=T.FONT_TINY,
        )
        self._export_note.pack(side="left", padx=(12, 0))

    def _build_filter_bar(self) -> None:
        """Row 2 — Search / filter controls."""
        bar = tk.Frame(self, bg=T.FILTER_BG)
        bar.grid(row=2, column=0, sticky="ew")

        inner = tk.Frame(bar, bg=T.FILTER_BG)
        inner.pack(padx=T.PAD_PAGE, pady=7, fill="x")

        def lbl(text):
            tk.Label(inner, text=text, bg=T.FILTER_BG,
                     fg=T.TEXT_SECONDARY, font=T.FONT_SMALL).pack(
                side="left", padx=(8, 2))

        # Search
        lbl("Search:")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filters())
        ttk.Entry(inner, textvariable=self._search_var, width=18).pack(
            side="left", padx=(0, 8))

        # Type
        lbl("Type:")
        self._type_var = tk.StringVar(value="All")
        ttk.Combobox(inner, textvariable=self._type_var,
                     values=["All"] + TRANSACTION_TYPES,
                     state="readonly", width=10).pack(side="left", padx=(0, 8))
        self._type_var.trace_add("write", lambda *_: self._apply_filters())

        # Category
        lbl("Category:")
        self._cat_var = tk.StringVar(value="All")
        self._cat_cb = ttk.Combobox(inner, textvariable=self._cat_var,
                                    state="readonly", width=16)
        self._cat_cb.pack(side="left", padx=(0, 8))
        self._cat_var.trace_add("write", lambda *_: self._apply_filters())

        # Date range
        lbl("From:")
        self._date_from_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self._date_from_var, width=11).pack(
            side="left", padx=(0, 4))

        lbl("To:")
        self._date_to_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self._date_to_var, width=11).pack(
            side="left", padx=(0, 8))

        ttk.Button(inner, text="Apply",
                   command=self._apply_filters).pack(side="left", padx=(0, 4))
        ttk.Button(inner, text="Clear",
                   command=self._clear_filters).pack(side="left")

        # Live result count
        self._filter_count_var = tk.StringVar(value="")
        tk.Label(inner, textvariable=self._filter_count_var,
                 bg=T.FILTER_BG, fg=T.TEXT_MUTED,
                 font=T.FONT_TINY).pack(side="right", padx=(0, 4))

    def _build_table(self) -> None:
        """Row 3 — Treeview with scrollbars."""
        frame = tk.Frame(self, bg=T.CONTENT_BG)
        frame.grid(row=3, column=0, sticky="nsew",
                   padx=T.PAD_PAGE, pady=(8, 0))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        T.apply_treeview_style("Tx")
        col_ids = [c[0] for c in COLUMNS]
        self._tree = ttk.Treeview(frame, columns=col_ids, show="headings",
                                  selectmode="browse", style="Tx.Treeview")

        for col_id, heading, width, anchor in COLUMNS:
            self._tree.heading(col_id, text=heading,
                               command=lambda c=col_id: self._sort_by(c))
            self._tree.column(col_id, width=width, anchor=anchor, minwidth=60)

        self._tree.tag_configure("income",  foreground=T.INCOME_CLR)
        self._tree.tag_configure("expense", foreground=T.EXPENSE_CLR)
        self._tree.tag_configure("odd",  background=T.ROW_ODD)
        self._tree.tag_configure("even", background=T.ROW_EVEN)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", lambda _: self._edit_selected())

        self._sort_col = "date"
        self._sort_asc = False

    def _build_summary_bar(self) -> None:
        """Row 4 — Totals for the currently visible rows."""
        bar = tk.Frame(self, bg=T.PANEL_BG,
                       highlightbackground=T.CARD_BORDER,
                       highlightthickness=1)
        bar.grid(row=4, column=0, sticky="ew")

        inner = tk.Frame(bar, bg=T.PANEL_BG)
        inner.pack(padx=T.PAD_PAGE, pady=8)

        def stat(label, color, attr):
            f = tk.Frame(inner, bg=T.PANEL_BG)
            f.pack(side="left", padx=20)
            tk.Label(f, text=label, bg=T.PANEL_BG, fg=T.TEXT_SECONDARY,
                     font=T.FONT_SMALL).pack()
            var = tk.StringVar(value="£0.00")
            setattr(self, attr, var)
            tk.Label(f, textvariable=var, bg=T.PANEL_BG, fg=color,
                     font=(T.FONT_FAMILY, 12, "bold")).pack()

        stat("Total Income",   T.INCOME_CLR,  "_income_var")
        stat("Total Expenses", T.EXPENSE_CLR, "_expense_var")
        stat("Balance",        T.BALANCE_CLR, "_balance_var")

        # Transaction count on the right
        self._count_var = tk.StringVar(value="0 transactions")
        tk.Label(inner, textvariable=self._count_var,
                 bg=T.PANEL_BG, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL).pack(side="left", padx=20)

    # ── Data loading ──────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._all_categories = get_all_categories()
        self._refresh_category_filter()
        self._apply_filters()

    def _refresh_category_filter(self) -> None:
        names = ["All"] + [c.name for c in self._all_categories]
        self._cat_cb["values"] = names
        if self._cat_var.get() not in names:
            self._cat_var.set("All")

    def _apply_filters(self) -> None:
        keyword   = self._search_var.get().strip()
        type_sel  = self._type_var.get()
        cat_sel   = self._cat_var.get()
        date_from = self._date_from_var.get().strip()
        date_to   = self._date_to_var.get().strip()

        type_filter = "" if type_sel == "All" else type_sel
        cat_id = None
        if cat_sel != "All":
            match = next((c for c in self._all_categories
                          if c.name == cat_sel), None)
            if match:
                cat_id = match.id

        try:
            self._transactions = search_transactions(
                keyword=keyword, type_filter=type_filter,
                category_id=cat_id, date_from=date_from, date_to=date_to,
            )
        except TransactionError as exc:
            messagebox.showerror("Filter Error",
                                 f"Invalid filter value:\n\n{exc}", parent=self)
            return

        self._populate_table()
        self._update_summary()

    def _clear_filters(self) -> None:
        self._search_var.set("")
        self._type_var.set("All")
        self._cat_var.set("All")
        self._date_from_var.set("")
        self._date_to_var.set("")
        self._apply_filters()

    # ── Table population ──────────────────────────────────────────────────────

    def _populate_table(self) -> None:
        self._tree.delete(*self._tree.get_children())
        self._edit_btn.config(state="disabled")
        self._delete_btn.config(state="disabled")

        for i, tx in enumerate(self._transactions):
            tag_type = "income" if tx.type == "Income" else "expense"
            tag_row  = "odd" if i % 2 == 0 else "even"
            self._tree.insert(
                "", "end", iid=str(tx.id),
                values=(tx.date, tx.type, tx.category_name,
                        tx.description, f"£{tx.amount:,.2f}",
                        tx.payment_method),
                tags=(tag_type, tag_row),
            )

        n = len(self._transactions)
        self._filter_count_var.set(
            f"{n} transaction{'s' if n != 1 else ''} shown")

    def _update_summary(self) -> None:
        txs      = [t.to_dict() for t in self._transactions]
        income   = calculate_total_income(txs)
        expenses = calculate_total_expenses(txs)
        balance  = income - expenses

        self._income_var.set(f"£{income:,.2f}")
        self._expense_var.set(f"£{expenses:,.2f}")
        self._balance_var.set(f"£{balance:,.2f}")
        n = len(self._transactions)
        self._count_var.set(f"{n} transaction{'s' if n != 1 else ''}")

    # ── Sorting ───────────────────────────────────────────────────────────────

    def _sort_by(self, col: str) -> None:
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
        has_sel = bool(self._tree.selection())
        state   = "normal" if has_sel else "disabled"
        self._edit_btn.config(state=state)
        self._delete_btn.config(state=state)

    def _selected_transaction(self):
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
        txs = self._transactions if self._transactions else None
        try:
            path = export_transactions_csv(txs)
            messagebox.showinfo(
                "Export Successful",
                f"CSV file saved to:\n\n{path}",
            )
        except ExportError as exc:
            messagebox.showerror("Export Failed",
                                 f"Could not export CSV:\n\n{exc}")

    def _generate_pdf(self) -> None:
        txs = self._transactions if self._transactions else None
        try:
            path = generate_pdf_report(txs)
            messagebox.showinfo(
                "PDF Generated",
                f"PDF report saved to:\n\n{path}",
            )
        except ExportError as exc:
            messagebox.showerror("Export Failed",
                                 f"Could not generate PDF:\n\n{exc}")

    def _delete_selected(self) -> None:
        tx = self._selected_transaction()
        if not tx:
            return
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this transaction?\n\n"
            f"  Date:    {tx.date}\n"
            f"  Type:    {tx.type}\n"
            f"  Amount:  £{tx.amount:,.2f}\n"
            f"  Details: {tx.description}\n\n"
            "This action cannot be undone.",
            icon="warning",
        )
        if confirmed:
            try:
                delete_transaction(tx.id)
                self.refresh()
            except TransactionError as exc:
                messagebox.showerror("Delete Failed", str(exc))
