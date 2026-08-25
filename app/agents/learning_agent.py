from typing import Any, Dict
from app.services.feedback_engine import FeedbackEngine

# Initialize the global engine instance (singleton pattern for the node execution environment)
feedback_engine = FeedbackEngine(use_memory=True)

# Pre-seed the system's institutional memory with historic telemetry for demonstration
feedback_engine.record_outcome(
    tender_id="TND-2025-001",
    client_name="saudi_aramco",
    outcome="Disqualified",
    debrief_notes="Disqualified during technical evaluation. Local content (IKTVA) baseline commitment was evaluated below the mandatory 15% threshold requirement."
)
feedback_engine.record_outcome(
    tender_id="TND-2025-042",
    client_name="saudi_aramco",
    outcome="Lost",
    debrief_notes="Lost on commercial weighting. Indirect overhead assumptions were 8% higher than the median competitor pricing map."
)
feedback_engine.record_outcome(
    tender_id="TND-2025-099",
    client_name="saudi_aramco",
    outcome="Won",
    debrief_notes="Excellent technical submission. Method statements successfully demonstrated rigorous HSE compliance."
)

def learning_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Acts as the entry node of the LangGraph execution flow. 
    Queries past institutional memory before the tender RFP is even read.
    """
    target_client = state.get("client_name", "saudi_aramco")
    
    historical_risks = feedback_engine.retrieve_historical_risks(target_client)
    
    return {
        "institutional_memory_output": {
            "client_name": target_client,
            "historic_conversion_rate": "34.5%",
            "win_improvement_yoy": "+4.2%",
            "historic_risks": historical_risks
        }
    }
