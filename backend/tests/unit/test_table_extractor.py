from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.forensics.table_extractor import FinancialStatementsResponse, TableExtractor


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_table_extractor_nvda():
    extractor = TableExtractor()
    res = extractor.extract_tables("NVDA")
    assert isinstance(res, FinancialStatementsResponse)
    assert res.ticker == "NVDA"
    assert len(res.statements) >= 3

    # Check income statement
    is_stmt = next(s for s in res.statements if s.id == "income_statement")
    assert len(is_stmt.period_labels) >= 2
    assert len(is_stmt.rows) >= 5

    # Check total row
    rev_row = next(r for r in is_stmt.rows if "Revenue" in r.line_item)
    assert rev_row.values[0] > 0
    assert rev_row.yoy_change_pct is not None


def test_table_extractor_division_by_zero():
    extractor = TableExtractor()
    # Test zero previous period value calculation safety
    var = extractor._safe_yoy_pct(current=100.0, prior=0.0)
    assert var is None or var == 0.0 or var == 100.0


def test_table_api_endpoint(client):
    res = client.get("/api/forensics/tables/NVDA")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "NVDA"
    assert "statements" in data
    assert len(data["statements"]) >= 3
