"""Core business logic calculations.

All functions accept a list of transactions where each item may be:
  - a plain dict  (used by unit tests)
  - a sqlite3.Row (returned directly by the database layer)
  - a Transaction model object (returned by the service layer)

The helper _val() normalises access so the same functions work with all three.
"""

import sqlite3


def _val(t, key: str):
    """Read a field from a dict, sqlite3.Row, or model object."""
    if isinstance(t, dict):
        return t[key]
    if isinstance(t, sqlite3.Row):
        return t[key]
    return getattr(t, key)


# ── Core calculations ─────────────────────────────────────────────────────────

def calculate_total_income(transactions: list) -> float:
    """Sum all Income transactions."""
    return sum(_val(t, "amount") for t in transactions if _val(t, "type") == "Income")


def calculate_total_expenses(transactions: list) -> float:
    """Sum all Expense transactions."""
    return sum(_val(t, "amount") for t in transactions if _val(t, "type") == "Expense")


def calculate_balance(transactions: list) -> float:
    """Calculate net balance (income − expenses)."""
    return calculate_total_income(transactions) - calculate_total_expenses(transactions)


def calculate_budget_remaining(budget_amount: float, spent: float) -> float:
    """Return how much of a budget is still available (may be negative)."""
    return budget_amount - spent


def calculate_category_percentage(category_total: float, grand_total: float) -> float:
    """Return the percentage that category_total represents of grand_total.

    Returns 0.0 when grand_total is zero to avoid division by zero.
    """
    if grand_total == 0:
        return 0.0
    return round((category_total / grand_total) * 100, 2)


def calculate_monthly_summary(transactions: list, year: int, month: int) -> dict:
    """Return income, expenses, and balance for a specific month.

    Args:
        transactions: Full transaction list (any supported type).
        year:         Four-digit year.
        month:        Month number (1–12).

    Returns:
        Dict with keys 'income', 'expenses', 'balance'.
    """
    prefix = f"{year}-{month:02d}"
    monthly = [t for t in transactions if _val(t, "date").startswith(prefix)]
    income   = calculate_total_income(monthly)
    expenses = calculate_total_expenses(monthly)
    return {"income": income, "expenses": expenses, "balance": income - expenses}


def calculate_category_totals(transactions: list) -> dict[str, float]:
    """Return {category_name: total_spent} for all Expense transactions.

    Uses 'category' key for dicts and 'category_name' attribute for model objects.
    """
    totals: dict[str, float] = {}
    for t in transactions:
        if _val(t, "type") != "Expense":
            continue
        # Support both dict key 'category' and model attribute 'category_name'
        if isinstance(t, dict):
            name = t.get("category") or t.get("category_name", "Unknown")
        elif isinstance(t, sqlite3.Row):
            keys = t.keys()
            name = t["category_name"] if "category_name" in keys else t.get("category", "Unknown")
        else:
            name = getattr(t, "category_name", "") or getattr(t, "category", "Unknown")
        totals[name] = totals.get(name, 0.0) + _val(t, "amount")
    return totals


def calculate_all_monthly_summaries(transactions: list, year: int) -> list[dict]:
    """Return a summary dict for every month of a given year.

    Returns a list of 12 dicts (one per month), each with:
        month, income, expenses, balance.
    Months with no transactions have zero values.
    """
    return [
        {"month": m, **calculate_monthly_summary(transactions, year, m)}
        for m in range(1, 13)
    ]


def calculate_budget_status(budget_amount: float, spent: float) -> dict:
    """Return a status summary for a single budget entry.

    Returns:
        Dict with keys: remaining, percentage_used, is_over_budget.
    """
    remaining   = calculate_budget_remaining(budget_amount, spent)
    percentage  = calculate_category_percentage(spent, budget_amount)
    return {
        "remaining":       remaining,
        "percentage_used": percentage,
        "is_over_budget":  spent > budget_amount,
    }
