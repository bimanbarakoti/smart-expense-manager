"""Core business logic calculations."""


def calculate_total_income(transactions: list[dict]) -> float:
    """Sum all income transactions."""
    return sum(t["amount"] for t in transactions if t["type"] == "Income")


def calculate_total_expenses(transactions: list[dict]) -> float:
    """Sum all expense transactions."""
    return sum(t["amount"] for t in transactions if t["type"] == "Expense")


def calculate_balance(transactions: list[dict]) -> float:
    """Calculate net balance (income - expenses)."""
    return calculate_total_income(transactions) - calculate_total_expenses(transactions)


def calculate_budget_remaining(budget_amount: float, spent: float) -> float:
    """Calculate remaining budget."""
    return budget_amount - spent


def calculate_category_percentage(category_total: float, grand_total: float) -> float:
    """Calculate what percentage a category represents of total spending."""
    if grand_total == 0:
        return 0.0
    return round((category_total / grand_total) * 100, 2)


def calculate_monthly_summary(transactions: list[dict], year: int, month: int) -> dict:
    """Return income, expenses, and balance for a given month."""
    monthly = [
        t for t in transactions
        if t["date"].startswith(f"{year}-{month:02d}")
    ]
    income = calculate_total_income(monthly)
    expenses = calculate_total_expenses(monthly)
    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
    }


def calculate_category_totals(transactions: list[dict]) -> dict[str, float]:
    """Return a dict of category -> total amount for expense transactions."""
    totals: dict[str, float] = {}
    for t in transactions:
        if t["type"] == "Expense":
            totals[t["category"]] = totals.get(t["category"], 0.0) + t["amount"]
    return totals
