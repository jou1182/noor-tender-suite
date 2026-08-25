from typing import Any, Dict
from app.parsers.drift_engine import DriftEngine

def drift_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # Extract data from state or mock for demonstration of the flow
    base_text = state.get("base_rfp_text", "Clause 1.0: Excavation is 5m deep.\nClause 2.0: Concrete grade C30.")
    addendum_text = state.get("addendum_rfp_text", "Clause 1.0: Excavation is 7m deep.\nClause 2.0: Concrete grade C30.")
    
    base_boq = state.get("base_boq", {"Excavation": 5000})
    addendum_boq = state.get("addendum_boq", {"Excavation": 7000})
    
    drift_results = DriftEngine.compare_versions(base_text, addendum_text, base_boq, addendum_boq)
    
    # Map impacts to existing compliance records, forcing re-audit triggers
    existing_records = state.get("compliance_records", [
        {"clause_code": "1.0", "status": "Pass"},
        {"clause_code": "2.0", "status": "Pass"}
    ])
    
    for rec in existing_records:
        if any(rec["clause_code"] in clause for clause in drift_results["impacted_clauses"]):
            rec["status"] = "RE-AUDIT_REQUIRED"
            
    drift_results["updated_compliance_records"] = existing_records
    
    return {"drift_output": drift_results}
