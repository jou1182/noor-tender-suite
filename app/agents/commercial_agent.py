from typing import Any, Dict
from app.parsers.cost_scurve_engine import CostSCurveEngine

def commercial_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # Extract mock activities simulating parsed P6 and BOQ merged structures
    activities = [
        {"item": "Mobilization", "cost": 500000, "unit_rate": 500000, "early_start": 0, "late_start": 0, "duration": 1},
        {"item": "Excavation", "cost": 1500000, "unit_rate": 45, "early_start": 1, "late_start": 2, "duration": 3},
        {"item": "Concrete Foundation", "cost": 3000000, "unit_rate": 600, "early_start": 3, "late_start": 5, "duration": 4}
    ]
    
    # Internal historical baselines mapped by AI
    baselines = {
        "Mobilization": 200000, # Bidders front-loading this to get early cash
        "Excavation": 35,       # Slightly high, but maybe not front-loaded >20%
        "Concrete Foundation": 620
    }
    
    max_month = 8
    
    # Generate financial structures
    scurve_data = CostSCurveEngine.generate_scurve(activities, max_month)
    front_loading = CostSCurveEngine.detect_front_loading(activities, baselines)
    
    return {
        "commercial_output": {
            "scurve": scurve_data,
            "front_loaded_warnings": front_loading
        }
    }
