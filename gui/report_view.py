"""Report view — four Matplotlib charts embedded in a Tkinter Notebook."""

import tkinter as tk
from tkinter import ttk
from datetime import date

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.report_service import (
    get_monthly_income_expense,
    get_category_spending,
    get_spending_trend,
    get_budget_summary,
)

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#f4f6f9"
WHITE       = "#ffffff"
CARD_BORDER = "#e0e4ea"
INCOME_CLR  = "#43a047"
EXPENSE_CLR = "#e53935"
BUDGET_CLR  = "#1565c0"
SPENT_CLR   = "#e53935"
TREND_CLR   = "#7b1fa2"
HEADER_FG   = "#37474f"

# Matplotlib figure background matches the app palette
FIG_BG      = "#f4f6f9"
AXES_BG     = "#ffffff"

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Pie chart colour cycle
PIE_COLORS = [
    "#1565c0", "#43a047", "#e53935", "#fb8c00", "#8e24aa",
    "#00838f", "#6d4c41", "#546e7a", "#c0ca33", "#f06292",
]


class ReportView(ttk.Frame):
    """Reports panel with four chart tabs."""

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")
        today = date.today()
        self._year  = today.year
        self._month = today.month
        self._trend_months = 6
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_notebook()

    def _build_toolbar(self) -> None:
        """Controls bar: year spinner, month selector, trend window, Generate button."""
        bar = tk.Frame(self, bg=WHITE, pady=8,
                       highlightbackground=CARD_BORDER, highlightthickness=1)
        bar.grid(row=0, column=0, sticky="ew")

        inner = tk.Frame(bar, bg=WHITE)
        inner.pack(padx=16, fill="x")

        def lbl(text):
            tk.Label(inner, text=text, bg=WHITE, fg=HEADER_FG,
                     font=("Segoe UI", 9)).pack(side="left", padx=(8, 2))

        # Year
        lbl("Year:")
        self._year_var = tk.IntVar(value=self._year)
        ttk.Spinbox(inner, from_=2000, to=2100,
                    textvariable=self._year_var, width=6).pack(side="left")

        # Month (for category + budget charts)
        lbl("Month:")
        self._month_var = tk.StringVar(value=MONTH_NAMES[self._month])
        ttk.Combobox(
            inner, textvariable=self._month_var,
            values=MONTH_NAMES[1:], state="readonly", width=11,
        ).pack(side="left")

        # Trend window
        lbl("Trend (months):")
        self._trend_var = tk.IntVar(value=self._trend_months)
        ttk.Spinbox(inner, from_=2, to=24,
                    textvariable=self._trend_var, width=4).pack(side="left")

        # Generate button
        tk.Button(
            inner, text="▶  Generate",
            bg="#1565c0", fg=WHITE,
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=14, pady=4, cursor="hand2",
            command=self.refresh,
        ).pack(side="left", padx=(16, 0))

    def _build_notebook(self) -> None:
        """Four tabs, one per chart type."""
        self._nb = ttk.Notebook(self)
        self._nb.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        # Each tab is a plain Frame; the canvas is placed inside it
        self._tab_income   = tk.Frame(self._nb, bg=BG)
        self._tab_category = tk.Frame(self._nb, bg=BG)
        self._tab_trend    = tk.Frame(self._nb, bg=BG)
        self._tab_budget   = tk.Frame(self._nb, bg=BG)

        for tab, title in [
            (self._tab_income,   "📊  Income vs Expenses"),
            (self._tab_category, "🥧  Category Spending"),
            (self._tab_trend,    "📈  Spending Trend"),
            (self._tab_budget,   "🎯  Budget Summary"),
        ]:
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(0, weight=1)
            self._nb.add(tab, text=title)

        # Canvas placeholders — replaced on each refresh
        self._canvas_income   = None
        self._canvas_category = None
        self._canvas_trend    = None
        self._canvas_budget   = None

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Read controls, fetch data from the service layer, redraw all charts."""
        try:
            self._year  = int(self._year_var.get())
        except (ValueError, tk.TclError):
            self._year = date.today().year

        month_name = self._month_var.get()
        self._month = MONTH_NAMES.index(month_name) if month_name in MONTH_NAMES else date.today().month

        try:
            self._trend_months = int(self._trend_var.get())
        except (ValueError, tk.TclError):
            self._trend_months = 6

        self._draw_income_chart()
        self._draw_category_chart()
        self._draw_trend_chart()
        self._draw_budget_chart()

    # ── Chart helpers ─────────────────────────────────────────────────────────

    def _embed_figure(self, fig, tab: tk.Frame, attr: str) -> None:
        """Destroy the old canvas for a tab and embed the new figure."""
        old = getattr(self, attr)
        if old is not None:
            old.get_tk_widget().destroy()
            plt.close(old.figure)

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        setattr(self, attr, canvas)

    def _empty_figure(self, message: str):
        """Return a Matplotlib figure showing a centred 'no data' message."""
        fig, ax = plt.subplots(figsize=(7, 4), facecolor=FIG_BG)
        ax.set_facecolor(AXES_BG)
        ax.text(0.5, 0.5, message,
                ha="center", va="center",
                fontsize=12, color="#90a4ae",
                transform=ax.transAxes)
        ax.axis("off")
        fig.tight_layout()
        return fig

    def _style_axes(self, ax) -> None:
        """Apply consistent styling to a chart axes."""
        ax.set_facecolor(AXES_BG)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#cfd8dc")
        ax.spines["bottom"].set_color("#cfd8dc")
        ax.tick_params(colors="#607d8b", labelsize=8)
        ax.yaxis.grid(True, color="#eceff1", linewidth=0.8)
        ax.set_axisbelow(True)

    # ── Chart 1 — Monthly Income vs Expenses ─────────────────────────────────

    def _draw_income_chart(self) -> None:
        data = get_monthly_income_expense(self._year)

        has_data = any(v > 0 for v in data["income"] + data["expenses"])
        if not has_data:
            fig = self._empty_figure(
                f"No transactions found for {self._year}.\nAdd some transactions to see this chart.")
            self._embed_figure(fig, self._tab_income, "_canvas_income")
            return

        import numpy as np
        x     = np.arange(12)
        width = 0.38

        fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=FIG_BG)
        self._style_axes(ax)

        bars_i = ax.bar(x - width / 2, data["income"],   width,
                        label="Income",   color=INCOME_CLR,  alpha=0.85)
        bars_e = ax.bar(x + width / 2, data["expenses"], width,
                        label="Expenses", color=EXPENSE_CLR, alpha=0.85)

        ax.set_title(f"Monthly Income vs Expenses — {self._year}",
                     fontsize=11, color=HEADER_FG, pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(data["labels"])
        ax.set_ylabel("Amount (£)", fontsize=9, color="#607d8b")
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
        ax.legend(fontsize=9)

        # Value labels on bars > 0
        for bar in list(bars_i) + list(bars_e):
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + max(data["income"] + data["expenses"]) * 0.01,
                        f"£{h:,.0f}", ha="center", va="bottom",
                        fontsize=6.5, color="#37474f")

        fig.tight_layout()
        self._embed_figure(fig, self._tab_income, "_canvas_income")

    # ── Chart 2 — Category Spending Pie ──────────────────────────────────────

    def _draw_category_chart(self) -> None:
        data = get_category_spending(self._month, self._year)

        if not data["values"]:
            fig = self._empty_figure(
                f"No expenses found for {MONTH_NAMES[self._month]} {self._year}.\n"
                "Add expense transactions to see this chart.")
            self._embed_figure(fig, self._tab_category, "_canvas_category")
            return

        fig, (ax_pie, ax_tbl) = plt.subplots(
            1, 2, figsize=(8, 4.2), facecolor=FIG_BG,
            gridspec_kw={"width_ratios": [1.4, 1]},
        )

        colors = (PIE_COLORS * 4)[:len(data["labels"])]
        wedges, texts, autotexts = ax_pie.pie(
            data["values"],
            labels=None,
            colors=colors,
            autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
            startangle=140,
            pctdistance=0.78,
            wedgeprops={"linewidth": 0.8, "edgecolor": WHITE},
        )
        for at in autotexts:
            at.set_fontsize(7.5)
            at.set_color(WHITE)

        ax_pie.set_title(
            f"Category Spending — {MONTH_NAMES[self._month]} {self._year}",
            fontsize=11, color=HEADER_FG, pad=10)

        # Legend / table on the right axes
        ax_tbl.axis("off")
        total = sum(data["values"])
        rows  = []
        for label, val, color in zip(data["labels"], data["values"], colors):
            pct = val / total * 100 if total else 0
            rows.append([f"  {label}", f"£{val:,.2f}", f"{pct:.1f}%"])

        if rows:
            tbl = ax_tbl.table(
                cellText=rows,
                colLabels=["Category", "Amount", "%"],
                cellLoc="left",
                loc="center",
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(8)
            tbl.scale(1, 1.4)
            for (r, c), cell in tbl.get_celld().items():
                cell.set_edgecolor("#eceff1")
                if r == 0:
                    cell.set_facecolor("#eceff1")
                    cell.set_text_props(fontweight="bold", color=HEADER_FG)
                else:
                    cell.set_facecolor(WHITE)
                    if c == 0:
                        cell.set_facecolor(colors[r - 1] + "22")

        fig.tight_layout()
        self._embed_figure(fig, self._tab_category, "_canvas_category")

    # ── Chart 3 — Spending Trend Line ─────────────────────────────────────────

    def _draw_trend_chart(self) -> None:
        data = get_spending_trend(self._trend_months)

        has_data = any(v > 0 for v in data["expenses"])
        if not has_data:
            fig = self._empty_figure(
                f"No expense data found for the last {self._trend_months} months.\n"
                "Add expense transactions to see this chart.")
            self._embed_figure(fig, self._tab_trend, "_canvas_trend")
            return

        fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=FIG_BG)
        self._style_axes(ax)

        x = range(len(data["labels"]))
        ax.plot(x, data["expenses"], color=TREND_CLR,
                linewidth=2, marker="o", markersize=5, zorder=3)
        ax.fill_between(x, data["expenses"],
                        color=TREND_CLR, alpha=0.08)

        # Annotate each point
        for xi, val in zip(x, data["expenses"]):
            if val > 0:
                ax.annotate(f"£{val:,.0f}",
                            xy=(xi, val),
                            xytext=(0, 8), textcoords="offset points",
                            ha="center", fontsize=7.5, color=TREND_CLR)

        ax.set_title(f"Spending Trend — Last {self._trend_months} Months",
                     fontsize=11, color=HEADER_FG, pad=10)
        ax.set_xticks(list(x))
        ax.set_xticklabels(data["labels"], rotation=30, ha="right")
        ax.set_ylabel("Total Expenses (£)", fontsize=9, color="#607d8b")
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"£{v:,.0f}"))

        fig.tight_layout()
        self._embed_figure(fig, self._tab_trend, "_canvas_trend")

    # ── Chart 4 — Budget Summary Grouped Bar ─────────────────────────────────

    def _draw_budget_chart(self) -> None:
        data = get_budget_summary(self._month, self._year)

        if not data["labels"]:
            fig = self._empty_figure(
                f"No budgets set for {MONTH_NAMES[self._month]} {self._year}.\n"
                "Add budgets in the Budgets view to see this chart.")
            self._embed_figure(fig, self._tab_budget, "_canvas_budget")
            return

        import numpy as np
        x     = np.arange(len(data["labels"]))
        width = 0.38

        fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=FIG_BG)
        self._style_axes(ax)

        bars_b = ax.bar(x - width / 2, data["budgeted"], width,
                        label="Budgeted", color=BUDGET_CLR, alpha=0.8)
        bars_s = ax.bar(x + width / 2, data["spent"],    width,
                        label="Spent",    color=SPENT_CLR,  alpha=0.8)

        # Colour over-budget spent bars differently
        for bar, budgeted, spent in zip(bars_s, data["budgeted"], data["spent"]):
            if spent > budgeted:
                bar.set_color("#b71c1c")
                bar.set_alpha(1.0)

        ax.set_title(
            f"Budget vs Actual — {MONTH_NAMES[self._month]} {self._year}",
            fontsize=11, color=HEADER_FG, pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(data["labels"], rotation=20, ha="right", fontsize=8)
        ax.set_ylabel("Amount (£)", fontsize=9, color="#607d8b")
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
        ax.legend(fontsize=9)

        # Value labels
        max_val = max(data["budgeted"] + data["spent"]) if data["budgeted"] else 1
        for bar in list(bars_b) + list(bars_s):
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        h + max_val * 0.01,
                        f"£{h:,.0f}",
                        ha="center", va="bottom",
                        fontsize=6.5, color="#37474f")

        fig.tight_layout()
        self._embed_figure(fig, self._tab_budget, "_canvas_budget")
