from typing import Any, Dict
from app.services.dossier_assembler import DossierAssembler

def dossier_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final terminal node in the LangGraph topology.
    Assembles the Master Technical Proposal Dossier from all preceding agent states 
    and applies cryptographic SHA-256 seals.
    """
    master_dossier = DossierAssembler.assemble_master_dossier(state)
    
    return {
        "dossier_output": master_dossier
    }
