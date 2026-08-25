"""
Strategic Bidding & Pricing — Pydantic schemas.

Typed contracts for game-theoretic pricing (Friedman/Gates), win-probability
curves, Monte Carlo margin simulation, and the strategic pricing summary.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CompetitorProfile(BaseModel):
    """A competitor's estimated bid behavior."""

    name: str
    cost_ratio_mean: float = 1.0   # expected competitor bid / our cost
    cost_ratio_std: float = 0.05   # dispersion of their bid ratio
    weight: float = 1.0            # relative aggressiveness / frequency


class PricingScenario(BaseModel):
    """A candidate markup scenario with its win probability and EV."""

    markup_pct: float = 0.0
    bid_ratio: float = 1.0
    probability_win: float = 0.0
    expected_value: float = 0.0
    combined_score: Optional[float] = None


class WinProbabilityCurvePoint(BaseModel):
    """One point on the win-probability vs markup curve."""

    markup_pct: float
    probability_win: float
    expected_value_pct: float
    combined_score: Optional[float] = None


class MonteCarloResult(BaseModel):
    """Result of the profit Monte Carlo simulation."""

    iterations: int = 0
    p10_net_profit_sar: float = 0.0
    p50_net_profit_sar: float = 0.0
    p90_net_profit_sar: float = 0.0
    var_95_sar: float = 0.0
    mean_net_profit_sar: float = 0.0
    distribution: List[Dict[str, Any]] = Field(default_factory=list)


class StrategicPricingSummary(BaseModel):
    """Aggregate strategic pricing output for state injection."""

    project_id: Optional[int] = None
    optimal_markup_pct: float = 0.0
    optimal_expected_value_pct: float = 0.0
    probability_win_at_optimal: float = 0.0
    friedman_markup_pct: float = 0.0
    gates_markup_pct: float = 0.0
    technical_weight: float = 0.6
    financial_weight: float = 0.4
    curve: List[WinProbabilityCurvePoint] = Field(default_factory=list)
    scenarios: List[PricingScenario] = Field(default_factory=list)
    monte_carlo: MonteCarloResult = Field(default_factory=MonteCarloResult)
