from typing import Dict, Any
from app.services.submission_dispatch_service import SubmissionDispatchService

def submission_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final node in the LangGraph Orchestration.
    Validates the compiled master dossier via the Pre-Flight Submission Dispatcher,
    issuing a certified payload or explicitly locking out the submission due to integrity failures.
    """
    print("--- [AGENT] Submission Pre-Flight Dispatcher ---")
    dossier_output = state.get("dossier_output", {})
    dispatch_output = SubmissionDispatchService.execute_preflight_checks(dossier_output)
    
    return {"dispatch_output": dispatch_output}
