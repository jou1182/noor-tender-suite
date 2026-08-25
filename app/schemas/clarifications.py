"""
Tender Addenda & Clarification — Pydantic schemas.

Typed contracts for addendum ingestion, delta items, clarification RFIs, and
impact summaries.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TenderAddendum(BaseModel):
    """A new tender bulletin/addendum uploaded for processing."""

    addendum_id: str = ""
    title: str = ""
    source_path: str = ""
    document_type: str = "pdf"  # pdf | docx | xlsx
    issued_at: str = ""
    raw_text: str = ""
    parsed_items: List[Dict[str, Any]] = Field(default_factory=list)


class AddendumDeltaItem(BaseModel):
    """A single delta detected between baseline state and the addendum."""

    delta_type: str = "clause"  # clause | boq | deadline | clarifications
    reference: str = ""
    base_value: str = ""
    new_value: str = ""
    severity: str = "LOW"  # HIGH | MEDIUM | LOW
    description: str = ""


class ClarificationRFI(BaseModel):
    """A professional clarification inquiry (RFI) sent to the client."""

    rfi_id: str = ""
    subject: str = ""
    question: str = ""
    reference_clause: str = ""
    status: str = "OPEN"  # OPEN | RESPONDED | WITHDRAWN
    client_response: str = ""
    created_at: str = ""
    impacted_risks: List[str] = Field(default_factory=list)


class AddendumImpactSummary(BaseModel):
    """Aggregate impact of an addendum on the tender state."""

    addendum_id: str = ""
    total_deltas: int = 0
    high_impact_count: int = 0
    medium_impact_count: int = 0
    low_impact_count: int = 0
    total_cost_variance_sar: float = 0.0
    reaudited_items: List[str] = Field(default_factory=list)
    deadline_extension_days: int = 0
    deltas: List[AddendumDeltaItem] = Field(default_factory=list)
