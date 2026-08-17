"""Transaction service — business logic for managing transactions.

This module sits between the GUI and the database layer.
All public functions validate input before touching the database.
"""

import sqlite3

from database.database import (
    get_all_transactions as _db_get_all,
    get_transaction_by_id as _db_get_by_id,
    insert_transaction as _db_insert,
    update_transaction as _db_update,
    delete_transaction as _db_delete,
    search_transactions as _db_search,
    _DB,
)
from models.transaction import Transaction
from utils.validators import validate_transaction, validate_amount, validate_date
from utils.constants import PAYMENT_METHODS


class TransactionError(Exception):
    """Raised when a transaction operation fails validation."""


def _row_to_transaction(row) -> Transaction:
    return Transaction.from_row(row)


def get_all_transactions(db: _DB = None) -> list[Transaction]:
    """Return all transactions as Transaction objects, newest first."""
    kwargs = {"db": db} if db is not None else {}
    return [_row_to_transaction(r) for r in _db_get_all(**kwargs)]


def get_transaction_by_id(transaction_id: int, db: _DB = None) -> Transaction | None:
    """Return a Transaction by id, or None if not found."""
    kwargs = {"db": db} if db is not None else {}
    row = _db_get_by_id(transaction_id, **kwargs)
    return _row_to_transaction(row) if row else None


def create_transaction(
    type_: str,
    amount: str,
    category_id: int,
    date: str,
    description: str,
    payment_method: str,
    db: _DB = None,
) -> Transaction:
    """Validate and create a new transaction.

    Args:
        type_:          'Income' or 'Expense'.
        amount:         Amount as a string (validated and converted here).
        category_id:    ID of an existing category.
        date:           Date string in YYYY-MM-DD format.
        description:    Non-empty description.
        payment_method: One of the allowed payment methods.
        db:             Optional DB path or connection.

    Returns:
        The newly created Transaction with its assigned id.

    Raises:
        TransactionError: on any validation failure.
    """
    # Validate all fields together
    valid, msg = validate_transaction(type_, amount, str(category_id), date, description)
    if not valid:
        raise TransactionError(msg)

    if payment_method not in PAYMENT_METHODS:
        raise TransactionError(f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}.")

    try:
        kwargs = {"db": db} if db is not None else {}
        new_id = _db_insert(
            type_, float(amount), category_id, date, description.strip(), payment_method, **kwargs
        )
        return Transaction(
            id=new_id,
            type=type_,
            amount=float(amount),
            category_id=category_id,
            date=date,
            description=description.strip(),
            payment_method=payment_method,
        )
    except sqlite3.IntegrityError as exc:
        raise TransactionError(f"Database error: {exc}") from exc


def update_transaction(
    transaction_id: int,
    type_: str,
    amount: str,
    category_id: int,
    date: str,
    description: str,
    payment_method: str,
    db: _DB = None,
) -> Transaction:
    """Validate and update an existing transaction.

    Returns:
        The updated Transaction object.

    Raises:
        TransactionError: on any validation failure.
    """
    valid, msg = validate_transaction(type_, amount, str(category_id), date, description)
    if not valid:
        raise TransactionError(msg)

    if payment_method not in PAYMENT_METHODS:
        raise TransactionError(f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}.")

    try:
        kwargs = {"db": db} if db is not None else {}
        _db_update(
            transaction_id, type_, float(amount), category_id,
            date, description.strip(), payment_method, **kwargs
        )
        return Transaction(
            id=transaction_id,
            type=type_,
            amount=float(amount),
            category_id=category_id,
            date=date,
            description=description.strip(),
            payment_method=payment_method,
        )
    except sqlite3.IntegrityError as exc:
        raise TransactionError(f"Database error: {exc}") from exc


def delete_transaction(transaction_id: int, db: _DB = None) -> None:
    """Delete a transaction by id.

    Raises:
        TransactionError: if the transaction does not exist.
    """
    kwargs = {"db": db} if db is not None else {}
    if get_transaction_by_id(transaction_id, db) is None:
        raise TransactionError(f"Transaction {transaction_id} not found.")
    _db_delete(transaction_id, **kwargs)


def search_transactions(
    keyword: str = "",
    type_filter: str = "",
    category_id: int | None = None,
    date_from: str = "",
    date_to: str = "",
    db: _DB = None,
) -> list[Transaction]:
    """Search and filter transactions. All parameters are optional.

    Args:
        keyword:     Matches against description (case-insensitive).
        type_filter: 'Income', 'Expense', or '' for both.
        category_id: Filter to a specific category, or None for all.
        date_from:   Inclusive start date (YYYY-MM-DD), or '' for no lower bound.
        date_to:     Inclusive end date   (YYYY-MM-DD), or '' for no upper bound.
        db:          Optional DB path or connection.

    Raises:
        TransactionError: if date_from or date_to are provided but invalid.
    """
    if date_from:
        valid, msg = validate_date(date_from)
        if not valid:
            raise TransactionError(f"Invalid date_from: {msg}")
    if date_to:
        valid, msg = validate_date(date_to)
        if not valid:
            raise TransactionError(f"Invalid date_to: {msg}")

    kwargs = {"db": db} if db is not None else {}
    rows = _db_search(
        keyword=keyword,
        type_filter=type_filter,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        **kwargs,
    )
    return [_row_to_transaction(r) for r in rows]
