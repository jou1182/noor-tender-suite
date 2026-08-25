"""
Bid-vs-RFP Proposal Evaluator.

Deconstructs the Owner RFP into structured mandatory requirements, ingests the
team's draft proposal (text/sections), cross-matches each mandate against
proposal sections using deterministic keyword + similarity scoring, and
computes a simulated Owner technical score (0-100) with a compliance gap matrix.
"""

import re
from typing import Any, Dict, List, Optional

from app.schemas.proposal_evaluation import (
    ComplianceGapItem,
    ProposalSectionMatch,
    RFPClauseMandate,
    TechnicalEvaluationScorecard,
)

DEFAULT_MANDATES = [
    RFPClauseMandate(
        clause_id="M-1", category="TECHNICAL", requirement="Provide a project quality assurance plan.",
        keywords=["quality", "qa", "plan", "assurance", "inspection"],
        weight=10.0, required_attachment="quality_plan",
    ),
    RFPClauseMandate(
        clause_id="M-2", category="TECHNICAL",
        requirement="Submit project manager CV with 10+ years of relevant experience.",
        keywords=["project manager", "experience", "cv", "years"],
        weight=10.0, required_attachment="pm_cv",
    ),
    RFPClauseMandate(
        clause_id="M-3", category="TECHNICAL",
        requirement="Method statement for concrete works complying with SBC-304.",
        keywords=["method statement", "concrete", "sbc", "pouring", "curing"],
        weight=15.0,
    ),
    RFPClauseMandate(
        clause_id="M-4", category="LEGAL",
        requirement="Commercial registration and contractor classification certificates.",
        keywords=["commercial registration", "classification", "certificate"],
        weight=5.0, required_attachment="commercial_registration",
    ),
    RFPClauseMandate(
        clause_id="M-5", category="TECHNICAL",
        requirement="Construction schedule demonstrating completion within 24 months.",
        keywords=["schedule", "programme", "months", "completion", "baseline"],
        weight=10.0,
    ),
]


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _semantic_overlap(mandate_keywords: List[str], section_text: str) -> float:
    """Fraction of mandate keywords present in a proposal section."""
    section_tokens = _tokens(section_text)
    if not mandate_keywords:
        return 0.0
    hits = sum(1 for kw in mandate_keywords if any(
        kw in token or token in kw for token in section_tokens
    ))
    return hits / len(mandate_keywords)


class BidVsRFPEvaluator:
    """Deterministic bid-vs-RFP cross-matching and scoring engine."""

    def __init__(self, mandates: List[RFPClauseMandate] | None = None) -> None:
        self.mandates = mandates if mandates is not None else DEFAULT_MANDATES

    @staticmethod
    def parse_mandates(rfp_text: str) -> List[RFPClauseMandate]:
        """Extract structured mandates from raw RFP text (line-based heuristics)."""
        mandates: List[RFPClauseMandate] = []
        idx = 0
        for line in rfp_text.splitlines():
            line = line.strip()
            if not line or not re.match(r"^(?:\d+\.?|M-\d+|Clause)", line, re.IGNORECASE):
                continue
            idx += 1
            keywords = [w for w in re.findall(r"[a-z]{4,}", line.lower())][:8]
            category = "LEGAL" if re.search(r"certificat|registration|guarantee|legal", line, re.I) else "TECHNICAL"
            mandates.append(
                RFPClauseMandate(
                    clause_id=f"RFP-{idx}", category=category, requirement=line,
                    keywords=keywords or ["requirement"], weight=10.0,
                )
            )
        return mandates

    @staticmethod
    def parse_proposal_sections(proposal_text: str) -> List[Dict[str, str]]:
        """Split the draft proposal into titled sections (heading stays with content)."""
        heading_boundary = re.compile(
            r"(?m)(?=^(?:#{1,3}\s+|(?:\d+\.\s*)?[A-Z][A-Za-z &\-\/]{4,}:))"
        )
        parts = [p.strip() for p in heading_boundary.split(proposal_text) if p and p.strip()]
        if len(parts) < 2:
            return [{"title": "Full Proposal", "text": proposal_text}]
        sections = []
        for part in parts:
            lines = part.splitlines()
            title = (lines[0] if lines else part)[:60].strip()
            sections.append({"title": title, "text": part})
        return sections

    @staticmethod
    def _required_years(mandate: RFPClauseMandate) -> Optional[int]:
        match = re.search(r"(\d+)\+?\s*years", mandate.requirement, re.IGNORECASE)
        return int(match.group(1)) if match else None

    @staticmethod
    def _claimed_max_years(sections: List[Dict[str, str]]) -> Optional[int]:
        best: Optional[int] = None
        for section in sections:
            for match in re.finditer(r"(\d+)\+?\s*years", section.get("text", ""), re.IGNORECASE):
                years = int(match.group(1))
                if best is None or years > best:
                    best = years
        return best

    def evaluate(self, proposal_text: str) -> TechnicalEvaluationScorecard:
        """Cross-match every mandate against the proposal and score the bid."""
        sections = BidVsRFPEvaluator.parse_proposal_sections(proposal_text)
        matches: List[ProposalSectionMatch] = []
        gaps: List[ComplianceGapItem] = []
        total_weight = sum(m.weight for m in self.mandates) or 1.0
        earned = 0.0
        addressed_count = 0

        for mandate in self.mandates:
            best_sim = 0.0
            best_section = ""
            best_hits: List[str] = []
            for section in sections:
                sim = _semantic_overlap(mandate.keywords, section["text"])
                if sim > best_sim:
                    best_sim = sim
                    best_section = section["title"]
                    best_hits = [kw for kw in mandate.keywords if kw in _tokens(section["text"])]

            addressed = best_sim >= 0.5
            depth = "FULL" if best_sim >= 0.8 else ("PARTIAL" if addressed else "NONE")

            # Experience gate: claimed years must meet the mandated minimum.
            required_years = BidVsRFPEvaluator._required_years(mandate)
            if required_years is not None:
                claimed = BidVsRFPEvaluator._claimed_max_years(sections)
                if claimed is None or claimed < required_years:
                    addressed = False
                    depth = "NONE"
                    best_sim = min(best_sim, 0.2)

            matches.append(
                ProposalSectionMatch(
                    clause_id=mandate.clause_id,
                    section_title=best_section or "—",
                    similarity=round(best_sim, 3),
                    addressed=addressed,
                    depth=depth,
                    matched_keywords=best_hits,
                )
            )

            if addressed:
                addressed_count += 1
                earned += mandate.weight * (1.0 if depth == "FULL" else 0.6)
            else:
                gap_type = "MISSING_ATTACHMENT" if mandate.required_attachment else "UNADDRESSED"
                gaps.append(
                    ComplianceGapItem(
                        clause_id=mandate.clause_id,
                        gap_type=gap_type,
                        description=(
                            f"Missing attachment '{mandate.required_attachment}' required by {mandate.clause_id}."
                            if mandate.required_attachment
                            else f"Requirement {mandate.clause_id} not addressed: {mandate.requirement[:80]}"
                        ),
                        penalty_points=round(mandate.weight, 2),
                    )
                )

        score = round(earned / total_weight * 100.0, 2)
        return TechnicalEvaluationScorecard(
            total_score=score,
            clauses_checked=len(self.mandates),
            clauses_addressed=addressed_count,
            gaps=gaps,
            matches=matches,
            summary=(
                f"Simulated Owner technical score {score}/100 — "
                f"{addressed_count}/{len(self.mandates)} mandates addressed, "
                f"{len(gaps)} gaps flagged."
            ),
        )
