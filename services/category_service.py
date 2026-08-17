"""Category service — business logic for managing categories.

This module sits between the GUI and the database layer.
All public functions validate input before touching the database.
"""

import sqlite3

from database.database import (
    get_all_categories as _db_get_all,
    get_category_by_id as _db_get_by_id,
    insert_category as _db_insert,
    update_category as _db_update,
    delete_category as _db_delete,
    _DB,
)
from models.category import Category
from utils.validators import validate_required, validate_transaction_type


class CategoryError(Exception):
    """Raised when a category operation fails validation or a DB constraint."""


def get_all_categories(db: _DB = None) -> list[Category]:
    """Return all categories as Category objects, ordered by type then name.

    Args:
        db: Optional DB path or connection (uses default DB when omitted).
    """
    kwargs = {"db": db} if db is not None else {}
    rows = _db_get_all(**kwargs)
    return [Category.from_row(r) for r in rows]


def get_category_by_id(category_id: int, db: _DB = None) -> Category | None:
    """Return a Category by id, or None if not found."""
    kwargs = {"db": db} if db is not None else {}
    row = _db_get_by_id(category_id, **kwargs)
    return Category.from_row(row) if row else None


def get_categories_by_type(type_: str, db: _DB = None) -> list[Category]:
    """Return only Income or only Expense categories.

    Args:
        type_: 'Income' or 'Expense'.
    """
    return [c for c in get_all_categories(db) if c.type == type_]


def create_category(name: str, type_: str, db: _DB = None) -> Category:
    """Validate and create a new category.

    Args:
        name:  Category name (must be unique and non-empty).
        type_: 'Income' or 'Expense'.
        db:    Optional DB path or connection.

    Returns:
        The newly created Category with its assigned id.

    Raises:
        CategoryError: on validation failure or duplicate name.
    """
    valid, msg = validate_required(name, "Category name")
    if not valid:
        raise CategoryError(msg)

    valid, msg = validate_transaction_type(type_)
    if not valid:
        raise CategoryError(msg)

    try:
        kwargs = {"db": db} if db is not None else {}
        new_id = _db_insert(name.strip(), type_, **kwargs)
        return Category(id=new_id, name=name.strip(), type=type_)
    except sqlite3.IntegrityError:
        raise CategoryError(f"A category named '{name}' already exists.")


def update_category(category_id: int, name: str, type_: str, db: _DB = None) -> Category:
    """Validate and update an existing category.

    Returns:
        The updated Category object.

    Raises:
        CategoryError: on validation failure, duplicate name, or not found.
    """
    valid, msg = validate_required(name, "Category name")
    if not valid:
        raise CategoryError(msg)

    valid, msg = validate_transaction_type(type_)
    if not valid:
        raise CategoryError(msg)

    try:
        kwargs = {"db": db} if db is not None else {}
        _db_update(category_id, name.strip(), type_, **kwargs)
        return Category(id=category_id, name=name.strip(), type=type_)
    except sqlite3.IntegrityError:
        raise CategoryError(f"A category named '{name}' already exists.")


def delete_category(category_id: int, db: _DB = None) -> None:
    """Delete a category if no transactions reference it.

    Raises:
        CategoryError: if transactions exist for this category.
    """
    try:
        kwargs = {"db": db} if db is not None else {}
        _db_delete(category_id, **kwargs)
    except sqlite3.IntegrityError:
        raise CategoryError(
            "Cannot delete this category because transactions are linked to it. "
            "Delete or reassign those transactions first."
        )
