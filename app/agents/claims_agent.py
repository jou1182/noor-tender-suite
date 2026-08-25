from typing import Any, Dict
from datetime import datetime
from app.parsers.tia_engine import TIAEngine

def claims_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # Mock Post-Award Variables for Variation Analysis
    baseline_end = datetime(2027, 12, 31)
    
    # Engineer issues instruction requiring structural re-design and extended execution
    fragnet_delays = [15, 10] # 15 days redesign phase + 10 days execution delay
    
    new_end, eot_days = TIAEngine.calculate_eot(baseline_end, fragnet_delays)
    
    # Notice evaluation simulation
    event_date = datetime(2026, 8, 1)
    notice_date = datetime(2026, 8, 15) # 14 days elapsed (Within bounds)
    
    entitlement = TIAEngine.evaluate_entitlement(event_date, notice_date)
    
    # Prolongation cost calculation based on modeled indirects
    daily_overhead_rate = 15000.0 # SAR
    cost_impact = eot_days * daily_overhead_rate
    
    draft_letter = (
        f"NOTICE OF CLAIM PURSUANT TO FIDIC SUB-CLAUSE 20.1\n\n"
        f"Dear Engineer,\n\n"
        f"We hereby give formal notice of our claim for an Extension of Time (EoT) and additional payment "
        f"resulting from the Engineer's Instruction dated {event_date.strftime('%Y-%m-%d')}.\n\n"
        f"Our Time Impact Analysis (TIA) demonstrates a direct critical path delay of {eot_days} days, "
        f"shifting the contractual completion date from {baseline_end.strftime('%Y-%m-%d')} to {new_end.strftime('%Y-%m-%d')}.\n\n"
        f"Estimated prolongation costs currently amount to SAR {cost_impact:,.2f}. Full particulars will follow within 42 days."
    )
    
    return {
        "claims_output": {
            "baseline_completion": baseline_end.strftime("%Y-%m-%d"),
            "impacted_completion": new_end.strftime("%Y-%m-%d"),
            "eot_days": eot_days,
            "entitlement": entitlement,
            "prolongation_cost": cost_impact,
            "draft_claim_letter": draft_letter
        }
    }
