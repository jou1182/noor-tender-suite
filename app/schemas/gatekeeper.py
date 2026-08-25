"""
Pre-Submission Gatekeeper — Pydantic schemas.

Typed contracts for the QA checklist, audit categories, the pre-submission
report, and the final submission clearance certificate.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QACheckItem(BaseModel):
    """A single gatekeeper QA check."""

    check_id: str
    description: str
    passed: bool
    severity: str = "LOW"  # LOW | MEDIUM | HIGH | FATAL_FLAW
    detail: str = ""


class QAAuditCategory(BaseModel):
    """A category of QA checks with aggregate status."""

    category: str  # SBC_STRUCTURAL | ARITHMETIC | ATTACHMENTS | CONTRACTUAL | PROPOSAL
    checks: List[QACheckItem] = Field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    fatal_count: int = 0
    fully_passed: bool = True


class PreSubmissionReport(BaseModel):
    """The full pre-submission audit report."""

    project_id: Optional[int] = None
    categories: List[QAAuditCategory] = Field(default_factory=list)
    bid_readiness_score: float = 0.0
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    fatal_flaws: List[QACheckItem] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    is_cleared_for_submission: bool = False


class SubmissionClearanceCertificate(BaseModel):
    """Cryptographic clearance certificate issued on full QA pass."""

    project_id: Optional[int] = None
    clearance_checksum: str = ""
    bid_readiness_score: float = 0.0
    authorized_by: str = ""
    authorized_at: str = ""
    valid_until: str = ""
    signed_payload: Dict[str, Any] = Field(default_factory=dict)
