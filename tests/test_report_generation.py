import unittest
import os
from app.services.executive_report_service import ExecutiveReportService

class TestReportGeneration(unittest.TestCase):
    def test_pdf_generation(self):
        tender_data = {
            "id": 999,
            "score": 85.5,
            "records": [
                {"clause_code": "SBC-303", "status": "Pass", "gap_analysis": "None"}
            ]
        }
        output_path = "test_report.pdf"
        ExecutiveReportService.generate_pdf_report(tender_data, output_path)
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)
        os.remove(output_path)

    def test_docx_generation(self):
        rfis = ["Draft RFI 1: Clarify excavation limits.", "Draft RFI 2: Specify concrete grade."]
        output_path = "test_rfis.docx"
        ExecutiveReportService.generate_rfi_docx(rfis, output_path)
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)
        os.remove(output_path)

if __name__ == "__main__":
    unittest.main()
