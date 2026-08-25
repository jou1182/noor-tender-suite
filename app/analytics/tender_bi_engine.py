"""
Tender Business Intelligence Engine.

Aggregates historical tender data (synthetic rows or SQLAlchemy rows) into
portfolio-wide executive KPIs, sector performance metrics, and client risk
metrics.
"""

from typing import Any, Dict, List, Optional

from app.schemas.analytics_bi import (
    ClientRiskMetric,
    ExecutiveKPISummary,
    SectorPerformanceMetric,
    TenderPortfolioReport,
)

SECTOR_KEYWORDS = {
    "Infrastructure": ["infrastructure", "roads", "bridge", "highway"],
    "Water Transmission": ["water", "pipeline", "transmission", "sewer", "desalination"],
    "Housing": ["housing", "residential", "villa", "district"],
    "Transportation": ["transport", "metro", "rail", "airport", "logistics"],
}


def _classify_sector(title: str) -> str:
    lowered = title.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return sector
    return "General Civil"


def _tender_outcome(row: Dict[str, Any]) -> str:
    """Derive WON/LOST from a tender row's outcome/status."""
    outcome = str(row.get("outcome", row.get("award_status", ""))).upper()
    if "WON" in outcome or outcome == "AWARDED":
        return "WON"
    if "LOST" in outcome or "DISQUAL" in outcome or "CANCELLED" in outcome:
        return "LOST"
    status = str(row.get("status", "")).lower()
    if status in ("awarded", "won"):
        return "WON"
    return "UNKNOWN"


class TenderBIEngine:
    """Deterministic portfolio KPI aggregation."""

    @staticmethod
    def aggregate(rows: List[Dict[str, Any]]) -> TenderPortfolioReport:
        """Aggregate tender rows into the full portfolio report."""
        total_value = 0.0
        ve_savings = 0.0
        markup_sum = 0.0
        markup_count = 0
        turnaround_sum = 0.0
        turnaround_count = 0
        won = 0
        lost = 0

        sectors: Dict[str, List[Dict[str, Any]]] = {}
        clients: Dict[str, List[Dict[str, Any]]] = {}

        for row in rows:
            title = str(row.get("title", row.get("name", "Untitled")))
            value = float(row.get("contract_value_sar", row.get("evaluated_value_sar", 0)) or 0)
            total_value += value
            ve_savings += float(row.get("ve_net_savings_sar", 0) or 0)

            markup = row.get("markup_pct")
            if markup is not None:
                markup_sum += float(markup)
                markup_count += 1
            turnaround = row.get("bid_prep_days")
            if turnaround is not None:
                turnaround_sum += float(turnaround)
                turnaround_count += 1

            outcome = _tender_outcome(row)
            if outcome == "WON":
                won += 1
            elif outcome == "LOST":
                lost += 1

            sector = _classify_sector(title)
            sectors.setdefault(sector, []).append(row)

            client = str(row.get("client_name", "Unknown Client"))
            clients.setdefault(client, []).append(row)

        sector_metrics = [
            TenderBIEngine._sector_metric(sector, sector_rows) for sector, sector_rows in sectors.items()
        ]
        sector_metrics.sort(key=lambda s: s.total_value_sar, reverse=True)

        client_metrics = [
            TenderBIEngine._client_metric(client, client_rows) for client, client_rows in clients.items()
        ]
        client_metrics.sort(key=lambda c: c.total_value_sar, reverse=True)

        decided = won + lost
        kpi = ExecutiveKPISummary(
            total_active_tenders=len(rows),
            win_rate_pct=round(won / decided * 100, 2) if decided else 0.0,
            total_pipeline_value_sar=round(total_value, 2),
            average_markup_pct=round(markup_sum / markup_count, 2) if markup_count else 0.0,
            total_ve_net_savings_sar=round(ve_savings, 2),
            bid_prep_turnaround_days=round(turnaround_sum / turnaround_count, 2) if turnaround_count else 0.0,
            won_tenders=won,
            lost_tenders=lost,
        )

        return TenderPortfolioReport(
            kpi=kpi,
            sectors=sector_metrics,
            clients=client_metrics,
            generated_at=__import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        )

    @staticmethod
    def _sector_metric(sector: str, rows: List[Dict[str, Any]]) -> SectorPerformanceMetric:
        total_value = sum(float(r.get("contract_value_sar", r.get("evaluated_value_sar", 0)) or 0) for r in rows)
        won = sum(1 for r in rows if _tender_outcome(r) == "WON")
        decided = sum(1 for r in rows if _tender_outcome(r) in ("WON", "LOST"))
        markup_vals = [float(r["markup_pct"]) for r in rows if r.get("markup_pct") is not None]
        return SectorPerformanceMetric(
            sector=sector,
            total_value_sar=round(total_value, 2),
            tender_count=len(rows),
            won_count=won,
            win_rate_pct=round(won / decided * 100, 2) if decided else 0.0,
            avg_markup_pct=round(sum(markup_vals) / len(markup_vals), 2) if markup_vals else 0.0,
        )

    @staticmethod
    def _client_metric(client: str, rows: List[Dict[str, Any]]) -> ClientRiskMetric:
        total_value = sum(float(r.get("contract_value_sar", r.get("evaluated_value_sar", 0)) or 0) for r in rows)
        won = sum(1 for r in rows if _tender_outcome(r) == "WON")
        decided = sum(1 for r in rows if _tender_outcome(r) in ("WON", "LOST"))
        scores = [float(r["technical_score"]) for r in rows if r.get("technical_score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        win_rate = won / decided * 100 if decided else 0.0
        risk = "HIGH" if win_rate < 40 else ("MEDIUM" if win_rate < 60 else "LOW")
        return ClientRiskMetric(
            client_name=client,
            total_value_sar=round(total_value, 2),
            win_rate_pct=round(win_rate, 2),
            avg_technical_score=round(avg_score, 2),
            risk_level=risk,
        )
