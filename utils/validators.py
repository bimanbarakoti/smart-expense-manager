"""Input validation utilities."""

from datetime import datetime
from utils.constants import DATE_FORMAT, TRANSACTION_TYPES


def validate_amount(value: str) -> tuple[bool, str]:
    """Validate that amount is a positive number."""
    try:
        amount = float(value)
        if amount <= 0:
            return False, "Amount must be greater than zero."
        return True, ""
    except (ValueError, TypeError):
        return False, "Amount must be a valid number."


def validate_date(value: str) -> tuple[bool, str]:
    """Validate date string matches expected format."""
    try:
        datetime.strptime(value, DATE_FORMAT)
        return True, ""
    except (ValueError, TypeError):
        return False, f"Date must be in format YYYY-MM-DD."


def validate_required(value: str, field_name: str = "Field") -> tuple[bool, str]:
    """Validate that a required field is not empty."""
    if not value or not str(value).strip():
        return False, f"{field_name} is required."
    return True, ""


def validate_transaction_type(value: str) -> tuple[bool, str]:
    """Validate transaction type is one of the allowed values."""
    if value not in TRANSACTION_TYPES:
        return False, f"Type must be one of: {', '.join(TRANSACTION_TYPES)}."
    return True, ""


def validate_transaction(
    type_: str, amount: str, category: str, date: str, description: str
) -> tuple[bool, str]:
    """Run all transaction field validations. Returns (is_valid, error_message)."""
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
