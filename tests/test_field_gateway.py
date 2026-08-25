import unittest
from app.services.field_gateway_service import FieldGatewayService

class TestFieldGateway(unittest.TestCase):
    def test_multimodal_defect_recognition_and_ncr_generation(self):
        # Provide raw, unstructured inputs simulating a site engineer's mobile app transmission
        voice_memo = "We are observing severe cracks forming on the primary retaining wall sequence."
        vision_tags = ["cracks", "missing_shoring"]
        
        # Process the data through the gateway
        result = FieldGatewayService.process_multimodal_field_report(voice_memo, vision_tags)
        
        # Verify accurate parsing and defect counting
        self.assertEqual(result["total_defects"], 2)
        self.assertEqual(len(result["ncrs_issued"]), 2)
        
        # Verify SBC Code cross-referencing injected correctly
        sbc_codes = [ncr["sbc_violation_code"] for ncr in result["ncrs_issued"]]
        self.assertIn("SBC-304", sbc_codes)
        self.assertIn("OSHA-1926", sbc_codes)
        
        # Verify strict NCR Formatting
        for ncr in result["ncrs_issued"]:
            self.assertTrue(ncr["ncr_id"].startswith("NCR-"))
            self.assertEqual(ncr["status"], "OPEN")
            self.assertTrue("remediation" in ncr["required_action"])

    def test_clean_site_generates_zero_ncrs(self):
        voice_memo = "Site conditions are clear. Rebar installation progressing normally."
        vision_tags = ["clean_site", "rebar_verified"]
        
        result = FieldGatewayService.process_multimodal_field_report(voice_memo, vision_tags)
        
        self.assertEqual(result["total_defects"], 0)
        self.assertEqual(len(result["ncrs_issued"]), 0)

if __name__ == "__main__":
    unittest.main()
