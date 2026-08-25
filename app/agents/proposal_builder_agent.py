from typing import Any, Dict
from app.services.proposal_generator import ProposalGeneratorService

def proposal_builder_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generative agent that constructs the technical proposal and method statement
    narratives automatically based on the parsed BOQ items and RFP specifications.
    """
    # Extract upstream parsed data or apply fallback mocks
    rfp_specs = state.get("rfp_output", {}).get("project_specs", "Standard commercial building specifications.")
    
    boq_output = state.get("boq_output", {})
    # Defaulting to structural test items if the upstream BOQ is empty
    raw_items = boq_output.get("items", ["Site Excavation Work", "Reinforced Concrete Foundation"])

    # BOQ line items may be structured dicts; normalize to description strings.
    item_names = []
    for item in raw_items:
        if isinstance(item, dict):
            name = item.get("description") or item.get("boq_item") or ""
            if name:
                item_names.append(str(name))
        else:
            item_names.append(str(item))
    if not item_names:
        item_names = ["Site Excavation Work", "Reinforced Concrete Foundation"]

    # Generate the proposal structure
    generated_proposal = ProposalGeneratorService.build_full_proposal(item_names, rfp_specs)
    
    return {"generated_proposal_output": generated_proposal}
