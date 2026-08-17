"""Tests for utils/validators.py"""

import pytest
from utils.validators import (
    validate_amount,
    validate_date,
    validate_required,
    validate_transaction_type,
    validate_transaction,
    validate_category_name,
    validate_budget_amount,
)


# --- validate_amount ---
def test_valid_amount():
    assert validate_amount("150.50") == (True, "")


def test_amount_zero():
    valid, msg = validate_amount("0")
    assert valid is False
    assert "greater than zero" in msg


def test_amount_negative():
    valid, msg = validate_amount("-10")
    assert valid is False


def test_amount_non_numeric():
    valid, msg = validate_amount("abc")
    assert valid is False
    assert "valid number" in msg


def test_amount_empty():
    valid, _ = validate_amount("")
    assert valid is False


# --- validate_date ---
def test_valid_date():
    assert validate_date("2024-06-15") == (True, "")


def test_invalid_date_format():
    valid, msg = validate_date("15/06/2024")
    assert valid is False


def test_invalid_date_value():
    valid, msg = validate_date("2024-13-01")
    assert valid is False


def test_date_empty():
    valid, _ = validate_date("")
    assert valid is False


# --- validate_required ---
def test_required_passes():
    assert validate_required("some value") == (True, "")


def test_required_empty_string():
    valid, msg = validate_required("")
    assert valid is False
    assert "required" in msg


def test_required_whitespace_only():
    valid, _ = validate_required("   ")
    assert valid is False


# --- validate_transaction_type ---
def test_valid_type_income():
    assert validate_transaction_type("Income") == (True, "")


def test_valid_type_expense():
    assert validate_transaction_type("Expense") == (True, "")


def test_invalid_type():
    valid, msg = validate_transaction_type("Transfer")
    assert valid is False


# --- validate_transaction (combined) ---
def test_valid_transaction():
    assert validate_transaction("Expense", "50.00", "Food & Dining", "2024-06-01", "Lunch") == (True, "")


def test_transaction_missing_description():
    valid, msg = validate_transaction("Expense", "50.00", "Food & Dining", "2024-06-01", "")
    assert valid is False
    assert "Description" in msg


def test_transaction_bad_amount():
    valid, msg = validate_transaction("Income", "abc", "Salary", "2024-06-01", "June salary")
    assert valid is False


# ── validate_category_name ───────────────────────────────────────────────────

def test_valid_category_name():
    assert validate_category_name("Groceries") == (True, "")


def test_category_name_empty():
    valid, msg = validate_category_name("")
    assert valid is False
    assert "required" in msg


def test_category_name_too_long():
    valid, msg = validate_category_name("A" * 51)
    assert valid is False
    assert "50 characters" in msg


def test_category_name_exactly_50_chars():
    assert validate_category_name("A" * 50) == (True, "")


# ── validate_budget_amount ──────────────────────────────────────────────────

def test_valid_budget_amount():
    assert validate_budget_amount("250.00") == (True, "")


def test_budget_amount_zero():
    valid, _ = validate_budget_amount("0")
    assert valid is False


def test_budget_amount_negative():
    valid, _ = validate_budget_amount("-100")
    assert valid is False
