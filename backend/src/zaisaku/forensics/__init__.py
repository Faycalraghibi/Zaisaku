"""Forensic financial analysis tools — filing diffs, Beneish M-Score, and accounting anomaly detection."""

from __future__ import annotations

from zaisaku.forensics.beneish import BeneishCalculator, BeneishMetrics, BeneishResult
from zaisaku.forensics.contradiction_radar import (
    ContradictionItem,
    ContradictionRadar,
    ContradictionRadarResult,
    ContradictionSeverity,
    ContradictionTopic,
)
from zaisaku.forensics.diff_engine import DiffEngine, FilingDiffResult, SectionDiff
from zaisaku.forensics.footnote_scanner import (
    FootnoteFinding,
    FootnoteRiskCategory,
    FootnoteScanner,
    FootnoteScanResult,
)
from zaisaku.forensics.report_generator import ForensicReportGenerator
from zaisaku.forensics.scorecard import ForensicScorecard, PillarScore, ScorecardResult
from zaisaku.forensics.section_extractor import SectionExtractor
from zaisaku.forensics.stress_tester import (
    MacroShockPreset,
    MonteCarloResult,
    ProFormaMetrics,
    ScenarioStressTester,
    StressSimulationRequest,
    StressSimulationResponse,
)

__all__ = [
    "BeneishCalculator",
    "BeneishMetrics",
    "BeneishResult",
    "ContradictionItem",
    "ContradictionRadar",
    "ContradictionRadarResult",
    "ContradictionSeverity",
    "ContradictionTopic",
    "DiffEngine",
    "FilingDiffResult",
    "FootnoteFinding",
    "FootnoteRiskCategory",
    "FootnoteScanResult",
    "FootnoteScanner",
    "ForensicReportGenerator",
    "ForensicScorecard",
    "MacroShockPreset",
    "MonteCarloResult",
    "PillarScore",
    "ProFormaMetrics",
    "ScenarioStressTester",
    "ScorecardResult",
    "SectionDiff",
    "SectionExtractor",
    "StressSimulationRequest",
    "StressSimulationResponse",
]
