-- Smart Expense Manager — database schema
-- SQLite enforces foreign keys only when PRAGMA foreign_keys = ON is set per connection.

CREATE TABLE IF NOT EXISTS categories (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT    NOT NULL UNIQUE,
    type  TEXT    NOT NULL CHECK(type IN ('Income', 'Expense'))
);

CREATE TABLE IF NOT EXISTS transactions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    type           TEXT    NOT NULL CHECK(type IN ('Income', 'Expense')),
    amount         REAL    NOT NULL CHECK(amount > 0),
    category_id    INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    date           TEXT    NOT NULL,   -- stored as YYYY-MM-DD
    description    TEXT    NOT NULL,
    payment_method TEXT    NOT NULL DEFAULT 'Cash'
);

CREATE TABLE IF NOT EXISTS budgets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    month       INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    year        INTEGER NOT NULL CHECK(year >= 2000),
    amount      REAL    NOT NULL CHECK(amount > 0),
    UNIQUE(category_id, month, year)   -- one budget per category per month
);
