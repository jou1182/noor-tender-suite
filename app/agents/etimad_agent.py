from typing import Any, Dict
from app.parsers.etimad_validator import EtimadValidator

def etimad_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # In production, this pulls parsed multimodal outputs containing classification cert logic
    # For now, we mock a compliant submission to successfully clear the gate in the graph
    mock_payload = {
        "documents": {
            "bank_guarantee": {"validity_days": 120},
            "classification_certificate": True,
            "local_content_score": 25.5
        }
    }

    result = EtimadValidator.validate_submission(mock_payload)
    
    return {"etimad_output": result}
