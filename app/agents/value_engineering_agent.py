from typing import Any, Dict, List

from app.parsers.value_engineering_engine import ValueEngineeringEngine

# Demonstration BOQ line items (concrete pours) with exposure / placement context
# and a candidate substitution source to evaluate.
MOCK_BOQ_ITEMS: List[Dict[str, Any]] = [
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
]


def _extract_boq_items(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Resolve BOQ line items from state (boq_output), defaulting to the mock."""
    boq = state.get("boq_output", {}) or {}
    items = boq.get("items")
    if items:
        return items
    legacy = state.get("client_boq_output", {}) or {}
    if legacy.get("items"):
        return legacy["items"]
    return MOCK_BOQ_ITEMS


def value_engineering_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Value Engineering & Constructability Optimization node.

    Extracts BOQ line items, runs ValueEngineeringEngine.generate_ve_matrix(),
    and mutates the orchestration state with ``ve_matrix`` (List[VEOpportunityCard])
    and ``ve_summary`` (aggregated savings SAR + average speed gain).

    Explicitly logs the SBC-304 compliance verdict for every evaluated item.
    """
    print("--- [AGENT] Value Engineering & Constructability Optimizer ---")

    boq_items = _extract_boq_items(state)
    cards = ValueEngineeringEngine.generate_ve_matrix(boq_items)
    summary = ValueEngineeringEngine.summarize(cards)

    # Explicit SBC-304 compliance logging for every evaluated item.
    for card in cards:
        print(
            f"[VE] {card.boq_item} | {card.sbc_status} | recommended={card.is_recommended} "
            f"| savings={card.net_savings_sar} SAR | speed={card.speed_index_gain_percent}% "
            f"| {card.technical_justification[:100]}"
        )

    matrix = [card.model_dump() for card in cards]
    summary_dict = summary.model_dump()

    return {
        "ve_matrix": matrix,
        "ve_summary": summary_dict,
        "ve_output": {"ve_matrix": matrix, "ve_summary": summary_dict},
    }


# Backward-compatible alias (the graph registers this node as `value_engineering_agent`).
value_engineering_agent = value_engineering_node