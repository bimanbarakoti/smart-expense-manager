"""Transaction model — represents a single financial transaction."""

import sqlite3


class Transaction:
    """Represents a financial transaction."""

    def __init__(
        self,
        id: int | None,
        type: str,
        amount: float,
        category_id: int,
        date: str,
        description: str,
        payment_method: str,
        category_name: str = "",
    ):
        self.id = id
        self.type = type
        self.amount = amount
        self.category_id = category_id
        self.date = date
        self.description = description
        self.payment_method = payment_method
        self.category_name = category_name  # denormalised for display

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Transaction":
        """Create a Transaction from a sqlite3.Row returned by the database."""
        return cls(
            id=row["id"],
            type=row["type"],
            amount=row["amount"],
            category_id=row["category_id"],
            date=row["date"],
            description=row["description"],
            payment_method=row["payment_method"],
            category_name=row["category_name"] if "category_name" in row.keys() else "",
        )

    def to_dict(self) -> dict:
        """Return a plain dict — used by calculation functions."""
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "category_id": self.category_id,
            "category": self.category_name,
            "date": self.date,
            "description": self.description,
            "payment_method": self.payment_method,
        }

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.id}, type={self.type}, "
            f"amount={self.amount}, date={self.date})"
        )
