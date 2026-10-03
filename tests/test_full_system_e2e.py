import unittest
from typing import Dict, Any

from app.agents.vendor_agent import vendor_agent
from app.agents.qaqc_deep_agent import qaqc_deep_agent
from app.agents.p6_dcma_agent import p6_dcma_agent
from app.agents.dossier_agent import dossier_agent

class TestFullSystemE2E(unittest.TestCase):
    def test_end_to_end_pipeline_simulation(self):
        import os, tempfile
        from tests.conftest import SAMPLE_XER_TEXT
        xer = os.path.join(tempfile.mkdtemp(), "schedule.xer")
        with open(xer, "w", encoding="utf-8") as fh:
            fh.write(SAMPLE_XER_TEXT)

        """
        Simulates an End-to-End master integration run traversing the critical path of the LangGraph swarm.
        Verifies that downstream data cleanly maps from BOQ extraction through to cryptographic sealing.
        """
        # Initialize an empty Orchestration State dict
        master_state: Dict[str, Any] = {"schedule_file": xer}
        
        # 1. Vendor & Procurement Evaluation
        vendor_res = vendor_agent(master_state)
        self.assertIn("vendor_output", vendor_res)
        master_state.update(vendor_res) # Append to state
        
        # 2. QA/QC ITPs & HSE Risk Matrix Generation
        qaqc_res = qaqc_deep_agent(master_state)
        self.assertIn("qaqc_output", qaqc_res)
        self.assertIn("hse_output", qaqc_res)
        master_state.update(qaqc_res)
        
        # 3. P6 DCMA Integrity Checks & Monte Carlo Probability
        p6_res = p6_dcma_agent(master_state)
        self.assertIn("p6_output", p6_res)
        master_state.update(p6_res)
        
        # 4. Master Dossier Assembly & Cryptographic Sealing
        dossier_res = dossier_agent(master_state)
        self.assertIn("dossier_output", dossier_res)
        
        # Final E2E Integrity Assertions
        dossier = dossier_res["dossier_output"]
        
        # Check Submission Status
        self.assertEqual(dossier["dossier_status"], "READY_FOR_SUBMISSION")
        
        # Validate Cryptographic Tamper-Proofing (SHA-256)
        manifest = dossier["manifest"]
        self.assertIn("master_hash", manifest)
        self.assertEqual(len(manifest["master_hash"]), 64)
        
        # Validate correct pipeline section stitching
        compiled_sections = dossier["sections_compiled"]
        self.assertIn("quality_safety_itp_hira", compiled_sections)
        self.assertIn("dcma_p6_schedule", compiled_sections)
        
        # Validate deterministic missing output flagging (Because ETIMAD wasn't injected)
        self.assertEqual(manifest["signatures"]["etimad_compliance"], "MISSING")
        # Validate successfully captured signature from QAQC node
        self.assertNotEqual(manifest["signatures"]["quality_safety_itp_hira"], "MISSING")

if __name__ == "__main__":
    unittest.main()
