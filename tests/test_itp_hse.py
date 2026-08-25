import unittest
from app.parsers.itp_hse_engine import ItpHseEngine

class TestItpHseEngine(unittest.TestCase):
    def test_itp_generation_for_concrete(self):
        boq = [{"description": "Ready-mix concrete for raft foundation"}]
        itp_register = ItpHseEngine.generate_itp(boq)
        
        # Verify that concrete items automatically trigger mandatory tests
        activities = [item["activity"] for item in itp_register]
        self.assertIn("Structural Rebar Inspection", activities)
        self.assertIn("Compressive Strength Testing", activities)
        
        # Verify Hold Point assignment
        hold_point = next(i for i in itp_register if i["activity"] == "Compressive Strength Testing")
        self.assertEqual(hold_point["checkpoint"], "Hold Point")
        self.assertEqual(hold_point["reference"], "ASTM C39")

    def test_hira_generation_for_deep_trench(self):
        boq = [{"description": "Deep trench excavation for utility lines"}]
        hira_register = ItpHseEngine.compute_hira(boq)
        
        # Verify Trenching creates a High-Risk entry
        trench_risk = next(h for h in hira_register if "Trench" in h["task"])
        
        self.assertEqual(trench_risk["probability"], 4)
        self.assertEqual(trench_risk["severity"], 4)
        self.assertEqual(trench_risk["risk_score"], 16) # High Risk threshold
        
        # Verify strict mitigation string includes Shoring
        self.assertIn("shoring", trench_risk["mitigation"].lower())

if __name__ == "__main__":
    unittest.main()
