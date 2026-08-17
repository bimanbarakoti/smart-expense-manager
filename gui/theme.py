"""Shared GUI theme — colours, fonts, and spacing used across all views."""

# ── Colours ───────────────────────────────────────────────────────────────────
SIDEBAR_BG        = "#1e2a38"
SIDEBAR_FG        = "#cdd6e0"
SIDEBAR_ACTIVE_BG = "#2e4057"
SIDEBAR_ACTIVE_FG = "#ffffff"
SIDEBAR_HOVER_BG  = "#263545"

CONTENT_BG  = "#f4f6f9"
PANEL_BG    = "#ffffff"
FILTER_BG   = "#eceff1"
CARD_BORDER = "#e0e4ea"

INCOME_CLR  = "#2e7d32"
INCOME_BTN  = "#43a047"
EXPENSE_CLR = "#c62828"
EXPENSE_BTN = "#e53935"
BALANCE_CLR = "#1565c0"
MONTH_CLR   = "#6a1b9a"
EXPORT_CLR  = "#6a1b9a"

OK_CLR   = "#2e7d32"
WARN_CLR = "#e65100"
OVER_CLR = "#c62828"

BTN_EDIT   = "#1565c0"
BTN_DELETE = "#b71c1c"
BTN_SAVE   = "#2e7d32"
BTN_CANCEL = "#546e7a"
BTN_FG     = "#ffffff"

TEXT_PRIMARY   = "#263238"
TEXT_SECONDARY = "#607d8b"
TEXT_MUTED     = "#90a4ae"
TEXT_HEADER    = "#37474f"

ROW_ODD  = "#ffffff"
ROW_EVEN = "#f5f7fa"
SEL_BG   = "#bbdefb"
TREE_HDR_BG = "#37474f"
TREE_HDR_FG = "#ffffff"

PROGRESS_BG = "#e0e0e0"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"

FONT_TITLE   = (FONT_FAMILY, 14, "bold")
FONT_H2      = (FONT_FAMILY, 11, "bold")
FONT_H3      = (FONT_FAMILY, 10, "bold")
FONT_BODY    = (FONT_FAMILY, 10)
FONT_SMALL   = (FONT_FAMILY, 9)
FONT_TINY    = (FONT_FAMILY, 8)
FONT_MONO    = ("Consolas", 10)

FONT_STAT_VALUE = (FONT_FAMILY, 18, "bold")
FONT_STAT_LABEL = (FONT_FAMILY, 9)

# ── Spacing ───────────────────────────────────────────────────────────────────
PAD_PAGE   = 16   # outer page margin
PAD_CARD   = 12   # inside a card
PAD_BTN_X  = 14   # button horizontal padding
PAD_BTN_Y  = 6    # button vertical padding
PAD_FORM_Y = 6    # form row vertical padding

# ── Helpers ───────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk


def make_button(parent, text, color, command, fg=BTN_FG,
                font=None, padx=None, pady=None, **kw):
    """Create a flat, hand-cursor button with consistent styling."""
    return tk.Button(
        parent, text=text,
        bg=color, fg=fg,
        font=font or FONT_BODY,
        relief="flat",
        padx=padx if padx is not None else PAD_BTN_X,
        pady=pady if pady is not None else PAD_BTN_Y,
        cursor="hand2",
        activebackground=color,
        activeforeground=fg,
        command=command,
        **kw,
    )


def make_section_header(parent, text, bg=PANEL_BG):
    """Return a bold section-header Label."""
    return tk.Label(parent, text=text, bg=bg, fg=TEXT_HEADER, font=FONT_H2)


def apply_treeview_style(style_name, row_height=28):
    """Configure a named Treeview style and return the style object."""
    s = ttk.Style()
    s.configure(f"{style_name}.Treeview",
                rowheight=row_height, font=FONT_BODY,
                background=ROW_ODD, fieldbackground=ROW_ODD)
    s.configure(f"{style_name}.Treeview.Heading",
                font=FONT_H3,
                background=TREE_HDR_BG, foreground=TREE_HDR_FG,
                relief="flat")
    s.map(f"{style_name}.Treeview",
          background=[("selected", SEL_BG)],
          foreground=[("selected", TEXT_PRIMARY)])
    return s


def panel(parent, **kw):
    """Return a white card-style Frame with a subtle border."""
    return tk.Frame(parent, bg=PANEL_BG,
                    highlightbackground=CARD_BORDER,
                    highlightthickness=1, **kw)


def separator(parent, padx=12, pady=4):
    """Pack a horizontal separator and return it."""
    sep = ttk.Separator(parent, orient="horizontal")
    sep.pack(fill="x", padx=padx, pady=pady)
    return sep
