"""Input validation utilities.

All functions return a (is_valid: bool, error_message: str) tuple.
An empty error string means the value is valid.
"""

from datetime import datetime
from utils.constants import DATE_FORMAT, TRANSACTION_TYPES


def validate_amount(value: str) -> tuple[bool, str]:
    """Validate that value is a positive number."""
    try:
        amount = float(value)
        if amount <= 0:
            return False, "Amount must be greater than zero."
        return True, ""
    except (ValueError, TypeError):
        return False, "Amount must be a valid number."


def validate_date(value: str) -> tuple[bool, str]:
    """Validate that value is a date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(value, DATE_FORMAT)
        return True, ""
    except (ValueError, TypeError):
        return False, "Date must be in format YYYY-MM-DD."


def validate_required(value: str, field_name: str = "Field") -> tuple[bool, str]:
    """Validate that a required field is not empty or whitespace-only."""
    if not value or not str(value).strip():
        return False, f"{field_name} is required."
    return True, ""


def validate_transaction_type(value: str) -> tuple[bool, str]:
    """Validate that value is one of the allowed transaction types."""
    if value not in TRANSACTION_TYPES:
        return False, f"Type must be one of: {', '.join(TRANSACTION_TYPES)}."
    return True, ""


def validate_category_name(name: str) -> tuple[bool, str]:
    """Validate a category name: non-empty and within a reasonable length."""
    valid, msg = validate_required(name, "Category name")
    if not valid:
        return False, msg
    if len(name.strip()) > 50:
        return False, "Category name must be 50 characters or fewer."
    return True, ""


def validate_budget_amount(value: str) -> tuple[bool, str]:
    """Validate a budget amount — same rules as a transaction amount."""
    return validate_amount(value)


def validate_transaction(
    type_: str, amount: str, category: str, date: str, description: str
) -> tuple[bool, str]:
    """Run all transaction field validations in order.

    Returns the first failure found, or (True, '') if all pass.
    """
    checks = [
        validate_transaction_type(type_),
        validate_amount(amount),
        validate_required(category, "Category"),
        validate_date(date),
        validate_required(description, "Description"),
    ]
    for is_valid, message in checks:
        if not is_valid:
            return False, message
    return True, ""
