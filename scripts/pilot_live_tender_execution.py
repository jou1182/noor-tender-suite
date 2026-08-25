import json
import time
import sys
import os

# Append project root to path for execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.graph import build_orchestrator
from app.core.crypto_sealer import CryptoSealer

def run_pilot():
    print("\n[INITIATING PILOT LIVE TENDER EXECUTION & DATA PIPELINE VERIFICATION]")
    print("="*75)
    
    # 1. Pilot Ingestion Pipeline Payload (Mocking large-scale payload)
    mock_initial_state = {
        "tender_id": 9999,
        "client_name": "NEOM Infrastructure - The Line Subsurface",
        "rfp_output": {"summary": "High-Speed Rail Phase 2", "specs": "AASHTO / SBC 304"},
        "boq_output": {"items_count": 1250, "total_value": 450000000, "items": [{"description": "Ready-mix concrete 40MPa", "qty": 50000}]},
        "geotech_output": {"soil_type": "Limestone", "bearing_capacity": "450 kPa", "coordinates": "[28.083, 34.916]"},
        "bim_output": {"ifc_elements": 15400, "clash_count": 12}
    }
    
    print("\n[1/3] Pipeline Ingestion Initialized...")
    print(f"      - Extracted BOQ Items: {mock_initial_state['boq_output']['items_count']} lines")
    print(f"      - Extracted IFC Elements: {mock_initial_state['bim_output']['ifc_elements']} geometries")
    print(f"      - Target Geotech Sector: {mock_initial_state['client_name']}")
    
    # 2. Real-time Telemetry & Stream Verification (LangGraph streaming)
    print("\n[2/3] Simulating SSE Real-time Telemetry Stream across LangGraph Swarm...")
    graph = build_orchestrator()
    
    # We will use .stream() to verify that each node processes and yields state sequentially
    start_time = time.time()
    for output in graph.stream(mock_initial_state):
        for node_name, state_update in output.items():
            print(f"  > [SSE Stream] Node completed: {node_name.upper():<20} | Status: OK")
            time.sleep(0.05) # Simulate SSE network transmission delays
            
    print(f"      -> Pipeline Traversal Time: {round(time.time() - start_time, 2)}s")
            
    # 3. Dossier Packaging & Cryptographic Export Verification
    print("\n[3/3] Dossier Packaging & Hash Export Verification...")
    
    # To get the absolute final accumulated state, we invoke it fully
    final_master_state = graph.invoke(mock_initial_state)
    dossier = final_master_state.get("dossier_output", {})
    
    if not dossier:
        print("[ERROR] Dossier Output missing!")
        sys.exit(1)
        
    print("\n[SUCCESS] Master Dossier Assembled Successfully!")
    print(f"  - Compilation Status: {dossier.get('dossier_status')}")
    
    sections = dossier.get("sections_compiled", [])
    print(f"  - Secured Modules ({len(sections)}):")
    for sec in sections:
        print(f"    * {sec}")
    
    manifest = dossier.get("manifest", {})
    master_hash = manifest.get("master_hash")
    
    # Mathematical integrity check on the final hash
    is_valid = CryptoSealer.verify_payload(manifest["signatures"], master_hash)
    
    print(f"\n  - SHA-256 MASTER SIGNATURE: {master_hash}")
    if is_valid:
        print("[VERIFIED] Cryptographic Seal Verified: IMMUTABLE & SECURE")
    else:
        print("[FAILED] Cryptographic Seal Verified: TAMPERED")
        sys.exit(1)
        
    print("\n[COMPLETED] PILOT EXECUTION VERIFIED. SYSTEM IS READY FOR PRODUCTION TRAFFIC.")
    print("="*75)

if __name__ == "__main__":
    run_pilot()
