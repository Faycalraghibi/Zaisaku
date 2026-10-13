from __future__ import annotations

import pytest

from zaisaku.ingestion.sec_edgar import SECEdgarClient


class TestSECEdgarClient:
    def test_get_cik_default(self):
        client = SECEdgarClient()
        assert client.get_cik("AAPL") == 320193
        assert client.get_cik("NVDA") == 1045810
        assert client.get_cik("msft") == 789019

    def test_get_cik_unknown_raises(self, monkeypatch):
        client = SECEdgarClient()

        class MockResp:
            def raise_for_status(self):
                pass
            def json(self):
                return {}

        monkeypatch.setattr("httpx.get", lambda *args, **kwargs: MockResp())
        with pytest.raises(ValueError, match="Could not find CIK"):
            client.get_cik("NONEXISTENT123")

    def test_fetch_recent_filing_success(self, monkeypatch):
        client = SECEdgarClient()

        submission_json = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q"],
                    "accessionNumber": ["0001045810-24-000029", "0001045810-24-000010"],
                    "primaryDocument": ["nvda-20240128.htm", "nvda-20231029.htm"],
                }
            }
        }

        def mock_get(url, *args, **kwargs):
            class MockResp:
                def __init__(self, data, content):
                    self._data = data
                    self.content = content
                def raise_for_status(self):
                    pass
                def json(self):
                    return self._data

            if "submissions" in url:
                return MockResp(submission_json, b"")
            return MockResp({}, b"<html><body>NVIDIA 10-K Report content</body></html>")

        monkeypatch.setattr("httpx.get", mock_get)

        filename, content = client.fetch_recent_filing("NVDA", "10-K")
        assert filename == "NVDA_10-K_001045810-24-000029.htm" or "NVDA_10-K_" in filename
        assert b"NVIDIA 10-K" in content
