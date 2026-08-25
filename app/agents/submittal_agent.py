from typing import Dict, Any
from app.parsers.submittal_review_engine import SubmittalReviewEngine

def submittal_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Technical Office Material Submittal Agent.
    Executes between Standards and QA/QC nodes, simulating an intensive technical review
    of manufacturer data sheets against SBC requirements and outputting structured Transmittal Forms.
    """
    print("--- [AGENT] Technical Office Submittal Review ---")
    
    # Simulate extraction of a structured Technical Data Sheet payload from the Orchestration network
    mock_submittal = {
        "material": "High-Performance Concrete Mix Design (C40) - Substructure",
        "minor_deviation": False,
        "parameters": [
            {"name": "28-Day Compressive Strength", "required_value": 40, "submitted_value": 42.5, "operator": ">=", "unit": "MPa"},
            {"name": "Water/Cement Ratio", "required_value": 0.40, "submitted_value": 0.38, "operator": "<=", "unit": "Ratio"},
            {"name": "Slump Test Tolerance", "required_value": 150, "submitted_value": 145, "operator": "<=", "unit": "mm"},
            {"name": "Chloride Ion Penetrability", "required_value": 1000, "submitted_value": 850, "operator": "<=", "unit": "Coulombs"}
        ]
    }
    
    submittal_output = SubmittalReviewEngine.evaluate_submittal(mock_submittal)
    
    return {"submittal_output": submittal_output}
