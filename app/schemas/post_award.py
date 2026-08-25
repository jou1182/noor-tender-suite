"""
Post-Award Analytics & Feedback — Pydantic schemas.

Typed contracts for award outcome ingestion, competitor bid entries,
post-award variance reporting, and engine calibration updates.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CompetitorBidEntry(BaseModel):
    """One ranked competitor bid from the award notice."""

    rank: int = 0
    competitor_name: str
    bid_amount_sar: float = 0.0
    technical_score: Optional[float] = None  # 0-100 if disclosed


class TenderAwardRecord(BaseModel):
    """Parsed award outcome for a tender."""

    project_id: Optional[int] = None
    tender_reference: str = ""
    award_status: str = "LOST"  # WON | LOST | DISQUALIFIED | CANCELLED
    awarded_contractor: str = ""
    awarded_amount_sar: float = 0.0
    our_submission_amount_sar: float = 0.0
    our_technical_score: Optional[float] = None
    ranked_bids: List[CompetitorBidEntry] = Field(default_factory=list)
    source_text: str = ""


class PostAwardVarianceReport(BaseModel):
    """Variance metrics computed after award outcome ingestion."""

    project_id: Optional[int] = None
    bid_to_winning_delta_pct: float = 0.0
    technical_ranking_delta: Optional[float] = None
    price_position_rank: Optional[int] = None
    outcome: str = ""
    calibration_applied: bool = False


class EngineCalibrationUpdate(BaseModel):
    """What the feedback learning engine changed after an outcome."""

    competitor_updates: List[Dict[str, Any]] = Field(default_factory=list)
    ve_confidence_updates: List[Dict[str, Any]] = Field(default_factory=list)
    pgvector_tags_applied: List[str] = Field(default_factory=list)
    knowledge_base_entry_id: Optional[str] = None
