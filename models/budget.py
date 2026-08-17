"""Budget model — represents a monthly category budget."""

import sqlite3


class Budget:
    """Represents a monthly budget for a category."""

    def __init__(
        self,
        id: int | None,
        category_id: int,
        month: int,
        year: int,
        amount: float,
        category_name: str = "",
    ):
        self.id = id
        self.category_id = category_id
        self.month = month
        self.year = year
        self.amount = amount
        self.category_name = category_name  # denormalised for display

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Budget":
        """Create a Budget from a sqlite3.Row returned by the database."""
        return cls(
            id=row["id"],
            category_id=row["category_id"],
            month=row["month"],
            year=row["year"],
            amount=row["amount"],
            category_name=row["category_name"] if "category_name" in row.keys() else "",
        )

    def to_dict(self) -> dict:
        """Return a plain dict representation."""
        return {
            "id": self.id,
            "category_id": self.category_id,
            "month": self.month,
            "year": self.year,
            "amount": self.amount,
            "category_name": self.category_name,
        }

    def __repr__(self) -> str:
        return (
            f"Budget(id={self.id}, category={self.category_name!r}, "
            f"{self.month:02d}/{self.year}, amount={self.amount})"
        )
