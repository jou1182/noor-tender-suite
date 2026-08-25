import unittest
from datetime import datetime
from app.parsers.tia_engine import TIAEngine

class TestTIAEngine(unittest.TestCase):
    def test_calculate_eot(self):
        baseline = datetime(2025, 1, 1)
        delays = [10, 5, 20] # total 35 days
        new_date, eot = TIAEngine.calculate_eot(baseline, delays)
        
        self.assertEqual(eot, 35)
        self.assertEqual(new_date.strftime("%Y-%m-%d"), "2025-02-05")

    def test_evaluate_entitlement_safe(self):
        event = datetime(2026, 1, 1)
        notice = datetime(2026, 1, 20) # 19 days elapsed
        result = TIAEngine.evaluate_entitlement(event, notice)
        
        self.assertFalse(result["is_time_barred"])
        self.assertEqual(result["days_elapsed"], 19)
        self.assertIn("successfully within", result["warning"])

    def test_evaluate_entitlement_time_barred(self):
        event = datetime(2026, 1, 1)
        notice = datetime(2026, 2, 5) # 35 days elapsed
        result = TIAEngine.evaluate_entitlement(event, notice)
        
        self.assertTrue(result["is_time_barred"])
        self.assertEqual(result["days_elapsed"], 35)
        self.assertIn("CRITICAL RISK", result["warning"])

if __name__ == "__main__":
    unittest.main()
