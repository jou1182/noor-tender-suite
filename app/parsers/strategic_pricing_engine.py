"""
Strategic Pricing Engine.

Implements game-theoretic bid pricing:

  - Friedman model: P(win) = product over competitors of P(our bid > their bid),
    each competitor's bid modeled as a normal distribution around their
    cost-ratio.
  - Gates model: P(win) = 1 / (1 + sum of competitor odds-ratios), a widely
    used variant for multi-competitor tenders.
  - EV = markup% * P(win), maximized over a continuous markup range to find the
    optimal markup m*.
  - Combined-score integration: when the client award uses a technical weight
    (Wt) and financial weight (Wf), the effective win probability is blended
    with the technical-score probability.
"""

import math
from typing import Any, Dict, List, Optional

from app.schemas.pricing import (
    CompetitorProfile,
    PricingScenario,
    StrategicPricingSummary,
    WinProbabilityCurvePoint,
)

DEFAULT_MARKUP_RANGE = (3.0, 25.0)
MARKUP_STEP = 0.5


class StrategicPricingEngine:
    """Game-theoretic optimal markup solver (Friedman & Gates)."""

    @staticmethod
    def _normal_cdf(x: float, mean: float = 1.0, std: float = 0.05) -> float:
        """P(X <= x) for a normal distribution using the error function."""
        if std <= 0:
            return 1.0 if x >= mean else 0.0
        return 0.5 * (1.0 + math.erf((x - mean) / (std * math.sqrt(2.0))))

    @staticmethod
    def friedman_probability_win(bid_ratio: float, competitors: List[CompetitorProfile]) -> float:
        """
        P(win) = product_i P(our bid_ratio > competitor_i bid ratio).

        Our bid wins against competitor i when our bid ratio exceeds their
        sampled cost ratio.
        """
        if not competitors:
            return 1.0
        prob = 1.0
        for comp in competitors:
            # P(our ratio > theirs) = 1 - CDF(theirs at our ratio)
            p_beat = 1.0 - StrategicPricingEngine._normal_cdf(
                bid_ratio, mean=comp.cost_ratio_mean, std=comp.cost_ratio_std
            )
            prob *= max(0.0, min(1.0, p_beat))
        return prob

    @staticmethod
    def gates_probability_win(bid_ratio: float, competitors: List[CompetitorProfile]) -> float:
        """
        P(win) = 1 / (1 + sum_i [ P(their ratio > our ratio) / P(our ratio > their ratio) ])
        """
        if not competitors:
            return 1.0
        odds_sum = 0.0
        for comp in competitors:
            p_they_beat = StrategicPricingEngine._normal_cdf(
                bid_ratio, mean=comp.cost_ratio_mean, std=comp.cost_ratio_std
            )
            p_we_beat = 1.0 - p_they_beat
            if p_we_beat <= 0:
                return 0.0
            odds_sum += p_they_beat / p_we_beat
        return 1.0 / (1.0 + odds_sum)

    @staticmethod
    def combined_win_probability(
        price_win: float,
        technical_score: float,
        technical_weight: float,
        financial_weight: float,
        min_technical_gate: float = 60.0,
    ) -> float:
        """
        Blended award probability when the client uses a combined score.

        A low technical score caps the effective win probability; the financial
        (price) dimension contributes via price_win scaled by financial weight.
        """
        if technical_score < min_technical_gate:
            return 0.0
        technical_prob = technical_score / 100.0
        return financial_weight * price_win + technical_weight * technical_prob

    @staticmethod
    def optimize(
        cost_basis_sar: float,
        competitors: List[CompetitorProfile],
        technical_score: float = 85.0,
        technical_weight: float = 0.6,
        financial_weight: float = 0.4,
        markup_min: float = DEFAULT_MARKUP_RANGE[0],
        markup_max: float = DEFAULT_MARKUP_RANGE[1],
        model: str = "friedman",
    ) -> Dict[str, Any]:
        """
        Solve for the optimal markup m* maximizing EV over the markup range.

        Returns a dict with the optimal markup, win probability, EV, and the
        full curve.
        """
        p_win_fn = (
            StrategicPricingEngine.friedman_probability_win
            if model == "friedman"
            else StrategicPricingEngine.gates_probability_win
        )

        curve: List[WinProbabilityCurvePoint] = []
        scenarios: List[PricingScenario] = []

        best: Optional[WinProbabilityCurvePoint] = None
        markup = markup_min
        while markup <= markup_max + 1e-9:
            bid_ratio = 1.0 + markup / 100.0
            price_win = p_win_fn(bid_ratio, competitors)
            combined = StrategicPricingEngine.combined_win_probability(
                price_win, technical_score, technical_weight, financial_weight
            )
            ev = markup * combined

            curve.append(
                WinProbabilityCurvePoint(
                    markup_pct=round(markup, 2),
                    probability_win=round(combined, 4),
                    expected_value_pct=round(ev, 4),
                    combined_score=round(
                        technical_weight * technical_score + financial_weight * (100.0 - markup),
                        2,
                    ),
                )
            )
            scenarios.append(
                PricingScenario(
                    markup_pct=round(markup, 2),
                    bid_ratio=round(bid_ratio, 4),
                    probability_win=round(combined, 4),
                    expected_value=round(ev, 4),
                    combined_score=round(
                        technical_weight * technical_score + financial_weight * (100.0 - markup), 2
                    ),
                )
            )
            if best is None or ev > best.expected_value_pct:
                best = curve[-1]
            markup += MARKUP_STEP

        if best is None:
            best = WinProbabilityCurvePoint(markup_pct=markup_min, probability_win=0.0, expected_value_pct=0.0)

        return {
            "optimal_markup_pct": best.markup_pct,
            "optimal_expected_value_pct": best.expected_value_pct,
            "probability_win_at_optimal": best.probability_win,
            "optimal_bid_sar": round(cost_basis_sar * (1 + best.markup_pct / 100.0), 2),
            "curve": curve,
            "scenarios": scenarios,
        }

    @staticmethod
    def build_summary(
        project_id: Optional[int],
        cost_basis_sar: float,
        competitors: List[CompetitorProfile],
        technical_score: float = 85.0,
        technical_weight: float = 0.6,
        financial_weight: float = 0.4,
    ) -> StrategicPricingSummary:
        """Convenience: compute both models and assemble a StrategicPricingSummary."""
        friedman = StrategicPricingEngine.optimize(
            cost_basis_sar, competitors, technical_score, technical_weight, financial_weight, model="friedman"
        )
        gates = StrategicPricingEngine.optimize(
            cost_basis_sar, competitors, technical_score, technical_weight, financial_weight, model="gates"
        )
        return StrategicPricingSummary(
            project_id=project_id,
            optimal_markup_pct=friedman["optimal_markup_pct"],
            optimal_expected_value_pct=friedman["optimal_expected_value_pct"],
            probability_win_at_optimal=friedman["probability_win_at_optimal"],
            friedman_markup_pct=friedman["optimal_markup_pct"],
            gates_markup_pct=gates["optimal_markup_pct"],
            technical_weight=technical_weight,
            financial_weight=financial_weight,
            curve=friedman["curve"],
            scenarios=friedman["scenarios"],
        )
