"""Report service — prepares data for financial charts and summaries.

All functions return plain Python structures (lists/dicts) so the GUI
layer only needs to handle rendering, not calculations.
"""

from datetime import date, timedelta

from database.database import search_transactions as _db_search
from services.transaction_service import get_all_transactions
from services.budget_service import get_budget_status
from utils.calculations import (
    calculate_monthly_summary,
    calculate_category_totals,
    calculate_total_expenses,
)

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def get_monthly_income_expense(year: int) -> dict:
    """Return monthly income and expense totals for a full calendar year.

    Args:
        year: Four-digit year.

    Returns:
        Dict with keys:
            - 'labels'   : list of 12 abbreviated month names
            - 'income'   : list of 12 income floats
            - 'expenses' : list of 12 expense floats
            - 'year'     : the requested year
    """
    transactions = get_all_transactions()
    income_vals   = []
    expense_vals  = []

    for month in range(1, 13):
        summary = calculate_monthly_summary(transactions, year, month)
        income_vals.append(summary["income"])
        expense_vals.append(summary["expenses"])

    return {
        "labels":   MONTH_LABELS,
        "income":   income_vals,
        "expenses": expense_vals,
        "year":     year,
    }


def get_category_spending(month: int, year: int) -> dict:
    """Return expense totals grouped by category for a single month.

    Args:
        month: Month number (1–12).
        year:  Four-digit year.

    Returns:
        Dict with keys:
            - 'labels'  : list of category name strings
            - 'values'  : list of corresponding expense floats
            - 'month'   : month number
            - 'year'    : year
        Both lists are empty when there are no expenses for the period.
    """
    date_from = f"{year}-{month:02d}-01"
    date_to   = f"{year}-{month:02d}-31"
    transactions = _db_search(
        type_filter="Expense", date_from=date_from, date_to=date_to
    )
    totals = calculate_category_totals(transactions)

    # Sort descending by amount so the largest slice comes first
    sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    return {"labels": labels, "values": values, "month": month, "year": year}


def get_spending_trend(months_back: int = 6) -> dict:
    """Return total monthly expenses for the last N months (rolling window).

    Args:
        months_back: How many months of history to include (1–24).

    Returns:
        Dict with keys:
            - 'labels'   : list of 'Mon YYYY' strings, oldest first
            - 'expenses' : list of expense floats, oldest first
    """
    months_back = max(1, min(months_back, 24))
    today = date.today()
    labels   = []
    expenses = []

    for i in range(months_back - 1, -1, -1):
        # Step back i months from today
        first_of_month = (today.replace(day=1) - timedelta(days=1))
        # Reliable month arithmetic: subtract i months
        month = today.month - i
        year  = today.year
        while month <= 0:
            month += 12
            year  -= 1

        date_from = f"{year}-{month:02d}-01"
        date_to   = f"{year}-{month:02d}-31"
        txs = _db_search(
            type_filter="Expense", date_from=date_from, date_to=date_to
        )
        total = calculate_total_expenses(txs)
        labels.append(f"{MONTH_LABELS[month - 1]} {year}")
        expenses.append(total)

    return {"labels": labels, "expenses": expenses}


def get_budget_summary(month: int, year: int) -> dict:
    """Return budget vs actual spending for every budgeted category in a month.

    Args:
        month: Month number (1–12).
        year:  Four-digit year.

    Returns:
        Dict with keys:
            - 'labels'   : list of category name strings
            - 'budgeted' : list of budget amount floats
            - 'spent'    : list of actual spent floats
            - 'month'    : month number
            - 'year'     : year
        All lists are empty when no budgets exist for the period.
    """
    status_list = get_budget_status(month, year)

    labels   = [s["category_name"] for s in status_list]
    budgeted = [s["budget_amount"] for s in status_list]
    spent    = [s["spent"]         for s in status_list]

    return {
        "labels":   labels,
        "budgeted": budgeted,
        "spent":    spent,
        "month":    month,
        "year":     year,
    }
