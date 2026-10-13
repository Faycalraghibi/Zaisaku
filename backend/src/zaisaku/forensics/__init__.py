"""Forensic financial analysis tools — filing diffs, Beneish M-Score, and accounting anomaly detection."""

from __future__ import annotations

from zaisaku.forensics.diff_engine import DiffEngine, FilingDiffResult, SectionDiff
from zaisaku.forensics.section_extractor import SectionExtractor

__all__ = ["DiffEngine", "FilingDiffResult", "SectionDiff", "SectionExtractor"]
