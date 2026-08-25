import unittest
import os
from app.models.tender_models import ComplianceRecord
from app.services.report_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.records = [
            ComplianceRecord(
                clause_code="REQ-1",
                requirement="Safety protocols",
                status="Compliant",
                severity="Low",
                gap_analysis=""
            ),
            ComplianceRecord(
                clause_code="REQ-2",
                requirement="Budget limits",
                status="Non-Compliant",
                severity="High",
                gap_analysis="Missing 20% of funds"
            )
        ]

    def test_json_report(self):
        json_str = ReportGenerator.generate_json_report(self.records)
        self.assertIn("REQ-1", json_str)
        self.assertIn("Non-Compliant", json_str)

    def test_excel_report(self):
        output_path = "test_matrix.xlsx"
        ReportGenerator.generate_excel_matrix(self.records, output_path)
        self.assertTrue(os.path.exists(output_path))
        os.remove(output_path)

if __name__ == "__main__":
    unittest.main()
