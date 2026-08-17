"""Tests for services/report_service.py

report_service functions call get_all_transactions() / _db_search()
which hit the default DB_PATH.  We monkey-patch those internal names so every
test runs against isolated in-memory data and never touches the production DB.
"""

import sqlite3
import pytest

from database.database import init_db, insert_transaction, insert_budget, get_all_categories
from database import database as db_mod
from models.transaction import Transaction
from services import report_service


# ── Helpers ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mem_conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    init_db(c)
    yield c
    c.close()


def _tx_objects(conn):
    """Return all transactions in conn as Transaction objects."""
    return [Transaction.from_row(r) for r in db_mod.get_all_transactions(conn)]


def _db_search_for(conn):
    """Return a _db_search replacement that queries conn."""
    return lambda **kw: db_mod.search_transactions(db=conn, **kw)


def _budget_status(conn, month, year):
    from services.budget_service import get_budget_status
    return get_budget_status(month, year, conn)


# ── get_monthly_income_expense ────────────────────────────────────────────────

class TestGetMonthlyIncomeExpense:

    def test_returns_12_months(self, monkeypatch, mem_conn):
        monkeypatch.setattr(report_service, "get_all_transactions", lambda: _tx_objects(mem_conn))
        result = report_service.get_monthly_income_expense(2024)
        assert len(result["labels"])   == 12
        assert len(result["income"])   == 12
        assert len(result["expenses"]) == 12
        assert result["year"] == 2024

    def test_correct_month_totals(self, monkeypatch, mem_conn):
        cats = get_all_categories(mem_conn)
        sal_id  = next(c["id"] for c in cats if c["name"] == "Salary")
        food_id = next(c["id"] for c in cats if c["name"] == "Food & Dining")
        insert_transaction("Income",  1500.0, sal_id,  "2024-03-10", "March salary", "Bank Transfer", mem_conn)
        insert_transaction("Expense",  200.0, food_id, "2024-03-15", "Groceries",    "Cash",          mem_conn)
        monkeypatch.setattr(report_service, "get_all_transactions", lambda: _tx_objects(mem_conn))
        result = report_service.get_monthly_income_expense(2024)
        assert result["income"][2]   == 1500.0
        assert result["expenses"][2] == 200.0

    def test_empty_db_returns_all_zeros(self, monkeypatch, mem_conn):
        monkeypatch.setattr(report_service, "get_all_transactions", lambda: _tx_objects(mem_conn))
        result = report_service.get_monthly_income_expense(2024)
        assert all(v == 0.0 for v in result["income"])
        assert all(v == 0.0 for v in result["expenses"])

    def test_month_labels_correct(self, monkeypatch, mem_conn):
        monkeypatch.setattr(report_service, "get_all_transactions", lambda: _tx_objects(mem_conn))
        result = report_service.get_monthly_income_expense(2024)
        assert result["labels"][0]  == "Jan"
        assert result["labels"][11] == "Dec"


# ── get_category_spending ─────────────────────────────────────────────────────

class TestGetCategorySpending:

    def _patch(self, monkeypatch, conn):
        monkeypatch.setattr(report_service, "_db_search", _db_search_for(conn))

    def test_returns_sorted_descending(self, monkeypatch, mem_conn):
        cats = get_all_categories(mem_conn)
        food_id  = next(c["id"] for c in cats if c["name"] == "Food & Dining")
        trans_id = next(c["id"] for c in cats if c["name"] == "Transport")
        insert_transaction("Expense", 300.0, food_id,  "2024-05-10", "Groceries", "Cash", mem_conn)
        insert_transaction("Expense",  80.0, trans_id, "2024-05-12", "Bus pass",  "Cash", mem_conn)
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_category_spending(5, 2024)
        assert result["values"][0] >= result["values"][-1]
        assert result["labels"][0] == "Food & Dining"

    def test_empty_month_returns_empty_lists(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_category_spending(1, 2020)
        assert result["labels"] == []
        assert result["values"] == []

    def test_income_excluded(self, monkeypatch, mem_conn):
        cats = get_all_categories(mem_conn)
        sal_id = next(c["id"] for c in cats if c["name"] == "Salary")
        insert_transaction("Income", 2000.0, sal_id, "2024-05-01", "Salary", "Bank Transfer", mem_conn)
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_category_spending(5, 2024)
        assert result["labels"] == []

    def test_metadata_fields(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_category_spending(6, 2024)
        assert result["month"] == 6
        assert result["year"]  == 2024


# ── get_spending_trend ────────────────────────────────────────────────────────

class TestGetSpendingTrend:

    def _patch(self, monkeypatch, conn):
        monkeypatch.setattr(report_service, "_db_search", _db_search_for(conn))

    def test_returns_correct_number_of_months(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        for n in (1, 3, 6, 12):
            result = report_service.get_spending_trend(n)
            assert len(result["labels"])   == n
            assert len(result["expenses"]) == n

    def test_clamps_to_24_max(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_spending_trend(99)
        assert len(result["labels"]) == 24

    def test_clamps_to_1_min(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_spending_trend(0)
        assert len(result["labels"]) == 1

    def test_empty_db_returns_zeros(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_spending_trend(3)
        assert all(v == 0.0 for v in result["expenses"])


# ── get_budget_summary ────────────────────────────────────────────────────────

class TestGetBudgetSummary:

    def _patch(self, monkeypatch, conn):
        monkeypatch.setattr(report_service, "get_budget_status",
                            lambda m, y: _budget_status(conn, m, y))

    def test_empty_returns_empty_lists(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_budget_summary(1, 2020)
        assert result["labels"]   == []
        assert result["budgeted"] == []
        assert result["spent"]    == []

    def test_returns_correct_structure(self, monkeypatch, mem_conn):
        cats = get_all_categories(mem_conn)
        food_id = next(c["id"] for c in cats if c["name"] == "Food & Dining")
        insert_budget(food_id, 5, 2024, 500.0, mem_conn)
        insert_transaction("Expense", 200.0, food_id, "2024-05-10", "Groceries", "Cash", mem_conn)
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_budget_summary(5, 2024)
        assert "Food & Dining" in result["labels"]
        idx = result["labels"].index("Food & Dining")
        assert result["budgeted"][idx] == 500.0
        assert result["spent"][idx]    == 200.0

    def test_metadata_fields(self, monkeypatch, mem_conn):
        self._patch(monkeypatch, mem_conn)
        result = report_service.get_budget_summary(8, 2024)
        assert result["month"] == 8
        assert result["year"]  == 2024
