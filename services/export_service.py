"""Export service — CSV (Pandas) and PDF (ReportLab) exports."""

import os
import re
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

from services.transaction_service import get_all_transactions, search_transactions
from utils.calculations import (
    calculate_total_income, calculate_total_expenses, calculate_all_monthly_summaries,
)
from utils.constants import DATE_FORMAT

EXPORTS_DIR = "exports"


class ExportError(Exception):
    pass


def _ensure_exports_dir() -> str:
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    return EXPORTS_DIR


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-.]", "_", name)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ── CSV Export ────────────────────────────────────────────────────────────────

def export_transactions_csv(transactions=None, filename: str = "") -> str:
    """Export transactions to CSV. Returns the file path."""
    try:
        if transactions is None:
            transactions = get_all_transactions()

        rows = [
            {
                "Date":           t.date,
                "Type":           t.type,
                "Category":       t.category_name,
                "Description":    t.description,
                "Amount (£)":     t.amount,
                "Payment Method": t.payment_method,
            }
            for t in transactions
        ]

        df = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Date", "Type", "Category", "Description", "Amount (£)", "Payment Method"]
        )

        folder = _ensure_exports_dir()
        fname  = filename or _safe_filename(f"transactions_{_timestamp()}.csv")
        path   = os.path.join(folder, fname)

        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    except Exception as exc:
        raise ExportError(f"CSV export failed: {exc}") from exc


# ── PDF Report ────────────────────────────────────────────────────────────────

def generate_pdf_report(transactions=None, filename: str = "") -> str:
    """Generate a PDF financial report. Returns the file path."""
    try:
        if transactions is None:
            transactions = get_all_transactions()

        folder = _ensure_exports_dir()
        fname  = filename or _safe_filename(f"financial_report_{_timestamp()}.pdf")
        path   = os.path.join(folder, fname)

        doc    = SimpleDocTemplate(path, pagesize=A4,
                                   leftMargin=2*cm, rightMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        # ── Styles ────────────────────────────────────────────────────────────
        title_style = ParagraphStyle("ReportTitle", parent=styles["Title"],
                                     fontSize=20, textColor=colors.HexColor("#1e2a38"),
                                     spaceAfter=4)
        h2_style    = ParagraphStyle("H2", parent=styles["Heading2"],
                                     fontSize=13, textColor=colors.HexColor("#1565c0"),
                                     spaceBefore=14, spaceAfter=6)
        normal      = styles["Normal"]

        # ── Header ────────────────────────────────────────────────────────────
        story.append(Paragraph("Smart Expense Manager", title_style))
        story.append(Paragraph("Financial Report", styles["Heading2"]))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
            normal,
        ))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#1e2a38"), spaceAfter=10))

        # ── Summary ───────────────────────────────────────────────────────────
        tx_dicts = [t.to_dict() for t in transactions]
        income   = calculate_total_income(tx_dicts)
        expenses = calculate_total_expenses(tx_dicts)
        balance  = income - expenses

        story.append(Paragraph("Summary", h2_style))

        summary_data = [
            ["Metric", "Amount"],
            ["Total Income",   f"£{income:,.2f}"],
            ["Total Expenses", f"£{expenses:,.2f}"],
            ["Net Balance",    f"£{balance:,.2f}"],
            ["Transactions",   str(len(transactions))],
        ]
        story.append(_make_table(summary_data, col_widths=[9*cm, 6*cm],
                                 header_bg="#1e2a38",
                                 value_colors={"Total Income": "#2e7d32",
                                               "Total Expenses": "#c62828",
                                               "Net Balance": "#1565c0" if balance >= 0 else "#c62828"}))
        story.append(Spacer(1, 0.4*cm))

        # ── Monthly Summary ───────────────────────────────────────────────────
        story.append(Paragraph("Monthly Summary", h2_style))

        # Derive years present in the data, then build per-year monthly summaries
        tx_dicts_all = [t.to_dict() for t in transactions]
        years = sorted({d["date"][:4] for d in tx_dicts_all}) if tx_dicts_all else []
        monthly_rows = []
        for yr in years:
            for row in calculate_all_monthly_summaries(tx_dicts_all, int(yr)):
                if row["income"] or row["expenses"]:
                    monthly_rows.append({
                        "month": f"{yr}-{row['month']:02d}",
                        "income": row["income"],
                        "expenses": row["expenses"],
                    })

        if monthly_rows:
            m_data = [["Month", "Income", "Expenses", "Balance"]]
            for row in sorted(monthly_rows, key=lambda r: r["month"]):
                bal = row["income"] - row["expenses"]
                m_data.append([
                    row["month"],
                    f"£{row['income']:,.2f}",
                    f"£{row['expenses']:,.2f}",
                    f"£{bal:,.2f}",
                ])
            story.append(_make_table(m_data,
                                     col_widths=[4.5*cm, 4*cm, 4*cm, 4*cm],
                                     header_bg="#37474f"))
        else:
            story.append(Paragraph("No transaction data available.", normal))

        story.append(Spacer(1, 0.4*cm))

        # ── Transaction Detail ────────────────────────────────────────────────
        story.append(Paragraph("Transaction Details", h2_style))

        if transactions:
            t_data = [["Date", "Type", "Category", "Description", "Amount (£)", "Payment"]]
            for t in sorted(transactions, key=lambda x: x.date, reverse=True):
                t_data.append([
                    t.date,
                    t.type,
                    t.category_name,
                    t.description[:40] + ("…" if len(t.description) > 40 else ""),
                    f"£{t.amount:,.2f}",
                    t.payment_method,
                ])
            story.append(_make_table(
                t_data,
                col_widths=[2.5*cm, 2*cm, 3*cm, 5*cm, 2.5*cm, 2.5*cm],
                header_bg="#37474f",
                row_colors=("#ffffff", "#f1f3f5"),
                type_col=1,
            ))
        else:
            story.append(Paragraph("No transactions to display.", normal))

        doc.build(story)
        return path

    except Exception as exc:
        raise ExportError(f"PDF generation failed: {exc}") from exc


# ── Table helper ──────────────────────────────────────────────────────────────

def _make_table(data, col_widths=None, header_bg="#1e2a38",
                row_colors=None, value_colors=None, type_col=None):
    """Build a styled ReportLab Table."""
    table = Table(data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING",    (0, 0), (-1, 0), 7),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("TOPPADDING",  (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor(c) for c in (row_colors or ("#ffffff", "#f1f3f5"))]),
    ]

    # Colour specific value rows (summary table)
    if value_colors:
        for row_idx, row in enumerate(data[1:], start=1):
            label = row[0]
            if label in value_colors:
                style_cmds.append(
                    ("TEXTCOLOR", (1, row_idx), (1, row_idx),
                     colors.HexColor(value_colors[label]))
                )
                style_cmds.append(
                    ("FONTNAME", (1, row_idx), (1, row_idx), "Helvetica-Bold")
                )

    # Colour Income/Expense in type column
    if type_col is not None:
        for row_idx, row in enumerate(data[1:], start=1):
            cell = row[type_col]
            clr  = colors.HexColor("#2e7d32" if cell == "Income" else "#c62828")
            style_cmds.append(("TEXTCOLOR", (type_col, row_idx), (type_col, row_idx), clr))

    table.setStyle(TableStyle(style_cmds))
    return table
