import unittest
from app.services.comparative_service import ComparativeService

class MockTender:
    def __init__(self, id, name, score, budget):
        self.id = id
        self.client_name = name
        self.technical_score = score
        self.audit_metadata = {"boq_output": {"boq_financials": {"total_budget": budget}}}

class TestBenchmarking(unittest.TestCase):
    def test_benchmarking_engine(self):
        tenders = [
            MockTender(1, "Alpha Const.", 85.0, 5000000),
            MockTender(2, "Beta Build", 92.5, 4800000),
            MockTender(3, "Gamma Group", 60.0, 7000000)
        ]
        
        result = ComparativeService.generate_benchmark(tenders)
        
        # Check rankings sorting
        self.assertEqual(result["rankings"][0]["tender_id"], 2) # Beta Build is 1st
        self.assertEqual(result["rankings"][1]["tender_id"], 1) # Alpha Const is 2nd
        self.assertEqual(result["rankings"][2]["tender_id"], 3) # Gamma Group is 3rd
        
        # Check mean calculation (85 + 92.5 + 60) / 3 = 79.166...
        self.assertAlmostEqual(result["mean_score"], 79.17, places=2)

        # Check outlier detection (Gamma Group should be flagged due to being > 1 std dev away)
        self.assertIn(3, result["outliers"])

if __name__ == "__main__":
    unittest.main()
