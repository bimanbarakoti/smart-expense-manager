"""Tests for database/database.py — all run against a shared in-memory Connection."""

import sqlite3
import pytest

from database.database import (
    get_connection,
    init_db,
    get_all_categories,
    get_category_by_id,
    insert_category,
    update_category,
    delete_category,
    get_all_transactions,
    get_transaction_by_id,
    insert_transaction,
    update_transaction,
    delete_transaction,
    search_transactions,
    get_all_budgets,
    get_budgets_for_month,
    insert_budget,
    update_budget,
    delete_budget,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def conn():
    """Fresh in-memory Connection, initialised with schema + default data."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def conn_with_data(conn):
    """Connection pre-loaded with one extra category, one transaction, one budget."""
    cat_id = insert_category("Test Income", "Income", conn)
    tx_id  = insert_transaction("Income", 500.0, cat_id, "2024-03-01", "Test pay", "Cash", conn)
    bud_id = insert_budget(cat_id, 3, 2024, 1000.0, conn)
    return conn, cat_id, tx_id, bud_id


# ── init_db ───────────────────────────────────────────────────────────────────

def test_init_creates_tables(conn):
    tables = {
        row[0] for row in
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"categories", "transactions", "budgets"}.issubset(tables)


def test_init_seeds_default_categories(conn):
    names = [c["name"] for c in get_all_categories(conn)]
    assert "Salary" in names
    assert "Food & Dining" in names


def test_init_is_idempotent(conn):
    """Calling init_db twice must not raise or duplicate categories."""
    init_db(conn)
    salary_rows = [c for c in get_all_categories(conn) if c["name"] == "Salary"]
    assert len(salary_rows) == 1


# ── Category CRUD ─────────────────────────────────────────────────────────────

def test_insert_and_get_category(conn):
    new_id = insert_category("Bonus", "Income", conn)
    cat = get_category_by_id(new_id, conn)
    assert cat["name"] == "Bonus"
    assert cat["type"] == "Income"


def test_get_all_categories_returns_list(conn):
    cats = get_all_categories(conn)
    assert isinstance(cats, list)
    assert len(cats) >= 13   # 13 defaults seeded


def test_update_category(conn):
    new_id = insert_category("OldName", "Expense", conn)
    update_category(new_id, "NewName", "Expense", conn)
    assert get_category_by_id(new_id, conn)["name"] == "NewName"


def test_delete_category(conn):
    new_id = insert_category("Temporary", "Expense", conn)
    delete_category(new_id, conn)
    assert get_category_by_id(new_id, conn) is None


def test_duplicate_category_name_raises(conn):
    insert_category("Unique", "Expense", conn)
    with pytest.raises(sqlite3.IntegrityError):
        insert_category("Unique", "Expense", conn)


def test_invalid_category_type_raises(conn):
    with pytest.raises(sqlite3.IntegrityError):
        insert_category("Bad", "Transfer", conn)


def test_delete_category_with_transaction_raises(conn_with_data):
    conn, cat_id, tx_id, _ = conn_with_data
    with pytest.raises(sqlite3.IntegrityError):
        delete_category(cat_id, conn)


# ── Transaction CRUD ──────────────────────────────────────────────────────────

def test_insert_and_get_transaction(conn_with_data):
    conn, cat_id, tx_id, _ = conn_with_data
    tx = get_transaction_by_id(tx_id, conn)
    assert tx["amount"] == 500.0
    assert tx["type"] == "Income"
    assert tx["category_name"] == "Test Income"


def test_get_all_transactions(conn_with_data):
    conn, *_ = conn_with_data
    assert len(get_all_transactions(conn)) >= 1


def test_update_transaction(conn_with_data):
    conn, cat_id, tx_id, _ = conn_with_data
    update_transaction(tx_id, "Income", 750.0, cat_id, "2024-03-15", "Updated", "Bank Transfer", conn)
    tx = get_transaction_by_id(tx_id, conn)
    assert tx["amount"] == 750.0
    assert tx["description"] == "Updated"
    assert tx["payment_method"] == "Bank Transfer"


def test_delete_transaction(conn_with_data):
    conn, _, tx_id, _ = conn_with_data
    delete_transaction(tx_id, conn)
    assert get_transaction_by_id(tx_id, conn) is None


def test_transaction_negative_amount_raises(conn):
    cat_id = get_all_categories(conn)[0]["id"]
    with pytest.raises(sqlite3.IntegrityError):
        insert_transaction("Expense", -50.0, cat_id, "2024-01-01", "Bad", "Cash", conn)


def test_transaction_invalid_type_raises(conn):
    cat_id = get_all_categories(conn)[0]["id"]
    with pytest.raises(sqlite3.IntegrityError):
        insert_transaction("Transfer", 100.0, cat_id, "2024-01-01", "Bad type", "Cash", conn)


def test_transaction_invalid_category_raises(conn):
    with pytest.raises(sqlite3.IntegrityError):
        insert_transaction("Expense", 50.0, 99999, "2024-01-01", "No cat", "Cash", conn)


# ── Search / Filter ───────────────────────────────────────────────────────────

def test_search_by_keyword(conn_with_data):
    conn, *_ = conn_with_data
    results = search_transactions(keyword="Test", db=conn)
    assert len(results) >= 1
    assert all("Test" in r["description"] for r in results)


def test_search_no_match(conn_with_data):
    conn, *_ = conn_with_data
    assert search_transactions(keyword="ZZZNOMATCH", db=conn) == []


def test_filter_by_type(conn_with_data):
    conn, cat_id, _, _ = conn_with_data
    insert_transaction("Expense", 100.0, cat_id, "2024-03-05", "Expense item", "Cash", conn)
    assert all(r["type"] == "Income"  for r in search_transactions(type_filter="Income",  db=conn))
    assert all(r["type"] == "Expense" for r in search_transactions(type_filter="Expense", db=conn))


def test_filter_by_category(conn_with_data):
    conn, cat_id, _, _ = conn_with_data
    results = search_transactions(category_id=cat_id, db=conn)
    assert all(r["category_id"] == cat_id for r in results)


def test_filter_by_date_range(conn_with_data):
    conn, cat_id, _, _ = conn_with_data
    insert_transaction("Income", 200.0, cat_id, "2024-01-10", "Jan tx", "Cash", conn)
    results = search_transactions(date_from="2024-03-01", date_to="2024-03-31", db=conn)
    assert all("2024-03" in r["date"] for r in results)


# ── Budget CRUD ───────────────────────────────────────────────────────────────

def test_insert_and_get_budget(conn_with_data):
    conn, _, _, _ = conn_with_data
    budgets = get_budgets_for_month(3, 2024, conn)
    assert len(budgets) == 1
    assert budgets[0]["amount"] == 1000.0
    assert budgets[0]["category_name"] == "Test Income"


def test_get_all_budgets(conn_with_data):
    conn, *_ = conn_with_data
    assert len(get_all_budgets(conn)) >= 1


def test_update_budget(conn_with_data):
    conn, _, _, bud_id = conn_with_data
    update_budget(bud_id, 1500.0, conn)
    assert get_budgets_for_month(3, 2024, conn)[0]["amount"] == 1500.0


def test_delete_budget(conn_with_data):
    conn, _, _, bud_id = conn_with_data
    delete_budget(bud_id, conn)
    assert get_budgets_for_month(3, 2024, conn) == []


def test_duplicate_budget_raises(conn_with_data):
    conn, cat_id, _, _ = conn_with_data
    with pytest.raises(sqlite3.IntegrityError):
        insert_budget(cat_id, 3, 2024, 500.0, conn)   # same category/month/year


def test_budget_invalid_month_raises(conn):
    cat_id = get_all_categories(conn)[0]["id"]
    with pytest.raises(sqlite3.IntegrityError):
        insert_budget(cat_id, 13, 2024, 100.0, conn)


def test_budget_deleted_when_category_deleted(conn):
    """Budget ON DELETE CASCADE — deleting a category removes its budgets."""
    cat_id = insert_category("Cascade Cat", "Expense", conn)
    insert_budget(cat_id, 1, 2024, 200.0, conn)
    delete_category(cat_id, conn)   # no transactions reference it
    assert get_budgets_for_month(1, 2024, conn) == []
