"""
Tender Business Intelligence — Pydantic schemas.

Typed contracts for executive KPI summaries, sector performance metrics,
client risk metrics, and the full portfolio report.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutiveKPISummary(BaseModel):
    """Core executive KPI aggregate."""

    total_active_tenders: int = 0
    win_rate_pct: float = 0.0
    total_pipeline_value_sar: float = 0.0
    average_markup_pct: float = 0.0
    total_ve_net_savings_sar: float = 0.0
    bid_prep_turnaround_days: float = 0.0
    won_tenders: int = 0
    lost_tenders: int = 0
    deltas: Dict[str, float] = Field(default_factory=dict)  # vs prior quarter


class SectorPerformanceMetric(BaseModel):
    """Pipeline volume + win rate for one engineering sector."""

    sector: str
    total_value_sar: float = 0.0
    tender_count: int = 0
    won_count: int = 0
    win_rate_pct: float = 0.0
    avg_markup_pct: float = 0.0


class ClientRiskMetric(BaseModel):
    """Per-client risk / performance summary."""

    client_name: str
    total_value_sar: float = 0.0
    win_rate_pct: float = 0.0
    avg_technical_score: float = 0.0
    risk_level: str = "LOW"  # LOW | MEDIUM | HIGH


class TenderPortfolioReport(BaseModel):
    """Full portfolio BI report."""

    kpi: ExecutiveKPISummary = Field(default_factory=ExecutiveKPISummary)
    sectors: List[SectorPerformanceMetric] = Field(default_factory=list)
    clients: List[ClientRiskMetric] = Field(default_factory=list)
    generated_at: str = ""
