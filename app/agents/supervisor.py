"""
Supervisor — LangGraph conditional routing.

Registers the Tender Technical Evaluation node and the Risk Mitigation node,
and routes conditionally after evaluation:

  - compliance score < 70%  -> risk_mitigation_node
  - compliance score >= 70% -> value_engineering_node
"""

from typing import Any, Dict

PASS_THRESHOLD = 70.0


def risk_mitigation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Risk Mitigation node — consumes the tender evaluation risks and produces
    an actionable mitigation register.
    """
    print("--- [AGENT] Risk Mitigation ---")
    evaluation = state.get("tender_evaluation", {}) or {}
    risks = evaluation.get("risks", []) or []

    mitigation_output = {
        "triggered": True,
        "reason": (
            evaluation.get("summary", "Technical evaluation below gate.")
            if not evaluation.get("pass_fail", True)
            else "Precautionary risk review."
        ),
        "risk_count": len(risks),
        "actions": [
            {
                "risk_id": r.get("risk_id"),
                "category": r.get("category"),
                "severity": r.get("severity"),
                "action": r.get("mitigation", "Review and remediate."),
            }
            for r in risks
        ],
    }
    return {"risk_mitigation_output": mitigation_output}


def route_after_evaluation(state: Dict[str, Any]) -> str:
    """Conditional edge: low compliance routes to risk mitigation."""
    evaluation = state.get("tender_evaluation", {}) or {}
    if not evaluation.get("pass_fail", True):
        return "risk_mitigation"
    return "value_engineering"


def register_supervisor(graph) -> None:
    """
    Register the supervisor nodes and conditional edges on a compiled-ready
    StateGraph. The graph must already declare the ``tender_evaluation``,
    ``risk_mitigation_output`` and ``value_engineering`` state keys.
    """
    from app.agents.tender_evaluation_agent import tender_evaluation_node

    graph.add_node("tender_evaluation", tender_evaluation_node)
    graph.add_node("risk_mitigation", risk_mitigation_node)

    graph.add_conditional_edges(
        "tender_evaluation",
        route_after_evaluation,
        {
            "risk_mitigation": "risk_mitigation",
            "value_engineering": "value_engineering",
        },
    )
    graph.add_edge("risk_mitigation", "value_engineering")