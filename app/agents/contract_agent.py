from typing import Any, Dict
from app.parsers.contract_risk_engine import ContractRiskEngine

def contract_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # Mock extracted contract clauses from the Client RFP corpus
    clauses = [
        {
            "ref": "Clause 14.1", 
            "text": "The Contractor shall give notice of a claim within 14 days after becoming aware of the event."
        },
        {
            "ref": "Clause 8.7", 
            "text": "Delay damages shall be applied at 0.1% per day. These liquidated damages are uncapped and without limit."
        },
        {
            "ref": "Clause 17.6",
            "text": "The Contractor shall indemnify the Employer against all consequential and indirect loss of profit."
        },
        {
            "ref": "Clause 20.1",
            "text": "The Contractor must give notice of claim within 28 days." # Safe clause, should be ignored
        }
    ]
    
    detected_risks = ContractRiskEngine.analyze_clauses(clauses)
    
    return {
        "contract_output": {
            "risks": detected_risks
        }
    }
