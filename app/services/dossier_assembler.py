from typing import Dict, Any
from app.core.crypto_sealer import CryptoSealer

class DossierAssembler:
    @staticmethod
    def assemble_master_dossier(orchestration_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compiles the disjointed multi-agent intelligence outputs into a unified, 
        submission-ready Technical Proposal Dossier, protected by cryptographic hashes.
        """
        
        # Extract and structurally map standard sections
        sections = {
            "executive_summary": orchestration_state.get("rfp_output", {}),
            "commercial_boq": orchestration_state.get("boq_output", {}),
            "technical_methodology": orchestration_state.get("generated_proposal_output", {}),
            "engineering_calculations": orchestration_state.get("calculation_output", {}),
            "dcma_p6_schedule": orchestration_state.get("p6_output", {}),
            "quality_safety_itp_hira": orchestration_state.get("qaqc_output", {}),
            "etimad_compliance": orchestration_state.get("etimad_output", {})
        }
        
        # Seal the payload immutably
        manifest = CryptoSealer.generate_manifest(sections)
        
        return {
            "dossier_status": "READY_FOR_SUBMISSION",
            "sections_compiled": list(manifest["signatures"].keys()),
            "manifest": manifest,
            "dossier_payload": sections
        }
