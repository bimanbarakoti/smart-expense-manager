"""Tests for services/export_service.py

All tests write to a temporary directory so they never touch the real
exports/ folder and leave no artefacts after the suite finishes.
"""

import os
import sqlite3
import pytest
import pandas as pd

from database.database import init_db, insert_transaction, get_all_categories
from models.transaction import Transaction
from services.export_service import (
    export_transactions_csv,
    generate_pdf_report,
    ExportError,
    _safe_filename,
    _ensure_exports_dir,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_exports(tmp_path, monkeypatch):
    """Redirect EXPORTS_DIR to a pytest-managed temp directory."""
    import services.export_service as svc
    monkeypatch.setattr(svc, "EXPORTS_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def sample_transactions():
    """Four Transaction objects — no DB required."""
    def _tx(id_, type_, amount, cat_id, date, desc, payment, cat_name):
        t = Transaction(id_, type_, amount, cat_id, date, desc, payment, cat_name)
        return t

    return [
        _tx(1, "Income",  1500.0, 1, "2024-01-15", "January salary",  "Bank Transfer", "Salary"),
        _tx(2, "Income",   300.0, 1, "2024-02-15", "February salary", "Bank Transfer", "Salary"),
        _tx(3, "Expense",  120.5, 2, "2024-01-20", "Groceries",       "Debit Card",    "Food & Dining"),
        _tx(4, "Expense",   45.0, 2, "2024-02-10", "Restaurant",      "Credit Card",   "Food & Dining"),
    ]


# ── _safe_filename ────────────────────────────────────────────────────────────

def test_safe_filename_strips_spaces():
    assert " " not in _safe_filename("my file name.csv")


def test_safe_filename_strips_special_chars():
    result = _safe_filename("report/2024:01.pdf")
    assert "/" not in result
    assert ":" not in result


def test_safe_filename_preserves_dots_and_hyphens():
    result = _safe_filename("report-2024.csv")
    assert result == "report-2024.csv"


# ── _ensure_exports_dir ───────────────────────────────────────────────────────

def test_ensure_exports_dir_creates_directory(tmp_path, monkeypatch):
    import services.export_service as svc
    target = str(tmp_path / "new_exports")
    monkeypatch.setattr(svc, "EXPORTS_DIR", target)
    _ensure_exports_dir()
    assert os.path.isdir(target)


def test_ensure_exports_dir_idempotent(tmp_path, monkeypatch):
    """Calling twice must not raise."""
    import services.export_service as svc
    monkeypatch.setattr(svc, "EXPORTS_DIR", str(tmp_path))
    _ensure_exports_dir()
    _ensure_exports_dir()


# ── export_transactions_csv ───────────────────────────────────────────────────

class TestExportTransactionsCsv:

    def test_returns_file_path(self, tmp_exports, sample_transactions):
        path = export_transactions_csv(sample_transactions, "test.csv")
        assert os.path.isfile(path)

    def test_correct_columns(self, tmp_exports, sample_transactions):
        path = export_transactions_csv(sample_transactions, "test.csv")
        df = pd.read_csv(path)
        assert list(df.columns) == [
            "Date", "Type", "Category", "Description", "Amount (£)", "Payment Method"
        ]

    def test_correct_row_count(self, tmp_exports, sample_transactions):
        path = export_transactions_csv(sample_transactions, "test.csv")
        df = pd.read_csv(path)
        assert len(df) == 4

    def test_income_row_values(self, tmp_exports, sample_transactions):
        path = export_transactions_csv(sample_transactions, "test.csv")
        df = pd.read_csv(path)
        income_rows = df[df["Type"] == "Income"]
        assert len(income_rows) == 2
        assert set(income_rows["Category"]) == {"Salary"}

    def test_empty_list_produces_header_only_csv(self, tmp_exports):
        path = export_transactions_csv([], "empty.csv")
        df = pd.read_csv(path)
        assert len(df) == 0
        assert "Date" in df.columns

    def test_custom_filename_used(self, tmp_exports, sample_transactions):
        path = export_transactions_csv(sample_transactions, "custom_name.csv")
        assert path.endswith("custom_name.csv")

    def test_auto_filename_generated_when_blank(self, tmp_exports, sample_transactions):
        path = export_transactions_csv(sample_transactions)
        assert os.path.isfile(path)
        assert path.endswith(".csv")

    def test_amounts_preserved(self, tmp_exports, sample_transactions):
        path = export_transactions_csv(sample_transactions, "test.csv")
        df = pd.read_csv(path)
        assert 1500.0 in df["Amount (£)"].values
        assert 120.5  in df["Amount (£)"].values


# ── generate_pdf_report ───────────────────────────────────────────────────────

class TestGeneratePdfReport:

    def test_returns_file_path(self, tmp_exports, sample_transactions):
        path = generate_pdf_report(sample_transactions, "test.pdf")
        assert os.path.isfile(path)

    def test_pdf_has_content(self, tmp_exports, sample_transactions):
        path = generate_pdf_report(sample_transactions, "test.pdf")
        assert os.path.getsize(path) > 1000   # a real PDF is never tiny

    def test_empty_transactions_still_generates_pdf(self, tmp_exports):
        path = generate_pdf_report([], "empty.pdf")
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 500

    def test_custom_filename_used(self, tmp_exports, sample_transactions):
        path = generate_pdf_report(sample_transactions, "my_report.pdf")
        assert path.endswith("my_report.pdf")

    def test_auto_filename_generated_when_blank(self, tmp_exports, sample_transactions):
        path = generate_pdf_report(sample_transactions)
        assert os.path.isfile(path)
        assert path.endswith(".pdf")

    def test_pdf_magic_bytes(self, tmp_exports, sample_transactions):
        """File must start with the PDF magic number %PDF."""
        path = generate_pdf_report(sample_transactions, "test.pdf")
        with open(path, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_multi_year_data(self, tmp_exports):
        """Transactions spanning two years must not raise."""
        txs = [
            Transaction(1, "Income", 1000.0, 1, "2023-06-01", "Old salary", "Cash", "Salary"),
            Transaction(2, "Income", 1200.0, 1, "2024-06-01", "New salary", "Cash", "Salary"),
        ]
        path = generate_pdf_report(txs, "multi_year.pdf")
        assert os.path.isfile(path)
