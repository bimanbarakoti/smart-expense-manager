"""Budget service — business logic for managing monthly budgets.

This module sits between the GUI and the database layer.
All public functions validate input before touching the database.
"""

import sqlite3

from database.database import (
    get_all_budgets as _db_get_all,
    get_budgets_for_month as _db_get_month,
    insert_budget as _db_insert,
    update_budget as _db_update,
    delete_budget as _db_delete,
    search_transactions as _db_search,
    _DB,
)
from models.budget import Budget
from utils.validators import validate_amount, validate_required
from utils.calculations import calculate_budget_remaining, calculate_category_percentage


class BudgetError(Exception):
    """Raised when a budget operation fails validation or a DB constraint."""


# ── CRUD ──────────────────────────────────────────────────────────────────────

def get_all_budgets(db: _DB = None) -> list[Budget]:
    """Return all budgets as Budget objects."""
    kwargs = {"db": db} if db is not None else {}
    return [Budget.from_row(r) for r in _db_get_all(**kwargs)]


def get_budgets_for_month(month: int, year: int, db: _DB = None) -> list[Budget]:
    """Return all budgets for a given month/year as Budget objects."""
    kwargs = {"db": db} if db is not None else {}
    return [Budget.from_row(r) for r in _db_get_month(month, year, **kwargs)]


def create_budget(
    category_id: int, month: int, year: int, amount: str, db: _DB = None
) -> Budget:
    """Validate and create a new monthly budget.

    Args:
        category_id: ID of an existing Expense category.
        month:       Month number (1–12).
        year:        Four-digit year (>= 2000).
        amount:      Budget amount as a string (validated and converted here).
        db:          Optional DB path or connection.

    Returns:
        The newly created Budget with its assigned id.

    Raises:
        BudgetError: on validation failure or duplicate budget.
    """
    valid, msg = validate_amount(amount)
    if not valid:
        raise BudgetError(msg)

    if not (1 <= month <= 12):
        raise BudgetError("Month must be between 1 and 12.")

    if year < 2000:
        raise BudgetError("Year must be 2000 or later.")

    try:
        kwargs = {"db": db} if db is not None else {}
        new_id = _db_insert(category_id, month, year, float(amount), **kwargs)
        return Budget(
            id=new_id,
            category_id=category_id,
            month=month,
            year=year,
            amount=float(amount),
        )
    except sqlite3.IntegrityError:
        raise BudgetError(
            f"A budget for this category in {month:02d}/{year} already exists."
        )


def update_budget(budget_id: int, amount: str, db: _DB = None) -> None:
    """Validate and update a budget's amount.

    Raises:
        BudgetError: if amount is invalid.
    """
    valid, msg = validate_amount(amount)
    if not valid:
        raise BudgetError(msg)

    kwargs = {"db": db} if db is not None else {}
    _db_update(budget_id, float(amount), **kwargs)


def delete_budget(budget_id: int, db: _DB = None) -> None:
    """Delete a budget by id."""
    kwargs = {"db": db} if db is not None else {}
    _db_delete(budget_id, **kwargs)


# ── Spending analysis ─────────────────────────────────────────────────────────

def get_budget_status(month: int, year: int, db: _DB = None) -> list[dict]:
    """Return budget vs actual spending for every budgeted category in a month.

    Each item in the returned list contains:
        - category_id
        - category_name
        - budget_amount
        - spent
        - remaining
        - percentage_used
        - is_over_budget (bool)

    Args:
        month: Month number (1–12).
        year:  Four-digit year.
        db:    Optional DB path or connection.
    """
    budgets = get_budgets_for_month(month, year, db)
    if not budgets:
        return []

    # Build date range for the month
    date_from = f"{year}-{month:02d}-01"
    date_to   = f"{year}-{month:02d}-31"  # SQLite date comparison handles overflow correctly

    status = []
    for budget in budgets:
        kwargs = {"db": db} if db is not None else {}
        rows = _db_search(
            type_filter="Expense",
            category_id=budget.category_id,
            date_from=date_from,
            date_to=date_to,
            **kwargs,
        )
        spent = sum(r["amount"] for r in rows)
        remaining = calculate_budget_remaining(budget.amount, spent)
        percentage = calculate_category_percentage(spent, budget.amount)

        status.append({
            "category_id":    budget.category_id,
            "category_name":  budget.category_name,
            "budget_amount":  budget.amount,
            "spent":          spent,
            "remaining":      remaining,
            "percentage_used": percentage,
            "is_over_budget": spent > budget.amount,
        })

    return status
