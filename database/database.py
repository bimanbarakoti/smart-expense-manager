"""Database connection, initialisation, and CRUD operations."""

import sqlite3
from pathlib import Path

from utils.constants import DB_PATH, DEFAULT_CATEGORIES

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Type alias — functions accept either a file path or an open connection.
_DB = str | sqlite3.Connection


# ── Connection helper ─────────────────────────────────────────────────────────

def get_connection(db: _DB = DB_PATH) -> sqlite3.Connection:
    """Return a configured SQLite connection.

    Args:
        db: A file path string, ':memory:', or an existing Connection object.
            When an existing Connection is passed it is returned as-is so that
            in-memory test databases can be shared across calls.

    Returns:
        sqlite3.Connection with row_factory and foreign-key enforcement set.
    """
    if isinstance(db, sqlite3.Connection):
        return db
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _conn(db: _DB) -> sqlite3.Connection:
    """Internal shorthand — always returns a ready connection."""
    return get_connection(db)


# ── Initialisation ────────────────────────────────────────────────────────────

def init_db(db: _DB = DB_PATH) -> None:
    """Create tables (if absent) and seed default categories.

    Safe to call on every application start — uses IF NOT EXISTS and
    INSERT OR IGNORE so existing data is never overwritten.
    """
    schema = _SCHEMA_PATH.read_text(encoding="utf-8")
    conn = _conn(db)
    conn.executescript(schema)
    conn.executemany(
        "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
        DEFAULT_CATEGORIES,
    )
    conn.commit()


# ── Category CRUD ─────────────────────────────────────────────────────────────

def get_all_categories(db: _DB = DB_PATH) -> list[sqlite3.Row]:
    """Return all categories ordered by type then name."""
    return _conn(db).execute(
        "SELECT * FROM categories ORDER BY type, name"
    ).fetchall()


def get_category_by_id(category_id: int, db: _DB = DB_PATH) -> sqlite3.Row | None:
    """Return a single category row or None if not found."""
    return _conn(db).execute(
        "SELECT * FROM categories WHERE id = ?", (category_id,)
    ).fetchone()


def insert_category(name: str, type_: str, db: _DB = DB_PATH) -> int:
    """Insert a new category and return its new id.

    Raises:
        sqlite3.IntegrityError: if the name already exists or type is invalid.
    """
    conn = _conn(db)
    cursor = conn.execute(
        "INSERT INTO categories (name, type) VALUES (?, ?)", (name, type_)
    )
    conn.commit()
    return cursor.lastrowid


def update_category(category_id: int, name: str, type_: str, db: _DB = DB_PATH) -> None:
    """Update an existing category's name and type."""
    conn = _conn(db)
    conn.execute(
        "UPDATE categories SET name = ?, type = ? WHERE id = ?",
        (name, type_, category_id),
    )
    conn.commit()


def delete_category(category_id: int, db: _DB = DB_PATH) -> None:
    """Delete a category.

    Raises:
        sqlite3.IntegrityError: if transactions reference this category
        (ON DELETE RESTRICT prevents orphaned transactions).
    """
    conn = _conn(db)
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()


# ── Transaction CRUD ──────────────────────────────────────────────────────────

def get_all_transactions(db: _DB = DB_PATH) -> list[sqlite3.Row]:
    """Return all transactions joined with their category name, newest first."""
    return _conn(db).execute(
        """
        SELECT t.*, c.name AS category_name
        FROM   transactions t
        JOIN   categories   c ON t.category_id = c.id
        ORDER  BY t.date DESC, t.id DESC
        """
    ).fetchall()


def get_transaction_by_id(transaction_id: int, db: _DB = DB_PATH) -> sqlite3.Row | None:
    """Return a single transaction row (with category_name) or None."""
    return _conn(db).execute(
        """
        SELECT t.*, c.name AS category_name
        FROM   transactions t
        JOIN   categories   c ON t.category_id = c.id
        WHERE  t.id = ?
        """,
        (transaction_id,),
    ).fetchone()


def insert_transaction(
    type_: str,
    amount: float,
    category_id: int,
    date: str,
    description: str,
    payment_method: str,
    db: _DB = DB_PATH,
) -> int:
    """Insert a new transaction and return its new id."""
    conn = _conn(db)
    cursor = conn.execute(
        """
        INSERT INTO transactions
            (type, amount, category_id, date, description, payment_method)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (type_, amount, category_id, date, description, payment_method),
    )
    conn.commit()
    return cursor.lastrowid


def update_transaction(
    transaction_id: int,
    type_: str,
    amount: float,
    category_id: int,
    date: str,
    description: str,
    payment_method: str,
    db: _DB = DB_PATH,
) -> None:
    """Update every field of an existing transaction."""
    conn = _conn(db)
    conn.execute(
        """
        UPDATE transactions
        SET    type = ?, amount = ?, category_id = ?,
               date = ?, description = ?, payment_method = ?
        WHERE  id = ?
        """,
        (type_, amount, category_id, date, description, payment_method, transaction_id),
    )
    conn.commit()


def delete_transaction(transaction_id: int, db: _DB = DB_PATH) -> None:
    """Delete a transaction by id."""
    conn = _conn(db)
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()


def search_transactions(
    keyword: str = "",
    type_filter: str = "",
    category_id: int | None = None,
    date_from: str = "",
    date_to: str = "",
    db: _DB = DB_PATH,
) -> list[sqlite3.Row]:
    """Search and filter transactions. All parameters are optional.

    Args:
        keyword:     Matches against description (case-insensitive).
        type_filter: 'Income', 'Expense', or '' for both.
        category_id: Filter to a specific category, or None for all.
        date_from:   Inclusive start date (YYYY-MM-DD), or '' for no lower bound.
        date_to:     Inclusive end date   (YYYY-MM-DD), or '' for no upper bound.
        db:          File path or open Connection.
    """
    query = """
        SELECT t.*, c.name AS category_name
        FROM   transactions t
        JOIN   categories   c ON t.category_id = c.id
        WHERE  1=1
    """
    params: list = []

    if keyword:
        query += " AND t.description LIKE ?"
        params.append(f"%{keyword}%")
    if type_filter:
        query += " AND t.type = ?"
        params.append(type_filter)
    if category_id is not None:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if date_from:
        query += " AND t.date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND t.date <= ?"
        params.append(date_to)

    query += " ORDER BY t.date DESC, t.id DESC"
    return _conn(db).execute(query, params).fetchall()


# ── Budget CRUD ───────────────────────────────────────────────────────────────

def get_all_budgets(db: _DB = DB_PATH) -> list[sqlite3.Row]:
    """Return all budgets joined with category name."""
    return _conn(db).execute(
        """
        SELECT b.*, c.name AS category_name
        FROM   budgets     b
        JOIN   categories  c ON b.category_id = c.id
        ORDER  BY b.year DESC, b.month DESC, c.name
        """
    ).fetchall()


def get_budgets_for_month(month: int, year: int, db: _DB = DB_PATH) -> list[sqlite3.Row]:
    """Return all budgets for a specific month/year with category name."""
    return _conn(db).execute(
        """
        SELECT b.*, c.name AS category_name
        FROM   budgets    b
        JOIN   categories c ON b.category_id = c.id
        WHERE  b.month = ? AND b.year = ?
        ORDER  BY c.name
        """,
        (month, year),
    ).fetchall()


def insert_budget(
    category_id: int, month: int, year: int, amount: float, db: _DB = DB_PATH
) -> int:
    """Insert a new budget and return its new id.

    Raises:
        sqlite3.IntegrityError: if a budget for that category/month/year exists.
    """
    conn = _conn(db)
    cursor = conn.execute(
        "INSERT INTO budgets (category_id, month, year, amount) VALUES (?, ?, ?, ?)",
        (category_id, month, year, amount),
    )
    conn.commit()
    return cursor.lastrowid


def update_budget(budget_id: int, amount: float, db: _DB = DB_PATH) -> None:
    """Update the amount of an existing budget."""
    conn = _conn(db)
    conn.execute("UPDATE budgets SET amount = ? WHERE id = ?", (amount, budget_id))
    conn.commit()


def delete_budget(budget_id: int, db: _DB = DB_PATH) -> None:
    """Delete a budget by id."""
    conn = _conn(db)
    conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
    conn.commit()
