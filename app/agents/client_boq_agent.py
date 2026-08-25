from typing import Any, Dict

def client_boq_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Client BOQ Agent — parses the bill of quantities into structured line items."""
    return {
        "boq_output": {
            "boq_financials": {"total_budget": 5000000},
            "items": [
                {
                    "boq_item": "Raft Foundation",
                    "original_spec": "C35 OPC",
                    "qty": 1200,
                    "unit_rate": 620,
                    "exposure_class": "S2",
                    "placement_context": "CAST_AGAINST_EARTH",
                    "candidate": "CONC_SRC_C35_GGBFS",
                },
                {
                    "boq_item": "Slab on Grade",
                    "original_spec": "C35 OPC",
                    "qty": 800,
                    "unit_rate": 580,
                    "exposure_class": "S1",
                    "placement_context": "CAST_AGAINST_EARTH",
                    "candidate": "CONC_SRC_LEAN_LOWCEMENT",
                },
            ],
        }
    }