"""Budget model — data class representing a monthly category budget."""


class Budget:
    """Represents a monthly budget for a category."""

    def __init__(
        self,
        id: int | None,
        category_id: int,
        month: int,
        year: int,
        amount: float,
    ):
        self.id = id
        self.category_id = category_id
        self.month = month
        self.year = year
        self.amount = amount

    def __repr__(self) -> str:
        return f"Budget(id={self.id}, category_id={self.category_id}, {self.month}/{self.year}, amount={self.amount})"
