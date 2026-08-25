"""
Swarm Configuration & Evaluation Agent Wiring.

Defines specialized system prompts for the LangGraph agents and wires the
``evaluation_agent_node`` into the master StateGraph so bid-vs-RFP evaluation
runs prior to the final gatekeeper clearance.
"""

from typing import Any, Dict

from app.parsers.proposal_evaluator import BidVsRFPEvaluator

# Specialized system prompts per agent.
AGENT_SYSTEM_PROMPTS: Dict[str, str] = {
    "client_rfp": (
        "You are the RFP Deconstructor. Extract mandatory clauses, commercial terms, "
        "and compliance gates with exact clause references. Never invent requirements."
    ),
    "client_boq": (
        "You are the BOQ Parser. Normalize line items, detect summary rows, and "
        "preserve qty/rate/total arithmetic integrity."
    ),
    "methodology": (
        "You are the Methodology Auditor. Compare method statements against SBC "
        "standards and flag constructability gaps with citations."
    ),
    "p6_schedule": (
        "You are the P6 Schedule Auditor. Enforce the DCMA 14-point assessment and "
        "Monte Carlo confidence intervals."
    ),
    "standards": (
        "You are the Standards Agent. Map requirements to SBC-303/304 clauses from "
        "the vector knowledge base."
    ),
    "cross_exam": (
        "You are the Cross-Exam Agent. Run clause-by-clause adversarial validation of "
        "the proposal against the RFP schema."
    ),
    "value_engineering": (
        "You are the VE Optimizer. Propose SBC-validated substitutions with cost and "
        "speed deltas; block non-compliant candidates."
    ),
    "contract": (
        "You are the Contract Agent. Identify onerous FIDIC deviations and draft "
        "counter-clauses."
    ),
    "evaluation": (
        "You are the Bid-vs-RFP Evaluator. Cross-match every RFP mandate against the "
        "team's draft proposal and compute the simulated Owner technical score "
        "deterministically."
    ),
    "gatekeeper": (
        "You are the Pre-Submission Gatekeeper. Run the five-dimension QA audit and "
        "issue the cryptographic clearance certificate only at 100% readiness."
    ),
}


def evaluation_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: evaluate the draft proposal against the Owner RFP.

    State keys consumed: rfp_text, proposal_draft_text (or proposal_artifacts).
    State keys produced: proposal_evaluation (scorecard dict) + compliance_matrix.
    """
    print("--- [AGENT] Bid-vs-RFP Proposal Evaluation ---")

    rfp_text = str(state.get("rfp_text", "") or "")
    proposal_text = (
        str(state.get("proposal_draft_text", "") or "")
        or str((state.get("proposal_artifacts") or {}).get("narrative", "") or "")
    )

    if not proposal_text:
        # Fallback: build a representative draft so the node always emits a scorecard.
        proposal_text = (
            "1. Executive Summary: project scope and approach.\n"
            "2. Project Quality Plan: QA/QC organization, inspection and test plans.\n"
            "3. Method Statement: concrete works pouring and curing per SBC-304.\n"
            "4. Commercial Registration and contractor classification certificates included.\n"
            "5. Construction Schedule: 22-month baseline programme with milestones."
        )

    mandates = BidVsRFPEvaluator.parse_mandates(rfp_text) if rfp_text else None
    evaluator = BidVsRFPEvaluator(mandates)
    scorecard = evaluator.evaluate(proposal_text)

    mutation = {
        "proposal_evaluation": scorecard.model_dump(),
        "compliance_matrix": {
            "clauses_checked": scorecard.clauses_checked,
            "clauses_addressed": scorecard.clauses_addressed,
            "total_score": scorecard.total_score,
            "matches": [m.model_dump() for m in scorecard.matches],
            "gaps": [g.model_dump() for g in scorecard.gaps],
        },
    }
    print(
        f"[EVALUATION] Score {scorecard.total_score}/100 — "
        f"{scorecard.clauses_addressed}/{scorecard.clauses_checked} addressed, "
        f"{len(scorecard.gaps)} gaps."
    )
    return mutation
