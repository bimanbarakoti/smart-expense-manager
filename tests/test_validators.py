"""Tests for utils/validators.py"""

import pytest
from utils.validators import (
    validate_amount,
    validate_date,
    validate_required,
    validate_transaction_type,
    validate_transaction,
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
