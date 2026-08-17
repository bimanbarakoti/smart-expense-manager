"""Transaction model — data class representing a single transaction."""


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
    ):
        self.id = id
        self.type = type
        self.amount = amount
        self.category_id = category_id
        self.date = date
        self.description = description
        self.payment_method = payment_method

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, type={self.type}, amount={self.amount}, date={self.date})"
