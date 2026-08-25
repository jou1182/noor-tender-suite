"""
Proposal Evaluation — Pydantic schemas.

Typed contracts for the bid-vs-RFP evaluation pipeline: mandatory RFP clause
mandates, proposal section matches, compliance gaps, and the simulated Owner
technical scorecard.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RFPClauseMandate(BaseModel):
    """A structured mandatory requirement extracted from the Owner RFP."""

    clause_id: str
    category: str = "TECHNICAL"  # TECHNICAL | COMMERCIAL | LEGAL | ADMIN
    requirement: str
    keywords: List[str] = Field(default_factory=list)
    weight: float = 1.0
    required_attachment: Optional[str] = None


class ProposalSectionMatch(BaseModel):
    """Cross-match result between an RFP mandate and a proposal section."""

    clause_id: str
    section_title: str
    similarity: float = 0.0
    addressed: bool = False
    depth: str = "NONE"  # NONE | PARTIAL | FULL
    matched_keywords: List[str] = Field(default_factory=list)


class ComplianceGapItem(BaseModel):
    """A detected compliance gap in the team's draft proposal."""

    clause_id: str
    gap_type: str = "UNADDRESSED"  # UNRESOLVED | MISSING_ATTACHMENT | AMBIGUOUS
    description: str = ""
    penalty_points: float = 0.0


class TechnicalEvaluationScorecard(BaseModel):
    """Simulated Owner technical evaluation score (0-100)."""

    total_score: float = 0.0
    max_points: float = 100.0
    clauses_checked: int = 0
    clauses_addressed: int = 0
    gaps: List[ComplianceGapItem] = Field(default_factory=list)
    matches: List[ProposalSectionMatch] = Field(default_factory=list)
    summary: str = ""
