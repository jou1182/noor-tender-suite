from typing import Any, Dict

def qaqc_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"qaqc_output": {"qaqc_deficiencies": [{"issue": "Missing QA manual"}]}}
