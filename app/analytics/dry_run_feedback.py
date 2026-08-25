"""
Dry Run Feedback Service.

Captures live stakeholder review scores, engineer comments, and feature
requests across the 21-engine architecture during the executive dry run, and
exports a structured evaluation report.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

ENGINE_CATALOG = [
    "RFP Clause Parser",
    "Excel BOQ Parser",
    "PDF Spec Parser",
    "SBC-304 Structural Engine",
    "Cross-Exam Matrix Engine",
    "Value Engineering Engine",
    "Strategic Pricing Engine",
    "Monte Carlo Pricing Simulator",
    "CPM / DCMA Schedule Engine",
    "GIS Logistics Engine",
    "FIDIC Contractual Risk Engine",
    "Cash Flow / S-Curve Engine",
    "ERP Mapping Engine",
    "Pre-Submission Gatekeeper",
    "Digital Signature / Stamping",
    "Proposal PDF/DOCX Generator",
    "Hybrid LLM Router",
    "Semantic Cache Engine",
    "Tender BI / KPI Engine",
    "Digital Twin Simulator",
    "Post-Award Feedback Engine",
]


class DryRunFeedbackService:
    """Aggregate and export stakeholder evaluation feedback."""

    def __init__(self) -> None:
        self.scores: Dict[str, List[float]] = {engine: [] for engine in ENGINE_CATALOG}
        self.comments: List[Dict[str, str]] = []
        self.feature_requests: List[str] = []

    def record_engine_score(self, engine: str, score: float) -> None:
        """Record a 1-10 review score for an engine."""
        if engine not in self.scores:
            self.scores[engine] = []
        self.scores[engine].append(max(1.0, min(10.0, float(score))))

    def add_comment(self, engine: str, author: str, comment: str) -> None:
        self.comments.append({"engine": engine, "author": author, "comment": comment})

    def request_feature(self, feature: str) -> None:
        self.feature_requests.append(feature)

    def average_score(self, engine: str) -> Optional[float]:
        vals = self.scores.get(engine, [])
        return round(sum(vals) / len(vals), 2) if vals else None

    def overall_readiness(self) -> float:
        """Average across all recorded scores; None-scores treated as untested."""
        all_scores = [s for vals in self.scores.values() for s in vals]
        if not all_scores:
            return 0.0
        return round(sum(all_scores) / len(all_scores), 2)

    def export_report(self, path: str = "DRY_RUN_EVALUATION_REPORT.md") -> str:
        """Write the consolidated evaluation report markdown."""
        lines = [
            "# Executive Dry Run — Stakeholder Evaluation Report",
            "",
            f"> Generated {datetime.now(timezone.utc).isoformat()} UTC",
            "",
            "## Engine Readiness Scores",
            "",
            "| Engine | Avg Score (1-10) | Reviews |",
            "|---|---|---|",
        ]
        for engine in ENGINE_CATALOG:
            avg = self.average_score(engine)
            count = len(self.scores.get(engine, []))
            lines.append(f"| {engine} | {avg if avg is not None else '—'} | {count} |")

        lines += ["", "## Overall Readiness Certification", ""]
        readiness = self.overall_readiness()
        cert = "CERTIFIED" if readiness >= 7.0 else "CONDITIONAL" if readiness >= 5.0 else "NOT READY"
        lines.append(f"**Overall readiness: {readiness}/10 — {cert}**")

        if self.comments:
            lines += ["", "## Engineer Comments", ""]
            for c in self.comments:
                lines.append(f"- **{c['author']}** ({c['engine']}): {c['comment']}")

        if self.feature_requests:
            lines += ["", "## Feature Requests", ""]
            for f in self.feature_requests:
                lines.append(f"- {f}")

        content = "\n".join(lines) + "\n"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path
