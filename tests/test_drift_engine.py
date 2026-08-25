import unittest
from app.parsers.drift_engine import DriftEngine

class TestDriftEngine(unittest.TestCase):
    def test_text_and_boq_drift(self):
        base_text = "Clause 1.0: Excavation is 5m deep.\nClause 2.0: Concrete grade C30."
        addendum_text = "Clause 1.0: Excavation is 7m deep.\nClause 2.0: Concrete grade C30."
        
        base_boq = {"Excavation": 5000}
        addendum_boq = {"Excavation": 7000, "Steel": 100}
        
        result = DriftEngine.compare_versions(base_text, addendum_text, base_boq, addendum_boq)
        
        # Verify text diffs
        additions = [c["content"] for c in result["text_changes"] if c["type"] == "addition"]
        self.assertIn("Clause 1.0: Excavation is 7m deep.", additions)
        
        # Verify impacted clause flag
        self.assertIn("1.0:", result["impacted_clauses"])
        
        # Verify BOQ variance math
        self.assertEqual(len(result["boq_variances"]), 2)
        exc_delta = next(v for v in result["boq_variances"] if v["item"] == "Excavation")
        self.assertEqual(exc_delta["delta"], 2000.0)
        
        steel_delta = next(v for v in result["boq_variances"] if v["item"] == "Steel")
        self.assertEqual(steel_delta["delta"], 100.0)

if __name__ == "__main__":
    unittest.main()
