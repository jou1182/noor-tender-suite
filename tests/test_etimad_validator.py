import unittest
from app.parsers.etimad_validator import EtimadValidator

class TestEtimadValidator(unittest.TestCase):
    def test_compliant_submission(self):
        payload = {
            "documents": {
                "bank_guarantee": {"validity_days": 120},
                "classification_certificate": True,
                "local_content_score": 25.0
            }
        }
        result = EtimadValidator.validate_submission(payload)
        self.assertEqual(result["status"], "COMPLIANT")
        self.assertEqual(result["readiness_score"], 100.0)
        self.assertEqual(len(result["missing_mandatory_attachments"]), 0)

    def test_non_compliant_submission(self):
        payload = {
            "documents": {
                "bank_guarantee": {"validity_days": 60}, # Invalid (requires 90)
                "classification_certificate": False, # Missing entirely
                "local_content_score": 5.0 # Low (requires 10)
            }
        }
        result = EtimadValidator.validate_submission(payload)
        self.assertEqual(result["status"], "NON-COMPLIANT")
        self.assertLess(result["readiness_score"], 50.0)
        self.assertEqual(len(result["missing_mandatory_attachments"]), 3)
        self.assertIn("Initial Bank Guarantee (Missing or < 90 days validity)", result["missing_mandatory_attachments"])

if __name__ == "__main__":
    unittest.main()
