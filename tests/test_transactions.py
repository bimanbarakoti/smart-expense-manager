"""Tests for services/transaction_service.py"""

import sqlite3
import pytest

from database.database import init_db
from services.category_service import create_category
from services.transaction_service import (
    TransactionError,
    get_all_transactions,
    get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
    search_transactions,
)
from models.transaction import Transaction


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
    """Return conn + one income category + one expense category."""
    inc = create_category("Test Salary", "Income", conn)
    exp = create_category("Test Food", "Expense", conn)
    return conn, inc.id, exp.id


# ── create_transaction ────────────────────────────────────────────────────────

def test_create_transaction_returns_object(setup):
    conn, inc_id, _ = setup
    tx = create_transaction("Income", "1500", inc_id, "2024-05-01", "May salary", "Bank Transfer", conn)
    assert isinstance(tx, Transaction)
    assert tx.id is not None
    assert tx.amount == 1500.0


def test_create_transaction_persisted(setup):
    conn, inc_id, _ = setup
    tx = create_transaction("Income", "1500", inc_id, "2024-05-01", "May salary", "Cash", conn)
    fetched = get_transaction_by_id(tx.id, conn)
    assert fetched is not None
    assert fetched.amount == 1500.0


def test_create_transaction_invalid_amount_raises(setup):
    conn, inc_id, _ = setup
    with pytest.raises(TransactionError, match="valid number"):
        create_transaction("Income", "abc", inc_id, "2024-05-01", "Bad", "Cash", conn)


def test_create_transaction_zero_amount_raises(setup):
    conn, inc_id, _ = setup
    with pytest.raises(TransactionError, match="greater than zero"):
        create_transaction("Income", "0", inc_id, "2024-05-01", "Zero", "Cash", conn)


def test_create_transaction_invalid_type_raises(setup):
    conn, inc_id, _ = setup
    with pytest.raises(TransactionError):
        create_transaction("Transfer", "100", inc_id, "2024-05-01", "Bad type", "Cash", conn)


def test_create_transaction_invalid_date_raises(setup):
    conn, inc_id, _ = setup
    with pytest.raises(TransactionError):
        create_transaction("Income", "100", inc_id, "not-a-date", "Bad date", "Cash", conn)


def test_create_transaction_empty_description_raises(setup):
    conn, inc_id, _ = setup
    with pytest.raises(TransactionError, match="Description"):
        create_transaction("Income", "100", inc_id, "2024-05-01", "", "Cash", conn)


def test_create_transaction_invalid_payment_method_raises(setup):
    conn, inc_id, _ = setup
    with pytest.raises(TransactionError, match="Payment method"):
        create_transaction("Income", "100", inc_id, "2024-05-01", "Test", "Crypto", conn)


# ── get_all_transactions ──────────────────────────────────────────────────────

def test_get_all_transactions_returns_list(setup):
    conn, inc_id, exp_id = setup
    create_transaction("Income",  "1000", inc_id, "2024-05-01", "Salary",  "Cash", conn)
    create_transaction("Expense",  "200", exp_id, "2024-05-02", "Groceries", "Cash", conn)
    txs = get_all_transactions(conn)
    assert len(txs) == 2
    assert all(isinstance(t, Transaction) for t in txs)


def test_get_all_transactions_newest_first(setup):
    conn, inc_id, _ = setup
    create_transaction("Income", "100", inc_id, "2024-01-01", "First",  "Cash", conn)
    create_transaction("Income", "200", inc_id, "2024-06-01", "Second", "Cash", conn)
    txs = get_all_transactions(conn)
    assert txs[0].date > txs[1].date


# ── update_transaction ────────────────────────────────────────────────────────

def test_update_transaction_success(setup):
    conn, inc_id, _ = setup
    tx = create_transaction("Income", "500", inc_id, "2024-05-01", "Original", "Cash", conn)
    updated = update_transaction(tx.id, "Income", "750", inc_id, "2024-05-15", "Updated", "Bank Transfer", conn)
    assert updated.amount == 750.0
    assert updated.description == "Updated"
    fetched = get_transaction_by_id(tx.id, conn)
    assert fetched.amount == 750.0


def test_update_transaction_invalid_amount_raises(setup):
    conn, inc_id, _ = setup
    tx = create_transaction("Income", "500", inc_id, "2024-05-01", "Test", "Cash", conn)
    with pytest.raises(TransactionError):
        update_transaction(tx.id, "Income", "-50", inc_id, "2024-05-01", "Test", "Cash", conn)


# ── delete_transaction ────────────────────────────────────────────────────────

def test_delete_transaction_success(setup):
    conn, inc_id, _ = setup
    tx = create_transaction("Income", "500", inc_id, "2024-05-01", "Test", "Cash", conn)
    delete_transaction(tx.id, conn)
    assert get_transaction_by_id(tx.id, conn) is None


def test_delete_nonexistent_transaction_raises(conn):
    with pytest.raises(TransactionError, match="not found"):
        delete_transaction(99999, conn)


# ── search_transactions ───────────────────────────────────────────────────────

def test_search_by_keyword(setup):
    conn, inc_id, exp_id = setup
    create_transaction("Income",  "1000", inc_id, "2024-05-01", "Monthly salary", "Cash", conn)
    create_transaction("Expense",  "50",  exp_id, "2024-05-02", "Coffee shop",    "Cash", conn)
    results = search_transactions(keyword="salary", db=conn)
    assert len(results) == 1
    assert "salary" in results[0].description.lower()


def test_search_by_type_filter(setup):
    conn, inc_id, exp_id = setup
    create_transaction("Income",  "1000", inc_id, "2024-05-01", "Salary",    "Cash", conn)
    create_transaction("Expense",  "200", exp_id, "2024-05-02", "Groceries", "Cash", conn)
    income_only = search_transactions(type_filter="Income", db=conn)
    assert all(t.type == "Income" for t in income_only)


def test_search_by_date_range(setup):
    conn, inc_id, _ = setup
    create_transaction("Income", "100", inc_id, "2024-01-15", "Jan", "Cash", conn)
    create_transaction("Income", "200", inc_id, "2024-06-15", "Jun", "Cash", conn)
    results = search_transactions(date_from="2024-06-01", date_to="2024-06-30", db=conn)
    assert len(results) == 1
    assert results[0].description == "Jun"


def test_search_invalid_date_raises(setup):
    conn, *_ = setup
    with pytest.raises(TransactionError, match="Invalid date_from"):
        search_transactions(date_from="bad-date", db=conn)


def test_search_no_results(setup):
    conn, *_ = setup
    assert search_transactions(keyword="ZZZNOMATCH", db=conn) == []


def test_search_invalid_date_to_raises(setup):
    conn, *_ = setup
    with pytest.raises(TransactionError, match="Invalid date_to"):
        search_transactions(date_to="not-a-date", db=conn)


def test_search_by_category_id(setup):
    conn, inc_id, exp_id = setup
    create_transaction("Income",  "500", inc_id, "2024-05-01", "Salary",    "Cash", conn)
    create_transaction("Expense", "100", exp_id, "2024-05-02", "Groceries", "Cash", conn)
    results = search_transactions(category_id=inc_id, db=conn)
    assert all(t.category_id == inc_id for t in results)


# ── get_transaction_by_id ────────────────────────────────────────────────────

def test_get_transaction_by_id_not_found(conn):
    assert get_transaction_by_id(99999, conn) is None


# ── Transaction model ──────────────────────────────────────────────────────────

def test_transaction_to_dict(setup):
    conn, inc_id, _ = setup
    tx = create_transaction("Income", "1000", inc_id, "2024-05-01", "Salary", "Cash", conn)
    d = tx.to_dict()
    assert d["type"]   == "Income"
    assert d["amount"] == 1000.0
    assert d["date"]   == "2024-05-01"
    assert "id" in d


def test_transaction_repr(setup):
    conn, inc_id, _ = setup
    tx = create_transaction("Income", "500", inc_id, "2024-05-01", "Test", "Cash", conn)
    r = repr(tx)
    assert "Income" in r
    assert "500" in r
