"""Forensic financial analysis tools — filing diffs, Beneish M-Score, and accounting anomaly detection."""

from __future__ import annotations

from zaisaku.forensics.beneish import BeneishCalculator, BeneishMetrics, BeneishResult
from zaisaku.forensics.diff_engine import DiffEngine, FilingDiffResult, SectionDiff
from zaisaku.forensics.footnote_scanner import (
    FootnoteFinding,
    FootnoteRiskCategory,
    FootnoteScanner,
    FootnoteScanResult,
)
from zaisaku.forensics.section_extractor import SectionExtractor

__all__ = [
    "BeneishCalculator",
    "BeneishMetrics",
    "BeneishResult",
    "DiffEngine",
    "FilingDiffResult",
    "FootnoteFinding",
    "FootnoteRiskCategory",
    "FootnoteScanResult",
    "FootnoteScanner",
    "SectionDiff",
    "SectionExtractor",
]
