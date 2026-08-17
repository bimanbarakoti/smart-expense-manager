"""Tests for utils/calculations.py"""

import pytest
from utils.calculations import (
    calculate_total_income,
    calculate_total_expenses,
    calculate_balance,
    calculate_budget_remaining,
    calculate_category_percentage,
    calculate_monthly_summary,
    calculate_category_totals,
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
