import unittest
from app.parsers.reconciliation_engine import ReconciliationEngine
from app.agents.cross_exam_agent import cross_exam_agent

class TestReconciliationEngine(unittest.TestCase):
    def test_variance_calculation_high_severity(self):
        rates = {"Excavation": 500} # 500 units/day
        boq = {"Excavation": 10000} # 10000 units total -> expected 20 days
        p6 = {"Excavation": 12} # Scheduled 12 days -> variance = 8/20 = 40%

        discrepancies = ReconciliationEngine.calculate_variances(rates, boq, p6)
        
        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0]["activity"], "Excavation")
        self.assertEqual(discrepancies[0]["variance_percent"], 40.0)
        self.assertEqual(discrepancies[0]["severity"], "High")
        self.assertIn("exceeds 10% threshold", discrepancies[0]["conflict"])

    def test_variance_calculation_no_flag_under_threshold(self):
        rates = {"Concrete": 100} # expected 10 days
        boq = {"Concrete": 1000} 
        p6 = {"Concrete": 10} # 0 variance

        discrepancies = ReconciliationEngine.calculate_variances(rates, boq, p6)
        self.assertEqual(len(discrepancies), 0)

    def test_cross_exam_agent_integration(self):
        state = {}
        result = cross_exam_agent(state)
        discrepancies = result.get("discrepancy_output", {}).get("discrepancies", [])
        
        # Excavation mock in cross_exam_agent: 10000 / 400 = 25 days expected vs 15 scheduled (40% variance)
        self.assertTrue(any(d.get("activity") == "Excavation" for d in discrepancies))
        self.assertEqual(discrepancies[0]["variance_percent"], 40.0)

if __name__ == "__main__":
    unittest.main()
