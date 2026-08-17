"""Tests for services/category_service.py"""

import sqlite3
import pytest

from database.database import init_db, get_connection
from services.category_service import (
    CategoryError,
    get_all_categories,
    get_category_by_id,
    get_categories_by_type,
    create_category,
    update_category,
    delete_category,
)
from services.transaction_service import create_transaction


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    init_db(c)
    yield c
    c.close()


# ── get_all_categories ────────────────────────────────────────────────────────

def test_get_all_returns_category_objects(conn):
    cats = get_all_categories(conn)
    assert len(cats) >= 13
    assert all(hasattr(c, "name") and hasattr(c, "type") for c in cats)


def test_get_categories_by_type_income(conn):
    income = get_categories_by_type("Income", conn)
    assert all(c.type == "Income" for c in income)
    assert len(income) >= 4


def test_get_categories_by_type_expense(conn):
    expense = get_categories_by_type("Expense", conn)
    assert all(c.type == "Expense" for c in expense)
    assert len(expense) >= 9


# ── create_category ───────────────────────────────────────────────────────────

def test_create_category_success(conn):
    cat = create_category("Bonus", "Income", conn)
    assert cat.id is not None
    assert cat.name == "Bonus"
    assert cat.type == "Income"


def test_create_category_persisted(conn):
    cat = create_category("Bonus", "Income", conn)
    fetched = get_category_by_id(cat.id, conn)
    assert fetched is not None
    assert fetched.name == "Bonus"


def test_create_category_empty_name_raises(conn):
    with pytest.raises(CategoryError, match="required"):
        create_category("", "Expense", conn)


def test_create_category_whitespace_name_raises(conn):
    with pytest.raises(CategoryError):
        create_category("   ", "Expense", conn)


def test_create_category_invalid_type_raises(conn):
    with pytest.raises(CategoryError, match="Type must be"):
        create_category("Misc", "Transfer", conn)


def test_create_category_duplicate_raises(conn):
    create_category("Unique", "Expense", conn)
    with pytest.raises(CategoryError, match="already exists"):
        create_category("Unique", "Expense", conn)


# ── update_category ───────────────────────────────────────────────────────────

def test_update_category_success(conn):
    cat = create_category("Old", "Expense", conn)
    updated = update_category(cat.id, "New", "Income", conn)
    assert updated.name == "New"
    assert updated.type == "Income"
    fetched = get_category_by_id(cat.id, conn)
    assert fetched.name == "New"


def test_update_category_empty_name_raises(conn):
    cat = create_category("Valid", "Expense", conn)
    with pytest.raises(CategoryError):
        update_category(cat.id, "", "Expense", conn)


def test_update_category_invalid_type_raises(conn):
    cat = create_category("Valid", "Expense", conn)
    with pytest.raises(CategoryError):
        update_category(cat.id, "Valid", "BadType", conn)


# ── delete_category ───────────────────────────────────────────────────────────

def test_delete_category_success(conn):
    cat = create_category("Temp", "Expense", conn)
    delete_category(cat.id, conn)
    assert get_category_by_id(cat.id, conn) is None


def test_delete_category_with_transactions_raises(conn):
    cat = create_category("Used", "Expense", conn)
    create_transaction("Expense", "50", cat.id, "2024-01-01", "Test", "Cash", conn)
    with pytest.raises(CategoryError, match="transactions are linked"):
        delete_category(cat.id, conn)


# ── get_category_by_id ───────────────────────────────────────────────────────────

def test_get_category_by_id_not_found(conn):
    assert get_category_by_id(99999, conn) is None


# ── Category model ──────────────────────────────────────────────────────────────

def test_category_to_dict(conn):
    cat = create_category("Rent", "Expense", conn)
    d = cat.to_dict()
    assert d["name"] == "Rent"
    assert d["type"] == "Expense"
    assert "id" in d


def test_category_repr(conn):
    cat = create_category("Rent", "Expense", conn)
    assert "Rent" in repr(cat)
    assert "Expense" in repr(cat)
