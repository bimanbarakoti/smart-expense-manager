"""Category view — manage income and expense categories."""

import tkinter as tk
from tkinter import ttk, messagebox

from services.category_service import (
    get_all_categories,
    create_category,
    update_category,
    delete_category,
    CategoryError,
)
from gui import theme as T

COLUMNS = [
    ("name", "Category Name", 220, "w"),
    ("type", "Type",          100, "center"),
]


class CategoryView(ttk.Frame):
    """Category management panel."""

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")
        self._categories = []
        self._build_ui()
        self.refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_toolbar()
        self._build_body()

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self, bg=T.PANEL_BG,
                       highlightbackground=T.CARD_BORDER, highlightthickness=1)
        bar.grid(row=0, column=0, sticky="ew")

        left = tk.Frame(bar, bg=T.PANEL_BG)
        left.pack(side="left", padx=T.PAD_PAGE, pady=10)

        T.make_button(left, "＋  Add Income Category",
                      T.INCOME_BTN, self._add_income,
                      font=T.FONT_H3).pack(side="left", padx=(0, 8))

        T.make_button(left, "＋  Add Expense Category",
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

    def _build_body(self) -> None:
        """Two-column layout: treeview (left) + info panel (right)."""
        body = tk.Frame(self, bg=T.CONTENT_BG)
        body.grid(row=1, column=0, sticky="nsew", padx=T.PAD_PAGE,
                  pady=T.PAD_PAGE)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_tree(body)
        self._build_info_panel(body)

    def _build_tree(self, parent) -> None:
        frame = T.panel(parent)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(frame, bg=T.PANEL_BG)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew",
                 padx=T.PAD_CARD, pady=(T.PAD_CARD, 4))
        T.make_section_header(hdr, "All Categories").pack(side="left")
        self._count_lbl = tk.Label(hdr, text="", bg=T.PANEL_BG,
                                   fg=T.TEXT_MUTED, font=T.FONT_SMALL)
        self._count_lbl.pack(side="right")

        tk.Frame(frame, bg=T.CARD_BORDER, height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew")

        T.apply_treeview_style("Cat")
        col_ids = [c[0] for c in COLUMNS]
        self._tree = ttk.Treeview(frame, columns=col_ids, show="headings",
                                  selectmode="browse", style="Cat.Treeview")
        for col_id, heading, width, anchor in COLUMNS:
            self._tree.heading(col_id, text=heading,
                               command=lambda c=col_id: self._sort_by(c))
            self._tree.column(col_id, width=width, anchor=anchor, minwidth=80)

        self._tree.tag_configure("Income",  foreground=T.INCOME_CLR)
        self._tree.tag_configure("Expense", foreground=T.EXPENSE_CLR)
        self._tree.tag_configure("odd",  background=T.ROW_ODD)
        self._tree.tag_configure("even", background=T.ROW_EVEN)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        self._tree.grid(row=2, column=0, sticky="nsew", padx=(T.PAD_CARD, 0),
                        pady=T.PAD_CARD)
        vsb.grid(row=2, column=1, sticky="ns", pady=T.PAD_CARD)
        frame.rowconfigure(2, weight=1)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", lambda _: self._edit_selected())

        self._sort_col = "type"
        self._sort_asc = True

    def _build_info_panel(self, parent) -> None:
        """Right panel showing counts and a usage note."""
        panel = T.panel(parent)
        panel.grid(row=0, column=1, sticky="nsew")

        tk.Frame(panel, bg=T.INCOME_CLR, height=4).pack(fill="x")

        inner = tk.Frame(panel, bg=T.PANEL_BG)
        inner.pack(fill="both", expand=True, padx=T.PAD_CARD, pady=T.PAD_CARD)

        T.make_section_header(inner, "Summary").pack(anchor="w", pady=(4, 8))

        def stat_row(label, var_attr, color):
            f = tk.Frame(inner, bg=T.PANEL_BG)
            f.pack(fill="x", pady=3)
            tk.Label(f, text=label, bg=T.PANEL_BG, fg=T.TEXT_SECONDARY,
                     font=T.FONT_SMALL).pack(side="left")
            var = tk.StringVar(value="0")
            setattr(self, var_attr, var)
            tk.Label(f, textvariable=var, bg=T.PANEL_BG, fg=color,
                     font=T.FONT_H3).pack(side="right")

        stat_row("Income categories:",  "_income_count_var",  T.INCOME_CLR)
        stat_row("Expense categories:", "_expense_count_var", T.EXPENSE_CLR)
        stat_row("Total:",              "_total_count_var",   T.BALANCE_CLR)

        tk.Frame(inner, bg=T.CARD_BORDER, height=1).pack(fill="x", pady=10)

        note = (
            "Categories organise your transactions.\n\n"
            "• Income categories are used for money received.\n"
            "• Expense categories are used for money spent.\n\n"
            "You cannot delete a category that has transactions linked to it."
        )
        tk.Label(inner, text=note, bg=T.PANEL_BG, fg=T.TEXT_SECONDARY,
                 font=T.FONT_SMALL, justify="left", wraplength=160).pack(
            anchor="w")

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._categories = get_all_categories()
        self._populate_tree()
        self._update_counts()

    def _populate_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        self._edit_btn.config(state="disabled")
        self._delete_btn.config(state="disabled")

        cats = sorted(self._categories,
                      key=lambda c: (c.type, c.name),
                      reverse=not self._sort_asc
                      if self._sort_col == "type" else False)

        for i, cat in enumerate(cats):
            tag_row  = "odd" if i % 2 == 0 else "even"
            self._tree.insert("", "end", iid=str(cat.id),
                              values=(cat.name, cat.type),
                              tags=(cat.type, tag_row))

    def _update_counts(self) -> None:
        income  = sum(1 for c in self._categories if c.type == "Income")
        expense = sum(1 for c in self._categories if c.type == "Expense")
        self._income_count_var.set(str(income))
        self._expense_count_var.set(str(expense))
        self._total_count_var.set(str(len(self._categories)))
        total = len(self._categories)
        self._count_lbl.config(
            text=f"{total} categor{'y' if total == 1 else 'ies'}")

    # ── Sorting ───────────────────────────────────────────────────────────────

    def _sort_by(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        key = (lambda c: c.name.lower()) if col == "name" else (lambda c: c.type)
        self._categories.sort(key=key, reverse=not self._sort_asc)
        self._populate_tree()

    # ── Selection ─────────────────────────────────────────────────────────────

    def _on_select(self, _event=None) -> None:
        has = bool(self._tree.selection())
        state = "normal" if has else "disabled"
        self._edit_btn.config(state=state)
        self._delete_btn.config(state=state)

    def _selected_category(self):
        sel = self._tree.selection()
        if not sel:
            return None
        cat_id = int(sel[0])
        return next((c for c in self._categories if c.id == cat_id), None)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_income(self) -> None:
        _CategoryForm(self, on_save=self.refresh, initial_type="Income")

    def _add_expense(self) -> None:
        _CategoryForm(self, on_save=self.refresh, initial_type="Expense")

    def _edit_selected(self) -> None:
        cat = self._selected_category()
        if cat:
            _CategoryForm(self, on_save=self.refresh, category=cat)

    def _delete_selected(self) -> None:
        cat = self._selected_category()
        if not cat:
            return
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Delete the category '{cat.name}' ({cat.type})?\n\n"
            "This will fail if any transactions are linked to it.",
            icon="warning",
        )
        if confirmed:
            try:
                delete_category(cat.id)
                self.refresh()
                messagebox.showinfo("Deleted",
                                    f"Category '{cat.name}' was deleted.")
            except CategoryError as exc:
                messagebox.showerror("Cannot Delete", str(exc))


# ── Category form dialog ──────────────────────────────────────────────────────

class _CategoryForm(tk.Toplevel):
    """Modal dialog for adding or editing a category."""

    def __init__(self, parent, on_save, category=None,
                 initial_type: str = "Expense"):
        super().__init__(parent)
        self._on_save   = on_save
        self._category  = category
        self._edit_mode = category is not None

        title = "Edit Category" if self._edit_mode else "Add Category"
        self.title(title)
        self.geometry("380x260")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.transient(parent)

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 380) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 260) // 2
        self.geometry(f"+{max(px,0)}+{max(py,0)}")

        self._build_ui(initial_type)
        if self._edit_mode:
            self._populate(category)

    def _build_ui(self, initial_type: str) -> None:
        self.configure(bg=T.PANEL_BG)

        # Title strip
        strip_color = (T.INCOME_CLR
                       if (self._category and self._category.type == "Income")
                       or initial_type == "Income"
                       else T.EXPENSE_CLR)
        tk.Label(
            self,
            text="Edit Category" if self._edit_mode else "Add Category",
            bg=strip_color, fg=T.BTN_FG,
            font=T.FONT_H2, pady=12,
        ).pack(fill="x")

        form = tk.Frame(self, bg=T.PANEL_BG)
        form.pack(fill="both", expand=True, padx=24, pady=16)
        form.columnconfigure(1, weight=1)

        def lbl(row, text):
            tk.Label(form, text=text, bg=T.PANEL_BG, fg=T.TEXT_HEADER,
                     font=T.FONT_BODY, anchor="w").grid(
                row=row, column=0, sticky="w",
                pady=T.PAD_FORM_Y, padx=(0, 16))

        # Row 0 — Name
        lbl(0, "Name *")
        self._name_var = tk.StringVar()
        name_entry = ttk.Entry(form, textvariable=self._name_var, width=26)
        name_entry.grid(row=0, column=1, sticky="ew", pady=T.PAD_FORM_Y)
        name_entry.focus_set()

        # Row 1 — Type
        lbl(1, "Type *")
        self._type_var = tk.StringVar(value=initial_type)
        type_frame = tk.Frame(form, bg=T.PANEL_BG)
        type_frame.grid(row=1, column=1, sticky="w", pady=T.PAD_FORM_Y)
        for t in ("Income", "Expense"):
            tk.Radiobutton(
                type_frame, text=t, variable=self._type_var, value=t,
                bg=T.PANEL_BG, font=T.FONT_BODY,
                activebackground=T.PANEL_BG,
            ).pack(side="left", padx=(0, 16))

        # Hint
        tk.Label(form,
                 text="Category names must be unique and up to 50 characters.",
                 bg=T.PANEL_BG, fg=T.TEXT_MUTED,
                 font=T.FONT_TINY, wraplength=260, justify="left").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # Buttons
        btn_frame = tk.Frame(self, bg=T.PANEL_BG)
        btn_frame.pack(fill="x", padx=24, pady=(0, 16))

        T.make_button(btn_frame, "Save", T.BTN_SAVE, self._save,
                      font=T.FONT_H3, padx=20).pack(side="right", padx=(8, 0))
        T.make_button(btn_frame, "Cancel", T.BTN_CANCEL, self.destroy,
                      padx=20).pack(side="right")

        self.bind("<Return>", lambda _: self._save())
        self.bind("<Escape>", lambda _: self.destroy())

    def _populate(self, cat) -> None:
        self._name_var.set(cat.name)
        self._type_var.set(cat.type)

    def _save(self) -> None:
        name  = self._name_var.get().strip()
        type_ = self._type_var.get()

        if not name:
            messagebox.showerror("Validation Error",
                                 "Category name is required.", parent=self)
            return

        try:
            if self._edit_mode:
                update_category(self._category.id, name, type_)
                messagebox.showinfo("Saved",
                                    f"Category '{name}' updated successfully.",
                                    parent=self)
            else:
                create_category(name, type_)
                messagebox.showinfo("Saved",
                                    f"Category '{name}' created successfully.",
                                    parent=self)
            self._on_save()
            self.destroy()
        except CategoryError as exc:
            messagebox.showerror("Error", str(exc), parent=self)
