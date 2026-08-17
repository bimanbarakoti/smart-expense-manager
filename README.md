# Smart Personal Expense & Budget Manager

A desktop GUI application for managing personal income, expenses, budgets, and financial reports — built with Python as a university programming project.

## Features

- Dashboard with balance, income, expense summary and recent transactions
- Full transaction management (add, edit, delete, search, filter)
- Category management with defaults
- Monthly budget tracking with overspend alerts
- Financial reports with Matplotlib charts
- CSV export (Pandas) and PDF report generation (ReportLab)
- SQLite persistent storage
- Full pytest unit test suite

## Technologies

| Purpose | Library |
|---|---|
| GUI | Tkinter / CustomTkinter |
| Database | SQLite3 |
| Data processing | Pandas |
| Charts | Matplotlib |
| PDF reports | ReportLab |
| Date picker | tkcalendar |
| Testing | pytest |

## Installation

```bash
git clone <repo-url>
cd smart-expense-manager
python -m pip install -r requirements.txt
```

## How to Run

```bash
python app.py
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
app.py                  # Entry point
database/
    database.py         # DB connection and setup
    schema.sql          # Table definitions
models/
    transaction.py
    category.py
    budget.py
services/
    transaction_service.py
    category_service.py
    budget_service.py
    report_service.py
    export_service.py
gui/
    dashboard.py
    transaction_form.py
    transaction_list.py
    category_view.py
    budget_view.py
    report_view.py
utils/
    constants.py        # App-wide constants
    validators.py       # Input validation
    calculations.py     # Business logic calculations
tests/
    test_calculations.py
    test_validators.py
    test_transactions.py
    test_categories.py
    test_budget.py
    test_database.py
exports/                # Generated CSV and PDF files
```

## Database Design

- `categories` — id, name, type (Income/Expense)
- `transactions` — id, type, amount, category_id, date, description, payment_method
- `budgets` — id, category_id, month, year, amount

## Git Workflow

Feature branches merged into `main`:
- `feature/project-setup`
- `feature/database`
- `feature/models-services`
- `feature/gui`
- `feature/budget`
- `feature/reports`
- `feature/export`
- `feature/testing`
- `feature/documentation`

## Screenshots

_To be added after GUI is complete._

## Future Improvements

- Multi-user support
- Cloud sync
- Mobile companion app
- Recurring transaction automation
