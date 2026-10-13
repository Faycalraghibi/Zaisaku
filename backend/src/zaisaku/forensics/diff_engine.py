"""Filing diff engine — detects language drift, stealth additions, and removed risk factors."""

from __future__ import annotations

import difflib
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from zaisaku.forensics.section_extractor import SectionExtractor

if TYPE_CHECKING:
    from zaisaku.generation.llm import LLMRouter


@dataclass
class SectionDiff:
    section_name: str
    similarity_ratio: float
    drift_score: float
    severity: str
    added_paragraphs: list[str] = field(default_factory=list)
    removed_paragraphs: list[str] = field(default_factory=list)
    modified_paragraphs: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FilingDiffResult:
    ticker: str
    form: str
    current_filing: str
    prior_filing: str
    overall_drift_score: float
    overall_severity: str
    sections: dict[str, SectionDiff] = field(default_factory=dict)
    forensic_summary: str = ""

    def to_dict(self) -> dict:
        res = asdict(self)
        res["sections"] = {k: v.to_dict() for k, v in self.sections.items()}
        return res


class DiffEngine:
    """Compares consecutive corporate SEC filings and quantifies language drift risk."""

    @staticmethod
    def _split_paragraphs(text: str) -> list[str]:
        """Split text into substantive paragraphs (filtering out titles and noise)."""
        raw = [p.strip() for p in text.split("\n\n")]
        return [p for p in raw if len(p) >= 40]

    @classmethod
    def compare_sections(cls, current_text: str, prior_text: str, section_name: str) -> SectionDiff:
        """Perform granular paragraph alignment and compute drift metrics between two texts."""
        clean_current = SectionExtractor.clean_boilerplate(current_text)
        clean_prior = SectionExtractor.clean_boilerplate(prior_text)

        if not clean_current and not clean_prior:
            return SectionDiff(
                section_name=section_name,
                similarity_ratio=1.0,
                drift_score=0.0,
                severity="LOW",
            )
        if not clean_current or not clean_prior:
            return SectionDiff(
                section_name=section_name,
                similarity_ratio=0.0,
                drift_score=100.0,
                severity="CRITICAL",
                added_paragraphs=cls._split_paragraphs(clean_current) if clean_current else [],
                removed_paragraphs=cls._split_paragraphs(clean_prior) if clean_prior else [],
            )

        # Overall section ratio
        matcher = difflib.SequenceMatcher(None, clean_current, clean_prior)
        ratio = round(matcher.ratio(), 4)
        drift = round((1.0 - ratio) * 100, 1)

        if drift >= 60.0:
            severity = "CRITICAL"
        elif drift >= 35.0:
            severity = "HIGH"
        elif drift >= 15.0:
            severity = "MODERATE"
        else:
            severity = "LOW"

        curr_paras = cls._split_paragraphs(clean_current)
        prior_paras = cls._split_paragraphs(clean_prior)

        added: list[str] = []
        modified: list[dict[str, str]] = []
        matched_prior_indices: set[int] = set()

        for curr_p in curr_paras:
            best_sim = 0.0
            best_idx = -1
            for idx, prior_p in enumerate(prior_paras):
                sim = difflib.SequenceMatcher(None, curr_p, prior_p).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best_idx = idx

            if best_sim >= 0.95:
                # Virtually unchanged
                if best_idx >= 0:
                    matched_prior_indices.add(best_idx)
            elif best_sim >= 0.60:
                # Substantive modification
                if best_idx >= 0:
                    matched_prior_indices.add(best_idx)
                    modified.append({"old": prior_paras[best_idx], "new": curr_p})
            else:
                # Completely new paragraph
                added.append(curr_p)

        # Removed paragraphs: prior paragraphs that found no match in current
        removed: list[str] = [
            prior_p for idx, prior_p in enumerate(prior_paras) if idx not in matched_prior_indices
        ]

        return SectionDiff(
            section_name=section_name,
            similarity_ratio=ratio,
            drift_score=drift,
            severity=severity,
            added_paragraphs=added[:15],  # Keep top substantive items
            removed_paragraphs=removed[:15],
            modified_paragraphs=modified[:15],
        )

    @classmethod
    def compare_filings(
        cls,
        ticker: str,
        form: str,
        current_text: str,
        prior_text: str,
        current_name: str = "Current Filing",
        prior_name: str = "Prior Filing",
        llm: LLMRouter | None = None,
    ) -> FilingDiffResult:
        """Compare two full filings across all standard sections."""
        curr_sections = SectionExtractor.extract_all(current_text)
        prior_sections = SectionExtractor.extract_all(prior_text)

        all_keys = set(curr_sections.keys()).union(set(prior_sections.keys()))
        if not all_keys:
            # Fall back to full document comparison
            all_keys = {"full_filing_body"}
            curr_sections = {"full_filing_body": current_text}
            prior_sections = {"full_filing_body": prior_text}

        diffs: dict[str, SectionDiff] = {}
        drift_scores: list[float] = []

        for key in sorted(all_keys):
            curr_sec = curr_sections.get(key, "")
            prior_sec = prior_sections.get(key, "")
            diff = cls.compare_sections(curr_sec, prior_sec, section_name=key)
            diffs[key] = diff
            drift_scores.append(diff.drift_score)

        overall_drift = round(sum(drift_scores) / len(drift_scores), 1) if drift_scores else 0.0
        if overall_drift >= 60.0:
            overall_severity = "CRITICAL"
        elif overall_drift >= 35.0:
            overall_severity = "HIGH"
        elif overall_drift >= 15.0:
            overall_severity = "MODERATE"
        else:
            overall_severity = "LOW"

        summary = ""
        if llm:
            try:
                summary = cls._generate_llm_summary(ticker, form, diffs, llm)
            except Exception:
                summary = cls._rule_based_summary(ticker, overall_drift, diffs)
        else:
            summary = cls._rule_based_summary(ticker, overall_drift, diffs)

        return FilingDiffResult(
            ticker=ticker,
            form=form,
            current_filing=current_name,
            prior_filing=prior_name,
            overall_drift_score=overall_drift,
            overall_severity=overall_severity,
            sections=diffs,
            forensic_summary=summary,
        )

    @staticmethod
    def _rule_based_summary(ticker: str, drift: float, diffs: dict[str, SectionDiff]) -> str:
        lines = [
            f"Forensic Language Drift Analysis for {ticker}: Overall Drift Score is {drift}%.",
        ]
        for key, diff in diffs.items():
            lines.append(
                f"- {key}: {diff.severity} severity (drift {diff.drift_score}%). "
                f"{len(diff.added_paragraphs)} new paragraph(s), {len(diff.removed_paragraphs)} removed."
            )
        return "\n".join(lines)

    @staticmethod
    def _generate_llm_summary(
        ticker: str, form: str, diffs: dict[str, SectionDiff], llm: LLMRouter
    ) -> str:
        sample_diffs = []
        for key, d in diffs.items():
            if d.added_paragraphs:
                sample_diffs.append(f"Section {key} Added:\n" + "\n".join(d.added_paragraphs[:3]))
            if d.removed_paragraphs:
                sample_diffs.append(f"Section {key} Removed:\n" + "\n".join(d.removed_paragraphs[:3]))

        context = "\n\n".join(sample_diffs)[:3000]
        prompt = (
            f"Analyze the following textual changes between consecutive {form} filings for {ticker}.\n\n"
            f"Key changes:\n{context}\n\n"
            "Provide a concise 3-point forensic executive summary highlighting what new operational, legal, "
            "or supplier risks management quietly introduced, and what prior disclosures were dropped."
        )
        res = llm.generate(
            prompt,
            "You are a hedge fund forensic accountant specializing in corporate risk factor drift.",
        )
        return res.get("text", "")
