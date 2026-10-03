from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END

from app.agents.client_rfp_agent import client_rfp_agent
from app.agents.client_boq_agent import client_boq_agent
from app.agents.proposal_builder_agent import proposal_builder_agent
from app.agents.methodology_agent import methodology_agent
from app.agents.calculation_agent import calculation_agent
from app.agents.geotech_agent import geotech_agent
from app.agents.p6_dcma_agent import p6_dcma_agent
from app.agents.commercial_agent import commercial_agent
from app.agents.standards_agent import standards_agent
from app.agents.qaqc_deep_agent import qaqc_deep_agent
from app.agents.cross_exam_agent import cross_exam_agent
from app.agents.red_team_agent import red_team_agent
from app.agents.contract_agent import contract_agent
from app.agents.etimad_agent import etimad_agent
from app.agents.claims_agent import claims_agent
from app.agents.bim_agent import bim_agent
from app.agents.learning_agent import learning_agent
from app.agents.vendor_agent import vendor_agent
from app.agents.arbitrator_agent import arbitrator_agent
from app.agents.dossier_agent import dossier_agent
from app.agents.vendor_agent import vendor_agent
from app.agents.arbitrator_agent import arbitrator_agent
from app.agents.dossier_agent import dossier_agent
from app.agents.submission_agent import submission_agent
from app.agents.field_agent import field_agent
from app.agents.blockchain_agent import blockchain_agent
from app.agents.pitch_deck_agent import pitch_deck_agent
from app.agents.value_engineering_agent import value_engineering_agent
from app.agents.submittal_agent import submittal_agent
from app.agents.ipc_agent import ipc_agent

class OrchestrationState(TypedDict, total=False):
    # Inputs — must be declared: LangGraph silently drops undeclared input keys.
    project_id: str
    tender_id: int
    client_name: str
    rfp_documents: List[str]
    methodology_documents: List[str]
    schedule_file: str
    boq_file: str
    institutional_memory_output: Dict[str, Any]
    rfp_output: Dict[str, Any]
    boq_output: Dict[str, Any]
    generated_proposal_output: List[Dict[str, Any]]
    methodology_output: Dict[str, Any]
    calculation_output: Dict[str, Any]
    geotech_output: Dict[str, Any]
    p6_output: Dict[str, Any]
    commercial_output: Dict[str, Any]
    vendor_output: Dict[str, Any]
    standards_output: Dict[str, Any]
    qaqc_output: Dict[str, Any]
    hse_output: Dict[str, Any]
    bim_output: Dict[str, Any]
    discrepancy_output: Dict[str, Any]
    cross_exam_output: Dict[str, Any]
    rfp_compliance_matrix: Dict[str, Any]
    red_team_output: Dict[str, Any]
    contract_output: Dict[str, Any]
    etimad_output: Dict[str, Any]
    claims_output: Dict[str, Any]
    llm_metrics_output: Dict[str, Any]
    arbitrator_output: Dict[str, Any]
    dossier_output: Dict[str, Any]
    dispatch_output: Dict[str, Any]
    field_output: Dict[str, Any]
    blockchain_output: Dict[str, Any]
    pitch_deck_output: Dict[str, Any]
    ve_output: Dict[str, Any]
    ve_matrix: Dict[str, Any]
    ve_summary: Dict[str, Any]
    submittal_output: Dict[str, Any]
    tender_evaluation: Dict[str, Any]
    risk_mitigation_output: Dict[str, Any]
    ipc_output: Dict[str, Any]

def build_orchestrator():
    graph = StateGraph(OrchestrationState)
    
    # Add Nodes
    graph.add_node("learning", learning_agent)
    graph.add_node("client_rfp", client_rfp_agent)
    graph.add_node("client_boq", client_boq_agent)
    graph.add_node("proposal_builder", proposal_builder_agent)
    graph.add_node("methodology", methodology_agent)
    graph.add_node("calculation", calculation_agent)
    graph.add_node("geotech", geotech_agent)
    graph.add_node("p6_schedule", p6_dcma_agent)
    graph.add_node("commercial", commercial_agent)
    graph.add_node("vendor", vendor_agent)
    graph.add_node("standards", standards_agent)
    graph.add_node("submittal", submittal_agent)
    graph.add_node("value_engineering", value_engineering_agent)
    graph.add_node("qaqc_deep", qaqc_deep_agent)
    graph.add_node("field", field_agent)
    graph.add_node("bim", bim_agent)
    graph.add_node("cross_exam", cross_exam_agent)
    graph.add_node("red_team", red_team_agent)
    graph.add_node("contract", contract_agent)
    graph.add_node("etimad", etimad_agent)
    graph.add_node("claims", claims_agent)
    graph.add_node("ipc", ipc_agent)
    graph.add_node("arbitrator", arbitrator_agent)
    graph.add_node("dossier", dossier_agent)
    graph.add_node("submission", submission_agent)
    graph.add_node("pitch_deck", pitch_deck_agent)
    graph.add_node("blockchain", blockchain_agent)
    
    # Define parallel entry edge routing via StateGraph Fan-out architecture
    graph.set_entry_point("learning")
    
    graph.add_edge("learning", "client_rfp")
    graph.add_edge("client_rfp", "client_boq")
    graph.add_edge("client_boq", "proposal_builder")
    graph.add_edge("proposal_builder", "methodology")
    graph.add_edge("methodology", "calculation")
    graph.add_edge("calculation", "geotech")
    graph.add_edge("geotech", "p6_schedule")
    graph.add_edge("p6_schedule", "commercial")
    graph.add_edge("commercial", "vendor")
    graph.add_edge("vendor", "standards")
    graph.add_edge("standards", "submittal")
    graph.add_edge("submittal", "tender_evaluation")
    # tender_evaluation conditionally routes -> risk_mitigation | value_engineering (supervisor)
    graph.add_edge("value_engineering", "qaqc_deep")
    graph.add_edge("qaqc_deep", "field")
    graph.add_edge("field", "bim")
    graph.add_edge("bim", "cross_exam")
    graph.add_edge("cross_exam", "red_team")
    graph.add_edge("red_team", "contract")
    graph.add_edge("contract", "etimad")
    graph.add_edge("etimad", "claims")
    graph.add_edge("claims", "ipc")
    graph.add_edge("ipc", "arbitrator")
    graph.add_edge("arbitrator", "dossier")
    graph.add_edge("dossier", "submission")
    graph.add_edge("submission", "pitch_deck")
    graph.add_edge("pitch_deck", "blockchain")
    graph.add_edge("blockchain", END)

    from app.agents.supervisor import register_supervisor
    register_supervisor(graph)

    return graph.compile()
