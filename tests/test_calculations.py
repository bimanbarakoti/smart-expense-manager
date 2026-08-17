"""Tests for utils/calculations.py"""

import sqlite3
import pytest
from utils.calculations import (
    calculate_total_income,
    calculate_total_expenses,
    calculate_balance,
    calculate_budget_remaining,
    calculate_category_percentage,
    calculate_monthly_summary,
    calculate_category_totals,
    calculate_all_monthly_summaries,
    calculate_budget_status,
    _val,
)

SAMPLE = [
    {"type": "Income",  "amount": 3000.0, "category": "Salary",       "date": "2024-01-15"},
    {"type": "Income",  "amount":  500.0, "category": "Freelance",     "date": "2024-01-20"},
    {"type": "Expense", "amount":  800.0, "category": "Housing",       "date": "2024-01-05"},
    {"type": "Expense", "amount":  200.0, "category": "Food & Dining", "date": "2024-01-10"},
    {"type": "Expense", "amount":  150.0, "category": "Transport",     "date": "2024-02-03"},
]


def test_total_income():
    assert calculate_total_income(SAMPLE) == 3500.0


def test_total_expenses():
    assert calculate_total_expenses(SAMPLE) == 1150.0


def test_balance():
    assert calculate_balance(SAMPLE) == 2350.0


def test_balance_empty():
    assert calculate_balance([]) == 0.0


def test_budget_remaining():
    assert calculate_budget_remaining(1000.0, 600.0) == 400.0


def test_budget_remaining_exceeded():
    assert calculate_budget_remaining(500.0, 700.0) == -200.0


def test_category_percentage():
    assert calculate_category_percentage(200.0, 1000.0) == 20.0


def test_category_percentage_zero_total():
    assert calculate_category_percentage(100.0, 0) == 0.0


def test_monthly_summary_january():
    result = calculate_monthly_summary(SAMPLE, 2024, 1)
    assert result["income"] == 3500.0
    assert result["expenses"] == 1000.0
    assert result["balance"] == 2500.0


def test_monthly_summary_february():
    result = calculate_monthly_summary(SAMPLE, 2024, 2)
    assert result["income"] == 0.0
    assert result["expenses"] == 150.0


def test_monthly_summary_empty_month():
    result = calculate_monthly_summary(SAMPLE, 2024, 6)
    assert result == {"income": 0.0, "expenses": 0.0, "balance": 0.0}


def test_category_totals():
    totals = calculate_category_totals(SAMPLE)
    assert totals["Housing"] == 800.0
    assert totals["Food & Dining"] == 200.0
    assert totals["Transport"] == 150.0
    assert "Salary" not in totals  # income excluded


def test_category_totals_empty():
    assert calculate_category_totals([]) == {}


# ── calculate_all_monthly_summaries ───────────────────────────────────────────

def test_all_monthly_summaries_length():
    """Always returns exactly 12 entries for the requested year."""
    result = calculate_all_monthly_summaries(SAMPLE, 2024)
    assert len(result) == 12
    assert [r["month"] for r in result] == list(range(1, 13))


def test_all_monthly_summaries_values():
    result = calculate_all_monthly_summaries(SAMPLE, 2024)
    jan = result[0]   # month 1
    assert jan["income"]   == 3500.0
    assert jan["expenses"] == 1000.0
    assert jan["balance"]  == 2500.0


def test_all_monthly_summaries_empty_year():
    """Year with no data returns all zeros."""
    result = calculate_all_monthly_summaries(SAMPLE, 2020)
    assert all(r["income"] == 0.0 and r["expenses"] == 0.0 for r in result)


# ── calculate_budget_status ───────────────────────────────────────────────────

def test_budget_status_under():
    s = calculate_budget_status(500.0, 200.0)
    assert s["remaining"]       == 300.0
    assert s["percentage_used"] == 40.0
    assert s["is_over_budget"]  is False


def test_budget_status_over():
    s = calculate_budget_status(100.0, 150.0)
    assert s["remaining"]      == -50.0
    assert s["is_over_budget"] is True


def test_budget_status_exactly_at_limit():
    s = calculate_budget_status(300.0, 300.0)
    assert s["remaining"]       == 0.0
    assert s["percentage_used"] == 100.0
    assert s["is_over_budget"]  is False


# ── _val helper ───────────────────────────────────────────────────────────────

def test_val_reads_dict():
    assert _val({"type": "Income", "amount": 10.0}, "amount") == 10.0


def test_val_reads_sqlite_row():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT 42 AS amount").fetchone()
    assert _val(row, "amount") == 42
    conn.close()


def test_val_reads_model_object():
    class Stub:
        amount = 99.9
    assert _val(Stub(), "amount") == 99.9
