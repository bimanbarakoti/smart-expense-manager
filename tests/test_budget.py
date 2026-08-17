"""Tests for services/budget_service.py"""

import sqlite3
import pytest

from database.database import init_db
from services.category_service import create_category
from services.transaction_service import create_transaction
from services.budget_service import (
    BudgetError,
    get_all_budgets,
    get_budgets_for_month,
    create_budget,
    update_budget,
    delete_budget,
    get_budget_status,
)
from models.budget import Budget


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def setup(conn):
    """Return conn + expense category id."""
    cat = create_category("Test Food", "Expense", conn)
    return conn, cat.id


# ── create_budget ─────────────────────────────────────────────────────────────

def test_create_budget_success(setup):
    conn, cat_id = setup
    b = create_budget(cat_id, 6, 2024, "500", conn)
    assert isinstance(b, Budget)
    assert b.id is not None
    assert b.amount == 500.0


def test_create_budget_persisted(setup):
    conn, cat_id = setup
    create_budget(cat_id, 6, 2024, "500", conn)
    budgets = get_budgets_for_month(6, 2024, conn)
    assert len(budgets) == 1
    assert budgets[0].amount == 500.0


def test_create_budget_invalid_amount_raises(setup):
    conn, cat_id = setup
    with pytest.raises(BudgetError, match="valid number"):
        create_budget(cat_id, 6, 2024, "abc", conn)


def test_create_budget_zero_amount_raises(setup):
    conn, cat_id = setup
    with pytest.raises(BudgetError, match="greater than zero"):
        create_budget(cat_id, 6, 2024, "0", conn)


def test_create_budget_invalid_month_raises(setup):
    conn, cat_id = setup
    with pytest.raises(BudgetError, match="Month"):
        create_budget(cat_id, 13, 2024, "500", conn)


def test_create_budget_invalid_year_raises(setup):
    conn, cat_id = setup
    with pytest.raises(BudgetError, match="Year"):
        create_budget(cat_id, 6, 1999, "500", conn)


def test_create_budget_duplicate_raises(setup):
    conn, cat_id = setup
    create_budget(cat_id, 6, 2024, "500", conn)
    with pytest.raises(BudgetError, match="already exists"):
        create_budget(cat_id, 6, 2024, "300", conn)


# ── update_budget ─────────────────────────────────────────────────────────────

def test_update_budget_success(setup):
    conn, cat_id = setup
    b = create_budget(cat_id, 6, 2024, "500", conn)
    update_budget(b.id, "800", conn)
    budgets = get_budgets_for_month(6, 2024, conn)
    assert budgets[0].amount == 800.0


def test_update_budget_invalid_amount_raises(setup):
    conn, cat_id = setup
    b = create_budget(cat_id, 6, 2024, "500", conn)
    with pytest.raises(BudgetError):
        update_budget(b.id, "-100", conn)


# ── delete_budget ─────────────────────────────────────────────────────────────

def test_delete_budget_success(setup):
    conn, cat_id = setup
    b = create_budget(cat_id, 6, 2024, "500", conn)
    delete_budget(b.id, conn)
    assert get_budgets_for_month(6, 2024, conn) == []


# ── get_budget_status ─────────────────────────────────────────────────────────

def test_budget_status_under_budget(setup):
    conn, cat_id = setup
    create_budget(cat_id, 5, 2024, "500", conn)
    create_transaction("Expense", "200", cat_id, "2024-05-10", "Groceries", "Cash", conn)
    status = get_budget_status(5, 2024, conn)
    assert len(status) == 1
    s = status[0]
    assert s["spent"] == 200.0
    assert s["remaining"] == 300.0
    assert s["is_over_budget"] is False
    assert s["percentage_used"] == 40.0


def test_budget_status_over_budget(setup):
    conn, cat_id = setup
    create_budget(cat_id, 5, 2024, "100", conn)
    create_transaction("Expense", "150", cat_id, "2024-05-10", "Overspend", "Cash", conn)
    status = get_budget_status(5, 2024, conn)
    s = status[0]
    assert s["is_over_budget"] is True
    assert s["remaining"] == -50.0


def test_budget_status_no_spending(setup):
    conn, cat_id = setup
    create_budget(cat_id, 5, 2024, "500", conn)
    status = get_budget_status(5, 2024, conn)
    s = status[0]
    assert s["spent"] == 0.0
    assert s["remaining"] == 500.0
    assert s["percentage_used"] == 0.0


def test_budget_status_empty_month(setup):
    conn, _ = setup
    assert get_budget_status(12, 2024, conn) == []


def test_budget_status_multiple_categories(conn):
    food = create_category("Food2",      "Expense", conn)
    rent = create_category("Rent",       "Expense", conn)
    create_budget(food.id, 5, 2024, "300", conn)
    create_budget(rent.id, 5, 2024, "1000", conn)
    create_transaction("Expense", "150", food.id, "2024-05-05", "Groceries", "Cash", conn)
    create_transaction("Expense", "900", rent.id, "2024-05-01", "Rent",      "Cash", conn)
    status = get_budget_status(5, 2024, conn)
    assert len(status) == 2
    names = {s["category_name"] for s in status}
    assert "Food2" in names
    assert "Rent" in names
