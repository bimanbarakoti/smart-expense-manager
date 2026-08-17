"""Application-wide constants."""

APP_TITLE = "Smart Expense Manager"
APP_WIDTH = 1100
APP_HEIGHT = 700
DB_PATH = "expense_manager.db"

TRANSACTION_TYPES = ["Income", "Expense"]

PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "Bank Transfer", "Other"]

DEFAULT_CATEGORIES = [
    ("Salary", "Income"),
    ("Freelance", "Income"),
    ("Investment", "Income"),
    ("Other Income", "Income"),
    ("Food & Dining", "Expense"),
    ("Transport", "Expense"),
    ("Housing", "Expense"),
    ("Utilities", "Expense"),
    ("Healthcare", "Expense"),
    ("Entertainment", "Expense"),
    ("Shopping", "Expense"),
    ("Education", "Expense"),
    ("Other Expense", "Expense"),
]

DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%d %b %Y"
