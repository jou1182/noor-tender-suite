"""
ERP & Cost Estimation Sync — Pydantic schemas.

Typed contracts for the Cost Breakdown Structure (CBS), SAP OData payloads,
Oracle Unifier packages, and export summaries.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CBSItemBreakdown(BaseModel):
    """A single BOQ line mapped to the 4-tier Cost Breakdown Structure."""

    item_code: str = ""
    description: str
    unit: str = ""
    quantity: float = 0.0
    unit_rate_sar: float = 0.0
    total_amount_sar: float = 0.0

    labor_pct: float = 0.0    # L
    plant_pct: float = 0.0    # P
    material_pct: float = 0.0  # M
    subcontractor_pct: float = 0.0  # S

    labor_amount_sar: float = 0.0
    plant_amount_sar: float = 0.0
    material_amount_sar: float = 0.0
    subcontractor_amount_sar: float = 0.0

    coa_code: str = ""
    coa_category: str = ""
    sbc_status: str = "COMPLIANT"
    ve_alternative: Optional[str] = None


class SAPConditionRecord(BaseModel):
    """SAP S/4HANA OData pricing condition record."""

    condition_type: str = "PR00"
    pricing_scale: str = "0"
    condition_value: float = 0.0
    currency: str = "SAR"
    condition_unit: str = "EA"
    rate_unit: str = "1"
    valid_from: str = ""
    valid_to: str = ""
    material_number: str = ""


class ERPPayloadContainer(BaseModel):
    """Container for all export targets."""

    target_system: str = "ALL"
    cbs_items: List[CBSItemBreakdown] = Field(default_factory=list)
    sap_payloads: Dict[str, Any] = Field(default_factory=dict)
    oracle_payloads: Dict[str, Any] = Field(default_factory=dict)
    excel_payloads: Dict[str, Any] = Field(default_factory=dict)
    totals: Dict[str, float] = Field(default_factory=dict)


class ERPExportSummary(BaseModel):
    """Summary of the ERP export operation."""

    project_id: Optional[int] = None
    target_system: str = "ALL"
    cbs_item_count: int = 0
    total_tender_value_sar: float = 0.0
    ve_net_savings_sar: float = 0.0
    sap_conditions_generated: int = 0
    oracle_rows_generated: int = 0
    artifacts: Dict[str, str] = Field(default_factory=dict)  # target -> path/url
