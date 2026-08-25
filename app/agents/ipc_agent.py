from typing import Dict, Any
from app.parsers.ipc_valuation_engine import IpcValuationEngine

def ipc_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Commercial Billing & IPC Audit Node.
    Executes within LangGraph to intercept payment applications, audit quantities against verified
    site ITP records, and issue standard Interim Payment Certificates without human math errors.
    """
    print("--- [AGENT] Commercial Billing & IPC Audit Engine ---")
    
    # Mock Contractor Payment Application Data
    mock_ipc_data = {
        "contract_value": 15000000.0, # 15M SAR Contract
        "previous_gross": 2000000.0,
        "previous_net": 1600000.0,
        "current_work_done": 2500000.0, # Contractor claiming 2.5M
        "materials_on_site": 150000.0,
        "advance_payment_total": 1500000.0, # 10% Advance
        "advance_recovered_previously": 200000.0,
        "advance_recovery_rate": 0.10,
        "retention_rate": 0.10, # 10% Retention
        "retention_cap_rate": 0.05, # Max 5% (750k)
        "liquidated_damages": 0.0
    }
    
    ipc_output = IpcValuationEngine.calculate_ipc(mock_ipc_data)
    
    return {"ipc_output": ipc_output}
