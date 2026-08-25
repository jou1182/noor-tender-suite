import unittest
from app.services.submission_dispatch_service import SubmissionDispatchService
from app.core.crypto_sealer import CryptoSealer

class TestSubmissionDispatch(unittest.TestCase):
    def test_valid_submission_dispatch_issues_certificate(self):
        # Generate valid mock signatures
        signatures = {
            "technical_methodology": "hash_tech_123",
            "commercial_boq": "hash_comm_456",
            "executive_summary": "hash_exec_789"
        }
        # Cryptographically seal them properly
        master_hash = CryptoSealer.hash_payload(signatures)
        
        dossier_data = {
            "manifest": {
                "signatures": signatures,
                "master_hash": master_hash
            }
        }
        
        result = SubmissionDispatchService.execute_preflight_checks(dossier_data)
        
        # Verify valid submission grants a certificate
        self.assertEqual(result["dispatch_status"], "CERTIFIED_READY")
        self.assertIn("certificate_id", result)
        self.assertTrue(result["certificate_id"].startswith("CERT-"))

    def test_missing_mandatory_doc_triggers_safety_lockout(self):
        # Simulate a missing critical technical methodology
        signatures = {
            "commercial_boq": "hash_comm_456",
            "technical_methodology": "MISSING" # FATAL ERROR
        }
        master_hash = CryptoSealer.hash_payload(signatures)
        
        dossier_data = {
            "manifest": {
                "signatures": signatures,
                "master_hash": master_hash
            }
        }
        
        result = SubmissionDispatchService.execute_preflight_checks(dossier_data)
        
        # Verify the dispatcher explicitly blocks submission
        self.assertEqual(result["dispatch_status"], "ABORTED_SAFETY_LOCKOUT")
        self.assertIn("CRITICAL: Technical Methodology Package Missing.", result["errors"])

    def test_tampered_hash_triggers_safety_lockout(self):
        signatures = {
            "technical_methodology": "hash_tech_123",
            "commercial_boq": "hash_comm_456",
        }
        # Simulate tampering by providing a corrupted master hash
        dossier_data = {
            "manifest": {
                "signatures": signatures,
                "master_hash": "a_corrupted_fake_hash_string"
            }
        }
        
        result = SubmissionDispatchService.execute_preflight_checks(dossier_data)
        
        self.assertEqual(result["dispatch_status"], "ABORTED_SAFETY_LOCKOUT")
        self.assertIn("CRITICAL: Cryptographic Hash Tamper Detected. Immutable seal broken.", result["errors"])

if __name__ == "__main__":
    unittest.main()
