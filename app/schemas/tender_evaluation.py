"""
Tender Technical Evaluation — schemas & compliance models.

Pydantic models mirroring the deterministic technical evaluation report
produced by the tender evaluation agent.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Per-criterion compliance verdict."""

    COMPLIANT = "COMPLIANT"
    COMPLIANT_WITH_DEVIATION = "COMPLIANT_WITH_DEVIATION"
    NON_COMPLIANT = "NON_COMPLIANT"


class EvaluationCriterion(BaseModel):
    """A weighted evaluation criterion with its computed score."""

    code: str
    name: str
    weight: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=100.0)
    weighted_score: float = Field(ge=0.0, le=100.0)
    status: ComplianceStatus
    remarks: str = ""


class TenderRiskItem(BaseModel):
    """A risk surfaced during the technical evaluation."""

    risk_id: str
    category: str
    description: str
    severity: str  # CRITICAL / HIGH / MEDIUM / LOW
    mitigation: str = ""


class TechnicalEvaluationReport(BaseModel):
    """Aggregate weighted technical evaluation report."""

    tender_id: int = 0
    overall_score: float = Field(ge=0.0, le=100.0)
    compliance_score: float = Field(ge=0.0, le=100.0)
    criteria: List[EvaluationCriterion] = Field(default_factory=list)
    risks: List[TenderRiskItem] = Field(default_factory=list)
    pass_fail: bool
    summary: str = ""


class TechnicalEvaluationScorecard(TechnicalEvaluationReport):
    """Alias for backwards compatibility with test imports."""
    pass