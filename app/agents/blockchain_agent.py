from typing import Dict, Any
from app.core.blockchain_ledger import BlockchainLedger
import time

# Singleton volatile ledger for the orchestration session. 
# In a production environment, this integrates directly with an external Hyperledger Fabric or immutable Postgres cluster.
GLOBAL_LEDGER = BlockchainLedger()

def blockchain_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enterprise Blockchain Compliance Agent.
    Executes at the termination of the LangGraph swarm to extract critical platform events
    (Dossier Seals, Field NCRs, DCMA Scores) and immutably anchors them into a block.
    """
    print("--- [AGENT] Blockchain Compliance Ledger Anchoring ---")
    
    # Extract structural milestones for immutable persistence
    dossier = state.get("dossier_output", {}).get("manifest", {})
    dossier_hash = dossier.get("master_hash", "UNAVAILABLE")
    
    field_data = state.get("field_output", {})
    ncrs_issued = len(field_data.get("ncrs_issued", [])) if field_data else 0
    
    p6_data = state.get("p6_output", {})
    dcma_score = p6_data.get("overall_status", "UNAVAILABLE")
    
    # Batch transactions for the block
    GLOBAL_LEDGER.add_transaction({
        "event_type": "DOSSIER_SEALED", 
        "payload_hash": dossier_hash,
        "timestamp": time.time()
    })
    
    if ncrs_issued > 0:
        GLOBAL_LEDGER.add_transaction({
            "event_type": "FIELD_NCRS_ISSUED", 
            "ncr_count": ncrs_issued,
            "timestamp": time.time()
        })
        
    GLOBAL_LEDGER.add_transaction({
        "event_type": "DCMA_VERIFIED", 
        "compliance_status": dcma_score,
        "timestamp": time.time()
    })
    
    # Mine and commit the block onto the chain
    new_block = GLOBAL_LEDGER.commit_block()
    
    return {
        "blockchain_output": {
            "block_height": new_block.index,
            "merkle_root": new_block.merkle_root,
            "block_hash": new_block.hash,
            "previous_hash": new_block.previous_hash,
            "transactions": new_block.transactions,
            "ledger_integrity_verified": GLOBAL_LEDGER.verify_chain_integrity(),
            "timestamp": new_block.timestamp
        }
    }
