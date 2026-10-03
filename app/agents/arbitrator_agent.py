from typing import Any, Dict

from app.agents.errors import InsufficientInputError


def arbitrator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Final verdict derived from the real weighted technical evaluation.

    The score is never invented: it is the ``tender_evaluation`` overall score
    computed upstream. Without it there is nothing to arbitrate.
    """
    evaluation = state.get("tender_evaluation") or {}
    score = evaluation.get("overall_score")
    if score is None:
        raise InsufficientInputError("Arbitrator has no technical evaluation score to rule on.")

    passed = bool(evaluation.get("pass_fail", False))
    return {
        "arbitrator_output": {
            "final_score": float(score),
            "summary": evaluation.get("summary") or ("Passed technical gate" if passed else "Below technical gate"),
            "status": "APPROVED" if passed else "REJECTED",
        }
    }
