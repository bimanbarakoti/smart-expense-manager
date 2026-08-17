"""Category model — data class representing a transaction category."""


class Category:
    """Represents a transaction category."""

    def __init__(self, id: int | None, name: str, type: str):
        self.id = id
        self.name = name
        self.type = type  # "Income" or "Expense"

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name={self.name}, type={self.type})"
