from typing import Any, Dict

def hse_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"hse_output": {"hse_risks": [{"risk": "Crane operation safety not explicitly detailed"}]}}
