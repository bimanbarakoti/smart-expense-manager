"""Transaction form — modal dialog for adding and editing transactions."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from services.transaction_service import create_transaction, update_transaction, TransactionError
from services.category_service import get_categories_by_type
from utils.constants import TRANSACTION_TYPES, PAYMENT_METHODS
from models.transaction import Transaction

# ── Colours (match app palette) ───────────────────────────────────────────────
BTN_SAVE   = "#2e7d32"
BTN_CANCEL = "#546e7a"
BTN_FG     = "#ffffff"
INCOME_CLR = "#1b5e20"
EXPENSE_CLR = "#b71c1c"
FIELD_BG   = "#ffffff"
LBL_FG     = "#37474f"


class TransactionForm(tk.Toplevel):
    """Modal dialog for adding or editing a transaction.

    Args:
        parent:      The parent widget (TransactionListView).
        on_save:     Callback invoked with no arguments after a successful save.
        transaction: If provided, the form opens in edit mode pre-filled with
                     the transaction's current values.
        initial_type: 'Income' or 'Expense' — pre-selects the type when adding.
    """

    def __init__(
        self,
        parent,
        on_save,
        transaction: Transaction | None = None,
        initial_type: str = "Expense",
    ):
        super().__init__(parent)
        self._on_save    = on_save
        self._transaction = transaction
        self._edit_mode  = transaction is not None

        self.title("Edit Transaction" if self._edit_mode else "Add Transaction")
        self.geometry("460x420")
        self.resizable(False, False)
        self.grab_set()          # make modal
        self.focus_set()

        # Centre over parent
        self.transient(parent)
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 460) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
        self.geometry(f"+{px}+{py}")

        self._category_map: dict[str, int] = {}   # name → id
        self._build_ui(initial_type)

        if self._edit_mode:
            self._populate(transaction)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self, initial_type: str) -> None:
        """Build all form widgets."""
        self.configure(bg=FIELD_BG)
        pad = {"padx": 20, "pady": 6}

        # ── Title bar strip ──
        title_text = "Edit Transaction" if self._edit_mode else "Add Transaction"
        color = INCOME_CLR if initial_type == "Income" else EXPENSE_CLR
        tk.Label(
            self, text=title_text, bg=color, fg=BTN_FG,
            font=("Segoe UI", 13, "bold"), pady=12,
        ).pack(fill="x")

        form = tk.Frame(self, bg=FIELD_BG)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        form.columnconfigure(1, weight=1)

        def lbl(row, text):
            tk.Label(form, text=text, bg=FIELD_BG, fg=LBL_FG,
                     font=("Segoe UI", 10), anchor="w").grid(
                row=row, column=0, sticky="w", pady=4, padx=(0, 12))

        # Row 0 — Type
        lbl(0, "Type *")
        self._type_var = tk.StringVar(value=initial_type)
        type_frame = tk.Frame(form, bg=FIELD_BG)
        type_frame.grid(row=0, column=1, sticky="w", pady=4)
        for t in TRANSACTION_TYPES:
            tk.Radiobutton(
                type_frame, text=t, variable=self._type_var, value=t,
                bg=FIELD_BG, font=("Segoe UI", 10),
                command=self._on_type_change,
            ).pack(side="left", padx=(0, 12))

        # Row 1 — Amount
        lbl(1, "Amount *")
        self._amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._amount_var, width=20).grid(
            row=1, column=1, sticky="w", pady=4)

        # Row 2 — Category
        lbl(2, "Category *")
        self._category_var = tk.StringVar()
        self._category_cb = ttk.Combobox(
            form, textvariable=self._category_var, state="readonly", width=28)
        self._category_cb.grid(row=2, column=1, sticky="w", pady=4)

        # Row 3 — Date
        lbl(3, "Date *")
        self._date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        date_frame = tk.Frame(form, bg=FIELD_BG)
        date_frame.grid(row=3, column=1, sticky="w", pady=4)
        ttk.Entry(date_frame, textvariable=self._date_var, width=14).pack(side="left")
        tk.Label(date_frame, text="  YYYY-MM-DD", bg=FIELD_BG,
                 fg="#90a4ae", font=("Segoe UI", 9)).pack(side="left")

        # Row 4 — Description
        lbl(4, "Description *")
        self._desc_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._desc_var, width=32).grid(
            row=4, column=1, sticky="ew", pady=4)

        # Row 5 — Payment method
        lbl(5, "Payment Method")
        self._payment_var = tk.StringVar(value=PAYMENT_METHODS[0])
        ttk.Combobox(
            form, textvariable=self._payment_var,
            values=PAYMENT_METHODS, state="readonly", width=18,
        ).grid(row=5, column=1, sticky="w", pady=4)

        # ── Buttons ──
        btn_frame = tk.Frame(self, bg=FIELD_BG)
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))

        tk.Button(
            btn_frame, text="Save", bg=BTN_SAVE, fg=BTN_FG,
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self._save,
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_frame, text="Cancel", bg=BTN_CANCEL, fg=BTN_FG,
            font=("Segoe UI", 10), relief="flat",
            padx=20, pady=6, cursor="hand2",
            command=self.destroy,
        ).pack(side="right")

        # Populate categories for the initial type
        self._refresh_categories()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_categories(self) -> None:
        """Reload the category combobox for the currently selected type."""
        type_ = self._type_var.get()
        cats  = get_categories_by_type(type_)
        self._category_map = {c.name: c.id for c in cats}
        names = list(self._category_map.keys())
        self._category_cb["values"] = names
        # Keep current selection if still valid, else reset
        if self._category_var.get() not in names:
            self._category_var.set(names[0] if names else "")

    def _on_type_change(self) -> None:
        """Called when the user switches Income ↔ Expense."""
        self._refresh_categories()

    def _populate(self, tx: Transaction) -> None:
        """Pre-fill all fields from an existing transaction (edit mode)."""
        self._type_var.set(tx.type)
        self._refresh_categories()
        self._amount_var.set(str(tx.amount))
        self._category_var.set(tx.category_name)
        self._date_var.set(tx.date)
        self._desc_var.set(tx.description)
        self._payment_var.set(tx.payment_method)

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        """Validate fields and call the appropriate service function."""
        type_        = self._type_var.get()
        amount       = self._amount_var.get().strip()
        cat_name     = self._category_var.get()
        date_str     = self._date_var.get().strip()
        description  = self._desc_var.get().strip()
        payment      = self._payment_var.get()

        category_id = self._category_map.get(cat_name)
        if category_id is None:
            messagebox.showerror("Validation Error", "Please select a category.", parent=self)
            return

        try:
            if self._edit_mode:
                update_transaction(
                    self._transaction.id, type_, amount,
                    category_id, date_str, description, payment,
                )
            else:
                create_transaction(type_, amount, category_id, date_str, description, payment)

            self._on_save()
            self.destroy()

        except TransactionError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
