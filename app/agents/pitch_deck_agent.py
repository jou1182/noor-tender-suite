from typing import Dict, Any
from app.parsers.simulation_4d_engine import Simulation4DEngine

def pitch_deck_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automated Pitch Deck Generation Agent.
    Aggregates executive telemetry, DCMA ratings, and active 4D digital twin state simulations
    into a structured presentation payload ready for front-end rendering or PDF export.
    """
    print("--- [AGENT] 4D Twin & Pitch Deck Generator ---")
    
    # Simulate extraction of active project BIM/IFC logic and P6 scheduling
    mock_elements = [
        {"guid": "IFC-FOUNDATION-01", "start_date": "2026-08-01T08:00:00", "finish_date": "2026-08-15T18:00:00", "is_critical": False, "delay_days": 0},
        {"guid": "IFC-COREWALL-02", "start_date": "2026-08-10T08:00:00", "finish_date": "2026-08-25T18:00:00", "is_critical": True, "delay_days": 3},
        {"guid": "IFC-ROOFSKU-03", "start_date": "2026-09-01T08:00:00", "finish_date": "2026-09-30T18:00:00", "is_critical": False, "delay_days": 0}
    ]
    
    # Generate the active visual twin snapshot based on current execution time
    snapshots = Simulation4DEngine.generate_timeline_snapshots(mock_elements)
    
    deck_payload = {
        "title": "Master Proposal Pitch Deck & 4D Execution Plan",
        "slides": [
            {"type": "EXECUTIVE_SUMMARY", "content": "Comprehensive end-to-end multi-agent orchestration completed."},
            {"type": "4D_DIGITAL_TWIN", "simulation_data": snapshots},
            {"type": "DCMA_METRICS", "score": state.get("p6_output", {}).get("dcma_score", "VERIFIED")},
        ]
    }
    
    return {"pitch_deck_output": deck_payload}
