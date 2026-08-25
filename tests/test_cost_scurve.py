import unittest
from app.parsers.cost_scurve_engine import CostSCurveEngine

class TestCostSCurveEngine(unittest.TestCase):
    def test_scurve_generation(self):
        activities = [
            {"item": "A", "cost": 100, "early_start": 0, "late_start": 0, "duration": 2}, # 50 per month
            {"item": "B", "cost": 200, "early_start": 1, "late_start": 2, "duration": 2}  # 100 per month
        ]
        # Total cost = 300
        scurve = CostSCurveEngine.generate_scurve(activities, 3)
        
        # Check final month explicitly resolves to exactly 100.0%
        self.assertEqual(scurve[-1]["cum_early_pct"], 100.0)
        self.assertEqual(scurve[-1]["cum_late_pct"], 100.0)
        
        # Verify Month 1 distributions
        self.assertEqual(scurve[0]["early_cost"], 50)
        self.assertEqual(scurve[0]["late_cost"], 50)
        
        # Verify Month 2 distributions (Act A + Act B early)
        self.assertEqual(scurve[1]["early_cost"], 150) # 50 + 100
        self.assertEqual(scurve[1]["late_cost"], 50)   # Act B hasn't started late

    def test_detect_front_loading(self):
        activities = [
            {"item": "Mob", "unit_rate": 500, "early_start": 0},
            {"item": "Excavation", "unit_rate": 100, "early_start": 1}
        ]
        baselines = {"Mob": 200, "Excavation": 95}
        
        warnings = CostSCurveEngine.detect_front_loading(activities, baselines)
        # Only Mob should trigger as it is >20% over baseline (150% over)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["item"], "Mob")
        self.assertEqual(warnings[0]["variance_pct"], 150.0)

if __name__ == "__main__":
    unittest.main()
