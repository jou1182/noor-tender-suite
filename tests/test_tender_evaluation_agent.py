"""
Tender Technical Evaluation Agent — verification tests.

Covers weighted scoring (40/30/30), Pass/Fail gating at 70%, risk
identification, and supervisor conditional routing between the risk
mitigation and value engineering branches.
"""

import pytest

from app.agents.supervisor import register_supervisor, risk_mitigation_node, route_after_evaluation
from app.agents.tender_evaluation_agent import tender_evaluation_node
from app.parsers.value_engineering_engine import ValueEngineeringEngine


HIGH_STATE = {
    "tender_id": 101,
    "standards_output": {
        "standards_citations": [
            {"code": "SBC-303", "violation": False},
            {"code": "SBC-304", "violation": False},
        ]
    },
    "calculation_output": {"checks": [{"is_safe": True}, {"is_safe": True}, {"is_safe": True}, {"is_safe": True}]},
    "submittal_output": {"parameters_evaluated": [{"passed": True}, {"passed": True}]},
    "p6_output": {"dcma_results": {"metrics": [{"passed": True}, {"passed": True}, {"passed": True}, {"passed": True}]}},
    "generated_proposal_output": [{"productivity_rate": 40.0}, {"productivity_rate": 150.0}],
}

LOW_STATE = {
    "tender_id": 102,
    "standards_output": {"standards_citations": [{"code": "SBC-303", "violation": True}]},
    "calculation_output": {"checks": [{"is_safe": False}, {"is_safe": False}]},
    "submittal_output": {"parameters_evaluated": [{"passed": True}, {"passed": False}]},
    "p6_output": {"dcma_results": {"metrics": [{"passed": False}, {"passed": False}, {"passed": False}]}},
    "generated_proposal_output": [],
}


def test_high_compliance_scores_above_threshold():
    out = tender_evaluation_node(HIGH_STATE)
    report = out["tender_evaluation"]
    assert report["overall_score"] == 100.0
    assert report["pass_fail"] is True
    assert len(report["criteria"]) == 3

    weights = {c["code"]: c["weight"] for c in report["criteria"]}
    assert weights == {"STRUCTURAL_CODE": 0.40, "MATERIAL_SPEC": 0.30, "METHOD_SCHEDULE": 0.30}
    # Weighted criteria must sum to the overall score.
    assert sum(c["weighted_score"] for c in report["criteria"]) == report["overall_score"]


def test_non_compliant_state_scores_below_threshold_and_fails_gate():
    out = tender_evaluation_node(LOW_STATE)
    report = out["tender_evaluation"]
    assert report["overall_score"] == 15.0
    assert report["pass_fail"] is False
    assert any(c["status"] == "NON_COMPLIANT" for c in report["criteria"])


def test_risk_identification_low_state():
    out = tender_evaluation_node(LOW_STATE)
    report = out["tender_evaluation"]
    risks = report["risks"]
    assert risks, "no risks surfaced for low-compliance state"
    assert any(r["risk_id"] == "TEV-RISK-OVERALL" for r in risks)
    assert "CRITICAL" in {r["severity"] for r in risks}


def test_high_state_has_no_overall_risk():
    out = tender_evaluation_node(HIGH_STATE)
    report = out["tender_evaluation"]
    assert not any(r["risk_id"] == "TEV-RISK-OVERALL" for r in report["risks"])


def test_conditional_routing_low_to_risk_mitigation():
    low_out = tender_evaluation_node(LOW_STATE)
    assert route_after_evaluation(low_out) == "risk_mitigation"


def test_conditional_routing_high_to_value_engineering():
    high_out = tender_evaluation_node(HIGH_STATE)
    assert route_after_evaluation(high_out) == "value_engineering"


def test_risk_mitigation_node_produces_actions():
    out = tender_evaluation_node(LOW_STATE)
    mitigation = risk_mitigation_node(out)
    register = mitigation["risk_mitigation_output"]
    assert register["triggered"] is True
    assert register["risk_count"] >= 1
    assert register["actions"], "mitigation actions missing"
    assert all("action" in a for a in register["actions"])


def test_supervisor_registration_on_graph():
    from app.agents.graph import build_orchestrator

    graph = build_orchestrator()
    compiled = graph  # build_orchestrator() already registers the supervisor + compiles

    # Structural smoke test: invoke the full graph and assert the evaluation key.
    result = compiled.invoke({"tender_id": 999})
    assert "tender_evaluation" in result, "tender_evaluation missing from graph state"

    evaluation = result["tender_evaluation"]
    if evaluation["pass_fail"]:
        assert "ve_matrix" in result, "high-compliance state should route to value_engineering"
        assert "risk_mitigation_output" not in result
    else:
        assert "risk_mitigation_output" in result, "low-compliance state should route to risk mitigation"


def test_supervisor_smoke_imports():
    # Guard against import-time regressions.
    assert callable(register_supervisor)
    assert callable(route_after_evaluation)
    assert callable(ValueEngineeringEngine.generate_ve_matrix)