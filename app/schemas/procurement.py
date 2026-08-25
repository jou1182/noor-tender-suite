"""
Procurement — Pydantic schemas.

Typed contracts for the vendor RFQ lifecycle: package generation, quotation
submissions, normalized bids, bid tabulation, and procurement summaries.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RFQPackage(BaseModel):
    """A trade package grouping BOQ items for vendor solicitation."""

    package_code: str
    trade_package: str
    item_count: int = 0
    estimated_value_sar: float = 0.0
    items: List[Dict[str, Any]] = Field(default_factory=list)
    magic_link_token: str = ""
    token_expires_at: str = ""


class TechnicalGateResult(BaseModel):
    """Deterministic technical gating verdict for a vendor submittal."""

    passed: bool
    gate: str = ""  # e.g. SBC-304 §5.2, ASTM C39
    submitted_value: float = 0.0
    required_value: float = 0.0
    reason: str = ""


class VendorQuotationSubmission(BaseModel):
    """Raw quotation uploaded by an external vendor via magic link."""

    token: str
    vendor_name: str
    package_code: str
    items: List[Dict[str, Any]] = Field(default_factory=list)  # [{item_code, description, unit_rate_sar, qty}]
    technical_data: Dict[str, Any] = Field(default_factory=dict)  # {fc_mpa, fy_mpa, cert_refs, lead_time_days}
    submitted_at: str = ""


class NormalizedBidItem(BaseModel):
    """One BOQ item from a vendor quotation after normalization."""

    item_code: str
    description: str
    quantity: float = 0.0
    unit_rate_sar: float = 0.0
    total_sar: float = 0.0
    baseline_rate_sar: float = 0.0
    variance_pct: float = 0.0
    technical_gate: TechnicalGateResult = Field(default_factory=TechnicalGateResult)


class BidTabulationRow(BaseModel):
    """A ranked vendor row in the comparative bid tabulation matrix."""

    rank: int = 0
    vendor_name: str
    package_code: str
    raw_bid_sar: float = 0.0
    normalized_bid_sar: float = 0.0
    variance_to_budget_pct: float = 0.0
    scope_coverage_pct: float = 100.0
    technical_compliant: bool = True
    lead_time_days: Optional[float] = None
    lead_time_risk: bool = False
    is_optimal: bool = False
    rejection_reason: Optional[str] = None


class ProcurementSummary(BaseModel):
    """Aggregate procurement state for state injection."""

    package_count: int = 0
    quotation_count: int = 0
    compliant_quotations: int = 0
    rejected_quotations: int = 0
    total_estimated_value_sar: float = 0.0
    best_normalized_bid_sar: float = 0.0
    projected_savings_sar: float = 0.0
    bid_tabulation: List[BidTabulationRow] = Field(default_factory=list)
