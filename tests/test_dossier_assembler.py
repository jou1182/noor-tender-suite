import unittest
from app.core.crypto_sealer import CryptoSealer
from app.services.dossier_assembler import DossierAssembler

class TestDossierAssembler(unittest.TestCase):
    def test_cryptographic_integrity_sealer(self):
        payload = {"project": "NEOM Line Section 4", "value_sar": 50000000}
        
        # Validate deterministic Hash Generation
        secure_hash = CryptoSealer.hash_payload(payload)
        self.assertEqual(len(secure_hash), 64) # Validate SHA-256 precise string length
        
        # Validate True Integrity Match
        self.assertTrue(CryptoSealer.verify_payload(payload, secure_hash))
        
        # Validate Tamper Detection Failures
        tampered_payload = {"project": "NEOM Line Section 4", "value_sar": 55000000}
        self.assertFalse(CryptoSealer.verify_payload(tampered_payload, secure_hash))

    def test_master_dossier_assembly(self):
        # Supply a disjointed mock graph orchestration state
        mock_state = {
            "rfp_output": {"project_summary": "High-Speed Rail"},
            "calculation_output": {"safety_factor": 1.5, "warnings": []},
            # Deliberately exclude ETIMAD and P6 modules to simulate missing compilation
        }
        
        dossier = DossierAssembler.assemble_master_dossier(mock_state)
        
        self.assertEqual(dossier["dossier_status"], "READY_FOR_SUBMISSION")
        self.assertIn("executive_summary", dossier["sections_compiled"])
        self.assertIn("dcma_p6_schedule", dossier["sections_compiled"])
        
        manifest = dossier["manifest"]
        
        # Verify Master Signature Generation
        self.assertIn("master_hash", manifest)
        self.assertEqual(len(manifest["master_hash"]), 64)
        
        # Verify Missing Handlers
        self.assertEqual(manifest["signatures"]["dcma_p6_schedule"], "MISSING")
        self.assertEqual(manifest["signatures"]["etimad_compliance"], "MISSING")
        
        # Verify Successfully Extracted Blocks
        self.assertNotEqual(manifest["signatures"]["executive_summary"], "MISSING")
        self.assertNotEqual(manifest["signatures"]["engineering_calculations"], "MISSING")

if __name__ == "__main__":
    unittest.main()
