"""Category model — represents a transaction category."""

import sqlite3


class Category:
    """Represents a transaction category."""

    def __init__(self, id: int | None, name: str, type: str):
        self.id = id
        self.name = name
        self.type = type  # "Income" or "Expense"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Category":
        """Create a Category from a sqlite3.Row returned by the database."""
        return cls(id=row["id"], name=row["name"], type=row["type"])

    def to_dict(self) -> dict:
        """Return a plain dict representation."""
        return {"id": self.id, "name": self.name, "type": self.type}

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name={self.name!r}, type={self.type!r})"
