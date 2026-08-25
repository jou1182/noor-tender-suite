"""
Value Engineering Optimizer.

Matches BOQ line items against an approved material-substitution catalog,
computes net cost deltas (SAR), construction speed indexes, and enforces
SBC 304 structural compliance via the Sbc304Engine.

Two entry points:

  - ``generate_ve_matrix(boq_items) -> List[VEOpportunityCard]``
      Production API returning structured opportunity cards (mirrored by the
      frontend ``frontend/src/types/ve.ts``). Non-compliant substitutions are
      BLOCKED with ``technical_justification`` prefixed by
      "NON-COMPLIANT with SBC 304:".
  - ``evaluate_boq(boq_items) -> dict``
      Legacy VEData-compatible aggregation (kept for backward compatibility).
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.parsers.sbc_standards_engine import ExposureClass, PlacementContext, Sbc304Engine


class ConcreteSource(str, Enum):
    """Approved concrete material sources / substitutions."""

    CONC_SRC_C35_OPC = "CONC_SRC_C35_OPC"
    CONC_SRC_C35_GGBFS = "CONC_SRC_C35_GGBFS"
    CONC_SRC_LEAN_LOWCEMENT = "CONC_SRC_LEAN_LOWCEMENT"


class VEOpportunityCard(BaseModel):
    """Pydantic model strictly mirrored by ``frontend/src/types/ve.ts``."""

    boq_item: str
    original_spec: str
    proposed_alternative: str
    unit_delta_sar: float = 0.0
    net_savings_sar: float = 0.0
    speed_index_gain_percent: float = 0.0
    sbc_status: str = "COMPLIANT"  # "COMPLIANT" | "BLOCKED"
    is_recommended: bool = True
    technical_justification: str = ""
    sbc_304_references: List[str] = Field(default_factory=list)
    is_accepted: bool = False


class VESummary(BaseModel):
    """Aggregated value-engineering summary."""

    total_potential_savings_sar: float = 0.0
    net_schedule_acceleration_percent: float = 0.0
    total_sbc_verified_proposals: int = 0
    total_blocked: int = 0


# SBC-validated concrete substitution catalog.
CONC_CATALOG: Dict[ConcreteSource, Dict[str, Any]] = {
    ConcreteSource.CONC_SRC_C35_GGBFS: {
        "proposed_alternative": "C35 GGBFS 50% (Slag-Blended Cement)",
        "material": {"fc": 35.0, "wc": 0.40, "fy": 420.0, "cover": 75.0},
        "cost_diff_percent": -8.0,
        "speed_index_gain_percent": 12.0,
        "references": ["SBC 304 Table 4.3.1", "SBC 304 Sec 7.7", "SBC 304 §5.3"],
        "justification": (
            "Slag replacement lowers unit cost and heat of hydration while meeting "
            "SBC 304 strength (f'c 35 MPa) and durability (w/c 0.40) requirements."
        ),
    },
    ConcreteSource.CONC_SRC_LEAN_LOWCEMENT: {
        "proposed_alternative": "Lean Concrete (Low-Cement Fill)",
        "material": {"fc": 18.0, "wc": 0.60, "fy": 300.0, "cover": 30.0},
        "cost_diff_percent": -35.0,
        "speed_index_gain_percent": 5.0,
        "references": ["SBC 304 Table 4.3.1"],
        "justification": (
            "Cheaper lean concrete — INVALID: fails SBC 304 minimum structural properties."
        ),
    },
}


class ValueEngineeringEngine:
    # Legacy demonstration catalog (kept for evaluate_boq backward compatibility).
    LEGACY_CATALOG: Dict[str, Dict[str, Any]] = {
        "Standard Portland Cement": {
            "substitution": "Pozzolanic Cement (Type IP)",
            "cost_diff_percent": -12.5,
            "speed_index": 1.05,
            "material": {"fc": 45.0, "wc": 0.40, "cover": 40.0},
            "justification": (
                "Reduces heat of hydration and lowers unit cost while maintaining SBC-304 "
                "structural strength requirements (f'c 45 MPa, w/c 0.40)."
            ),
        },
        "Grade 60 Steel Rebar": {
            "substitution": "High-Yield Grade 80 Rebar",
            "cost_diff_percent": -8.0,
            "speed_index": 1.085,
            "material": {"fy": 550.0},
            "justification": (
                "Higher yield strength (fy 550 MPa) reduces tonnage and accelerates "
                "steel fixing (SBC 304 §3.5.3)."
            ),
        },
        "Alternative Sulphate-Resisting Mix": {
            "substitution": "Reduced-Cement Blend (Non-Compliant)",
            "cost_diff_percent": -22.0,
            "speed_index": 1.02,
            "material": {"fc": 20.0, "wc": 0.55, "cover": 15.0},
            "justification": "Proposed for cost reduction; INVALID under SBC 304.",
        },
    }

    # ---- Production API (new directive) ----

    @staticmethod
    def generate_ve_matrix(boq_items: List[Dict[str, Any]]) -> List[VEOpportunityCard]:
        """Evaluate every BOQ line item against the SBC-validated catalog."""
        return [ValueEngineeringEngine._evaluate_item(item) for item in boq_items]

    @staticmethod
    def _evaluate_item(item: Dict[str, Any]) -> VEOpportunityCard:
        boq_item = item.get("boq_item") or item.get("description") or "Unknown Item"
        original_spec = item.get("original_spec") or item.get("spec") or "C35 OPC"
        qty = float(item.get("qty", 1) or 1)
        unit_rate = float(item.get("unit_rate", 0) or 0)
        exposure = ExposureClass(item.get("exposure_class", "S1"))
        placement = PlacementContext(item.get("placement_context", "EXTERIOR"))
        candidate = ConcreteSource(item.get("candidate", ConcreteSource.CONC_SRC_C35_GGBFS))

        entry = CONC_CATALOG.get(candidate)
        if entry is None:
            return VEOpportunityCard(
                boq_item=boq_item,
                original_spec=original_spec,
                proposed_alternative=str(candidate),
                sbc_status="BLOCKED",
                is_recommended=False,
                technical_justification="NON-COMPLIANT with SBC 304: unrecognized substitution source.",
            )

        material = entry["material"]
        gate = Sbc304Engine.evaluate_material(
            fc_mpa=material.get("fc"),
            wc=material.get("wc"),
            fy_mpa=material.get("fy"),
            cover_depth_mm=material.get("cover"),
            exposure_class=exposure,
            placement=placement,
        )

        unit_delta = round(unit_rate * (entry["cost_diff_percent"] / 100.0), 2)

        if gate.is_compliant:
            net_savings = round(abs(unit_delta) * qty, 2) if unit_delta < 0 else 0.0
            return VEOpportunityCard(
                boq_item=boq_item,
                original_spec=original_spec,
                proposed_alternative=entry["proposed_alternative"],
                unit_delta_sar=unit_delta,
                net_savings_sar=net_savings,
                speed_index_gain_percent=entry["speed_index_gain_percent"],
                sbc_status="COMPLIANT",
                is_recommended=True,
                technical_justification=entry["justification"],
                sbc_304_references=list(entry["references"]),
            )

        return VEOpportunityCard(
            boq_item=boq_item,
            original_spec=original_spec,
            proposed_alternative=entry["proposed_alternative"],
            unit_delta_sar=unit_delta,
            net_savings_sar=0.0,
            speed_index_gain_percent=0.0,
            sbc_status="BLOCKED",
            is_recommended=False,
            technical_justification="NON-COMPLIANT with SBC 304: " + "; ".join(gate.violations),
            sbc_304_references=list(entry["references"]),
        )

    @staticmethod
    def summarize(cards: List[VEOpportunityCard]) -> VESummary:
        """Aggregate recommended cards into a summary."""
        recommended = [c for c in cards if c.is_recommended]
        blocked = [c for c in cards if not c.is_recommended]
        total_savings = sum(c.net_savings_sar for c in recommended)
        avg_speed = (
            sum(c.speed_index_gain_percent for c in recommended) / len(recommended)
            if recommended
            else 0.0
        )
        return VESummary(
            total_potential_savings_sar=round(total_savings, 2),
            net_schedule_acceleration_percent=round(avg_speed, 2),
            total_sbc_verified_proposals=len(recommended),
            total_blocked=len(blocked),
        )

    # ---- Legacy aggregation (backward compatibility) ----

    @staticmethod
    def evaluate_boq(boq_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Legacy VEData-compatible aggregation over the legacy catalog."""
        proposals: List[Dict[str, Any]] = []
        blocked: List[Dict[str, Any]] = []
        total_original_cost = 0.0
        total_savings = 0.0
        speed_indexes: List[float] = []

        for item in boq_items:
            desc = item.get("description", "")
            qty = float(item.get("qty", 0) or 0)
            unit_rate = float(item.get("unit_rate", 0) or 0)
            original_cost = qty * unit_rate
            total_original_cost += original_cost

            entry = ValueEngineeringEngine.LEGACY_CATALOG.get(desc)
            if entry is None:
                continue

            material = entry["material"]
            gate = Sbc304Engine.evaluate_material(
                fc_mpa=material.get("fc"),
                wc=material.get("wc"),
                fy_mpa=material.get("fy"),
                cover_depth_mm=material.get("cover"),
            )

            if gate.is_compliant:
                delta = round(original_cost * (entry["cost_diff_percent"] / 100.0), 2)
                savings = abs(delta) if delta < 0 else 0.0
                total_savings += savings
                speed_indexes.append(entry["speed_index"])
                proposals.append({
                    "original_item": desc,
                    "proposed_substitution": entry["substitution"],
                    "original_cost": original_cost,
                    "new_cost": round(original_cost + delta, 2),
                    "net_cost_delta_sar": delta,
                    "projected_savings": round(savings, 2),
                    "constructability_impact": f"+{round((entry['speed_index'] - 1.0) * 100, 2)}%",
                    "speed_index": entry["speed_index"],
                    "sbc_compliant": True,
                    "justification": entry["justification"],
                })
            else:
                blocked.append({
                    "original_item": desc,
                    "proposed_substitution": entry["substitution"],
                    "original_cost": original_cost,
                    "sbc_compliant": False,
                    "sbc_non_compliance_reason": "; ".join(gate.violations),
                    "blocked_parameters": [
                        v.split(" ")[0].strip("'") for v in gate.violations
                    ],
                    "justification": entry["justification"],
                })

        avg_speed = (sum(speed_indexes) / len(speed_indexes)) if speed_indexes else 1.0
        return {
            "total_proposals": len(proposals),
            "total_original_cost_sar": round(total_original_cost, 2),
            "total_projected_savings_sar": round(total_savings, 2),
            "savings_percentage": (
                round((total_savings / total_original_cost * 100), 2) if total_original_cost > 0 else 0.0
            ),
            "avg_constructability_index_boost": f"+{round((avg_speed - 1.0) * 100, 2)}%",
            "proposals": proposals,
            "blocked_substitutions": blocked,
        }