from __future__ import annotations

import logging
from typing import ClassVar

import httpx

logger = logging.getLogger(__name__)


class SECEdgarClient:
    """Client for querying and downloading SEC EDGAR filings."""

    USER_AGENT: str = "ZaisakuFinancialBot/1.0 (contact@zaisaku.internal)"
    BASE_URL: str = "https://data.sec.gov"
    ARCHIVES_URL: str = "https://www.sec.gov/Archives/edgar/data"

    DEFAULT_CIKS: ClassVar[dict[str, int]] = {
        "AAPL": 320193,
        "MSFT": 789019,
        "NVDA": 1045810,
        "AMZN": 1018724,
        "GOOGL": 1652044,
        "GOOG": 1652044,
        "META": 1326801,
        "TSLA": 1318605,
        "JPM": 19617,
        "V": 1403161,
        "WMT": 104169,
    }

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout
        self.headers = {"User-Agent": self.USER_AGENT, "Accept-Encoding": "gzip, deflate"}

    def get_cik(self, ticker: str) -> int:
        ticker = ticker.strip().upper()
        if ticker in self.DEFAULT_CIKS:
            return self.DEFAULT_CIKS[ticker]

        # Dynamic lookup from SEC ticker directory
        url = "https://www.sec.gov/files/company_tickers.json"
        try:
            r = httpx.get(url, headers=self.headers, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker:
                    return int(entry["cik_str"])
        except Exception as e:
            logger.warning(f"Failed to lookup CIK for {ticker} from SEC: {e}")

        raise ValueError(f"Could not find CIK for ticker '{ticker}'.")

    def fetch_consecutive_filings(
        self, ticker: str, form: str = "10-K", count: int = 2
    ) -> list[tuple[str, bytes]]:
        """Fetch the N most recent filings of the given form for a ticker.

        Returns a list of (filename, content_bytes), newest first.
        """
        ticker = ticker.strip().upper()
        form = form.strip().upper()

        cik = self.get_cik(ticker)
        padded_cik = str(cik).zfill(10)
        sub_url = f"{self.BASE_URL}/submissions/CIK{padded_cik}.json"

        r = httpx.get(sub_url, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        sub_data = r.json()

        recent = sub_data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        target_indices: list[int] = []
        for i, f in enumerate(forms):
            if f.upper() == form:
                target_indices.append(i)
                if len(target_indices) >= count:
                    break

        if not target_indices:
            raise ValueError(f"No recent filing with form '{form}' found for {ticker}.")

        results: list[tuple[str, bytes]] = []
        for idx in target_indices:
            acc_num = accession_numbers[idx]
            primary_doc = primary_docs[idx]
            acc_no_dash = acc_num.replace("-", "")

            doc_url = f"{self.ARCHIVES_URL}/{cik}/{acc_no_dash}/{primary_doc}"
            logger.info(f"Downloading SEC filing from {doc_url}")

            doc_resp = httpx.get(doc_url, headers=self.headers, timeout=self.timeout)
            doc_resp.raise_for_status()

            clean_ext = ".htm" if primary_doc.lower().endswith((".htm", ".html")) else ".txt"
            filename = f"{ticker}_{form}_{acc_num}{clean_ext}"
            results.append((filename, doc_resp.content))

        return results

    def fetch_recent_filing(self, ticker: str, form: str = "10-K") -> tuple[str, bytes]:
        """Fetch the most recent filing of the given form for a ticker.

        Returns (filename, content_bytes).
        """
        filings = self.fetch_consecutive_filings(ticker, form, count=1)
        return filings[0]
