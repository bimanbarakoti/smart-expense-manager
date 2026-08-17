"""Transaction form — modal dialog for adding and editing transactions."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services.transaction_service import (
    create_transaction, update_transaction, TransactionError)
from services.category_service import get_categories_by_type
from utils.constants import TRANSACTION_TYPES, PAYMENT_METHODS
from models.transaction import Transaction
from gui import theme as T

_W, _H = 480, 440


class TransactionForm(tk.Toplevel):
    """Modal dialog for adding or editing a transaction."""

    def __init__(self, parent, on_save, transaction: Transaction | None = None,
                 initial_type: str = "Expense"):
        super().__init__(parent)
        self._on_save     = on_save
        self._transaction = transaction
        self._edit_mode   = transaction is not None

        self.title("Edit Transaction" if self._edit_mode else "Add Transaction")
        self.geometry(f"{_W}x{_H}")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.transient(parent)

        # Centre over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - _W) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - _H) // 2
        self.geometry(f"+{max(px, 0)}+{max(py, 0)}")

        self._category_map: dict[str, int] = {}
        self._build_ui(initial_type)

        if self._edit_mode:
            self._populate(transaction)

        self.bind("<Return>", lambda _: self._save())
        self.bind("<Escape>", lambda _: self.destroy())

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self, initial_type: str) -> None:
        self.configure(bg=T.PANEL_BG)

        # Coloured title strip
        strip_color = (T.INCOME_CLR if initial_type == "Income"
                       else T.EXPENSE_CLR)
        title_text  = ("Edit Transaction" if self._edit_mode
                       else f"New {initial_type} Transaction")
        tk.Label(self, text=title_text, bg=strip_color, fg=T.BTN_FG,
                 font=T.FONT_H2, pady=13).pack(fill="x")

        form = tk.Frame(self, bg=T.PANEL_BG)
        form.pack(fill="both", expand=True, padx=28, pady=14)
        form.columnconfigure(1, weight=1)

        def lbl(row, text):
            tk.Label(form, text=text, bg=T.PANEL_BG, fg=T.TEXT_HEADER,
                     font=T.FONT_BODY, anchor="w").grid(
                row=row, column=0, sticky="w",
                pady=T.PAD_FORM_Y, padx=(0, 16))

        # Row 0 — Type
        lbl(0, "Type")
        self._type_var = tk.StringVar(value=initial_type)
        type_frame = tk.Frame(form, bg=T.PANEL_BG)
        type_frame.grid(row=0, column=1, sticky="w", pady=T.PAD_FORM_Y)
        for t in TRANSACTION_TYPES:
            tk.Radiobutton(
                type_frame, text=t, variable=self._type_var, value=t,
                bg=T.PANEL_BG, font=T.FONT_BODY,
                activebackground=T.PANEL_BG,
                command=self._on_type_change,
            ).pack(side="left", padx=(0, 16))

        # Row 1 — Amount
        lbl(1, "Amount (£)")
        amt_frame = tk.Frame(form, bg=T.PANEL_BG)
        amt_frame.grid(row=1, column=1, sticky="w", pady=T.PAD_FORM_Y)
        self._amount_var = tk.StringVar()
        amt_entry = ttk.Entry(amt_frame, textvariable=self._amount_var, width=16)
        amt_entry.pack(side="left")
        tk.Label(amt_frame, text="  e.g. 150.00", bg=T.PANEL_BG,
                 fg=T.TEXT_MUTED, font=T.FONT_TINY).pack(side="left")
        amt_entry.focus_set()

        # Row 2 — Category
        lbl(2, "Category")
        self._category_var = tk.StringVar()
        self._category_cb = ttk.Combobox(
            form, textvariable=self._category_var,
            state="readonly", width=28)
        self._category_cb.grid(row=2, column=1, sticky="w",
                               pady=T.PAD_FORM_Y)

        # Row 3 — Date
        lbl(3, "Date")
        date_frame = tk.Frame(form, bg=T.PANEL_BG)
        date_frame.grid(row=3, column=1, sticky="w", pady=T.PAD_FORM_Y)
        self._date_var = tk.StringVar(
            value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self._date_var, width=14).pack(
            side="left")
        tk.Label(date_frame, text="  YYYY-MM-DD", bg=T.PANEL_BG,
                 fg=T.TEXT_MUTED, font=T.FONT_TINY).pack(side="left")

        # Row 4 — Description
        lbl(4, "Description")
        self._desc_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._desc_var, width=32).grid(
            row=4, column=1, sticky="ew", pady=T.PAD_FORM_Y)

        # Row 5 — Payment method
        lbl(5, "Payment Method")
        self._payment_var = tk.StringVar(value=PAYMENT_METHODS[0])
        ttk.Combobox(form, textvariable=self._payment_var,
                     values=PAYMENT_METHODS, state="readonly",
                     width=20).grid(row=5, column=1, sticky="w",
                                    pady=T.PAD_FORM_Y)

        # Required-fields note
        tk.Label(form, text="All fields are required.",
                 bg=T.PANEL_BG, fg=T.TEXT_MUTED,
                 font=T.FONT_TINY).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # Buttons
        btn_frame = tk.Frame(self, bg=T.PANEL_BG)
        btn_frame.pack(fill="x", padx=28, pady=(0, 18))

        T.make_button(btn_frame, "Save", T.BTN_SAVE, self._save,
                      font=T.FONT_H3, padx=24).pack(side="right",
                                                     padx=(8, 0))
        T.make_button(btn_frame, "Cancel", T.BTN_CANCEL, self.destroy,
                      padx=24).pack(side="right")

        self._refresh_categories()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_categories(self) -> None:
        type_ = self._type_var.get()
        cats  = get_categories_by_type(type_)
        self._category_map = {c.name: c.id for c in cats}
        names = list(self._category_map.keys())
        self._category_cb["values"] = names
        if self._category_var.get() not in names:
            self._category_var.set(names[0] if names else "")

    def _on_type_change(self) -> None:
        self._refresh_categories()

    def _populate(self, tx: Transaction) -> None:
        self._type_var.set(tx.type)
        self._refresh_categories()
        self._amount_var.set(str(tx.amount))
        self._category_var.set(tx.category_name)
        self._date_var.set(tx.date)
        self._desc_var.set(tx.description)
        self._payment_var.set(tx.payment_method)

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        type_       = self._type_var.get()
        amount      = self._amount_var.get().strip()
        cat_name    = self._category_var.get()
        date_str    = self._date_var.get().strip()
        description = self._desc_var.get().strip()
        payment     = self._payment_var.get()

        category_id = self._category_map.get(cat_name)
        if category_id is None:
            messagebox.showerror("Missing Field",
                                 "Please select a category.", parent=self)
            return

        try:
            if self._edit_mode:
                update_transaction(
                    self._transaction.id, type_, amount,
                    category_id, date_str, description, payment,
                )
                messagebox.showinfo("Saved",
                                    "Transaction updated successfully.",
                                    parent=self)
            else:
                create_transaction(type_, amount, category_id,
                                   date_str, description, payment)
                messagebox.showinfo("Saved",
                                    "Transaction added successfully.",
                                    parent=self)
            self._on_save()
            self.destroy()

        except TransactionError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
