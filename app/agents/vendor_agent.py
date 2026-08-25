from typing import Any, Dict
from app.parsers.rfq_package_engine import RfqPackageEngine

def vendor_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates intelligent RFQ compilation and vendor bid normalization.
    Clusters flat upstream BOQ data into specific CSI operational sub-contracts.
    """
    # Upstream mock BOQ data for analytical processing
    mock_boq = [
        {"item_no": "1.1", "description": "Excavation for foundations", "qty": 500, "unit": "m3", "rate": 25.0},
        {"item_no": "1.2", "description": "Backfill with approved soil", "qty": 300, "unit": "m3", "rate": 15.0},
        {"item_no": "2.1", "description": "Ready-mix Concrete 35MPa", "qty": 1000, "unit": "m3", "rate": 350.0},
        {"item_no": "2.2", "description": "High yield structural rebar", "qty": 120, "unit": "t", "rate": 2500.0}
    ]
    
    clusters = RfqPackageEngine.cluster_boq_items(mock_boq)
    
    # Simulate isolated evaluation for the Concrete Subcontracting Package
    concrete_budget = (1000 * 350.0) + (120 * 2500.0) # Evaluates exactly to 650,000 SAR
    
    mock_quotes = [
        {"vendor_name": "Saudi ReadyMix Co.", "bid_amount": 640000, "scope_coverage_pct": 100.0},
        {"vendor_name": "Al Kifah Building Materials", "bid_amount": 585000, "scope_coverage_pct": 90.0}, # Appeared cheaper, but missing 10% operational scope (e.g., pump trucks)
        {"vendor_name": "Eastern Concrete Suppliers", "bid_amount": 665000, "scope_coverage_pct": 100.0}
    ]
    
    # Executes defensive normalization algorithms to expose the true cost of Al Kifah's omitted scope
    evaluations = RfqPackageEngine.normalize_vendor_bids(concrete_budget, mock_quotes)
    
    # Pack resulting cluster metadata payload
    package_metadata = []
    for trade, items in clusters.items():
        package_metadata.append({
            "trade_package": trade,
            "item_count": len(items),
            "estimated_value": sum((i["qty"] * i["rate"]) for i in items)
        })
        
    return {
        "vendor_output": {
            "packages": package_metadata,
            "concrete_evaluation": {
                "budget": concrete_budget,
                "vendors": evaluations
            }
        }
    }
