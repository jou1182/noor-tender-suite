"""
SBC-304 Compliance & Value Engineering Optimizer — verification suite.

Required cases:
  1. S2 sulfate-exposure mix violation (f'c >= 31.0 MPa, w/c <= 0.45).
  2. Earth-cast concrete cover violation (SBC 304 Sec 7.7, 75.0 mm).
  3. Rebar yield strength limits (non-standard warning; over-strength block).
  4. VE engine blocks a non-compliant cost-saving substitution.
  5. VE engine approves a compliant optimization (CONC_SRC_C35_GGBFS).

Plus deterministic coverage of agent state mutation and summary aggregation.
"""

from app.agents.value_engineering_agent import value_engineering_node
from app.parsers.sbc_standards_engine import ExposureClass, PlacementContext, Sbc304Engine
from app.parsers.value_engineering_engine import ValueEngineeringEngine


# ---- Required: 1. S2 durability violation ----
def test_sbc_durability_sulfate_s2_violation():
    result = Sbc304Engine.evaluate_mix(
        fc_mpa=28.0, wc=0.50, exposure_class=ExposureClass.S2
    )
    assert result.is_compliant is False
    fc_msg = next(v for v in result.violations if "f'c" in v)
    assert ">= 31.0 MPa" in fc_msg, fc_msg
    wc_msg = next(v for v in result.violations if "w/c" in v)
    assert "<= 0.45" in wc_msg, wc_msg


# ---- Required: 2. Earth-cast cover violation ----
def test_sbc_concrete_cover_earth_cast_violation():
    result = Sbc304Engine.evaluate_cover(50.0, PlacementContext.CAST_AGAINST_EARTH)
    assert result.is_compliant is False
    assert result.min_cover_mm == 75.0
    assert "75.0 mm" in result.violations[0]


# ---- Required: 3. Rebar yield strength limits ----
def test_sbc_rebar_yield_strength_limits():
    non_standard = Sbc304Engine.evaluate_rebar(500.0)
    assert non_standard.warnings, "non-standard grade (500 MPa) must trigger a warning"
    assert non_standard.is_compliant is True

    over_strength = Sbc304Engine.evaluate_rebar(600.0)
    assert over_strength.is_compliant is False
    assert "550" in over_strength.violations[0], over_strength.violations


# ---- Required: 4. VE blocks non-compliant cost-saving substitution ----
def test_ve_engine_blocks_non_compliant_cost_saving_substitutions():
    boq = [
        {
            "boq_item": "Slab on Grade",
            "original_spec": "C35 OPC",
            "qty": 800,
            "unit_rate": 580,
            "exposure_class": "S2",
            "placement_context": "CAST_AGAINST_EARTH",
            "candidate": "CONC_SRC_LEAN_LOWCEMENT",
        }
    ]
    cards = ValueEngineeringEngine.generate_ve_matrix(boq)
    card = cards[0]
    assert card.is_recommended is False
    assert card.technical_justification.startswith("NON-COMPLIANT with SBC 304:")


# ---- Required: 5. VE approves compliant optimization ----
def test_ve_engine_approves_compliant_optimizations():
    boq = [
        {
            "boq_item": "Raft Foundation",
            "original_spec": "C35 OPC",
            "qty": 1200,
            "unit_rate": 620,
            "exposure_class": "S2",
            "placement_context": "CAST_AGAINST_EARTH",
            "candidate": "CONC_SRC_C35_GGBFS",
        }
    ]
    cards = ValueEngineeringEngine.generate_ve_matrix(boq)
    card = cards[0]
    assert card.is_recommended is True
    assert card.net_savings_sar > 0
    assert card.speed_index_gain_percent >= 0


# ---- Additional deterministic coverage ----

def test_sbc_mix_general_compliant():
    result = Sbc304Engine.evaluate_mix(35.0, 0.40, ExposureClass.S1)
    assert result.is_compliant is True


def test_sbc_grade60_rebar_compliant():
    result = Sbc304Engine.evaluate_rebar(420.0)
    assert result.is_compliant is True
    assert result.warnings == []


def test_ve_mixed_matrix_accepts_and_blocks():
    boq = [
        {
            "boq_item": "Raft Foundation",
            "original_spec": "C35 OPC",
            "qty": 1200,
            "unit_rate": 620,
            "exposure_class": "S2",
            "placement_context": "CAST_AGAINST_EARTH",
            "candidate": "CONC_SRC_C35_GGBFS",
        },
        {
            "boq_item": "Slab on Grade",
            "original_spec": "C35 OPC",
            "qty": 800,
            "unit_rate": 580,
            "exposure_class": "S1",
            "placement_context": "CAST_AGAINST_EARTH",
            "candidate": "CONC_SRC_LEAN_LOWCEMENT",
        },
    ]
    cards = ValueEngineeringEngine.generate_ve_matrix(boq)
    assert sum(c.is_recommended for c in cards) == 1
    assert sum(not c.is_recommended for c in cards) == 1
    # Studio-contract mirror (frontend/src/types/ve.ts fields).
    for field in ("boq_item", "original_spec", "proposed_alternative", "unit_delta_sar",
                  "net_savings_sar", "speed_index_gain_percent", "sbc_status",
                  "is_recommended", "technical_justification", "sbc_304_references",
                  "is_accepted"):
        assert hasattr(cards[0], field), f"missing studio-contract field: {field}"


def test_ve_summary_aggregation():
    boq = [
        {
            "boq_item": "Raft Foundation",
            "original_spec": "C35 OPC",
            "qty": 1200,
            "unit_rate": 620,
            "exposure_class": "S2",
            "placement_context": "CAST_AGAINST_EARTH",
            "candidate": "CONC_SRC_C35_GGBFS",
        },
        {
            "boq_item": "Slab on Grade",
            "original_spec": "C35 OPC",
            "qty": 800,
            "unit_rate": 580,
            "exposure_class": "S1",
            "placement_context": "CAST_AGAINST_EARTH",
            "candidate": "CONC_SRC_LEAN_LOWCEMENT",
        },
    ]
    cards = ValueEngineeringEngine.generate_ve_matrix(boq)
    summary = ValueEngineeringEngine.summarize(cards)
    assert summary.total_potential_savings_sar > 0
    assert summary.total_sbc_verified_proposals == 1
    assert summary.total_blocked == 1
    assert summary.net_schedule_acceleration_percent >= 0


def test_agent_mutates_state_with_ve_matrix_and_summary():
    boq = {
        "boq_output": {
            "items": [
                {
                    "boq_item": "Raft Foundation",
                    "original_spec": "C35 OPC",
                    "qty": 1200,
                    "unit_rate": 620,
                    "exposure_class": "S2",
                    "placement_context": "CAST_AGAINST_EARTH",
                    "candidate": "CONC_SRC_C35_GGBFS",
                },
                {
                    "boq_item": "Slab on Grade",
                    "original_spec": "C35 OPC",
                    "qty": 800,
                    "unit_rate": 580,
                    "exposure_class": "S1",
                    "placement_context": "CAST_AGAINST_EARTH",
                    "candidate": "CONC_SRC_LEAN_LOWCEMENT",
                },
            ]
        }
    }
    out = value_engineering_node(boq)
    assert "ve_matrix" in out and "ve_summary" in out
    assert len(out["ve_matrix"]) == 2
    assert out["ve_summary"]["total_sbc_verified_proposals"] == 1
    assert out["ve_summary"]["total_blocked"] == 1


def test_agent_default_mock_produces_blocked_entry():
    out = value_engineering_node({})
    matrix = out["ve_matrix"]
    assert len(matrix) >= 2
    blocked = [c for c in matrix if not c["is_recommended"]]
    assert blocked, "mock catalog should surface a blocked substitution"
    assert blocked[0]["technical_justification"].startswith("NON-COMPLIANT with SBC 304:")