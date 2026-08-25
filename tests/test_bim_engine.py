import unittest
from app.parsers.bim_ifc_engine import BimIfcEngine

class TestBimIfcEngine(unittest.TestCase):
    def test_audit_boq_variances_flags_over_5_percent(self):
        bim_quantities = {"Concrete": 110.0, "Steel": 100.0}
        boq_quantities = {"Concrete": 100.0, "Steel": 98.0}
        
        variances = BimIfcEngine.audit_boq_variances(bim_quantities, boq_quantities)
        
        # Concrete variance = (110 - 100) / 100 = +10.0% -> Should be strictly flagged
        concrete = next(v for v in variances if v["item"] == "Concrete")
        self.assertTrue(concrete["flagged"])
        self.assertEqual(concrete["variance_pct"], 10.0)
        self.assertIn("AUDIT WARNING", concrete["warning"])
        
        # Steel variance = (100 - 98) / 98 = ~+2.04% -> Should NOT be flagged
        steel = next(v for v in variances if v["item"] == "Steel")
        self.assertFalse(steel["flagged"])
        self.assertIn("Within acceptable", steel["warning"])

if __name__ == "__main__":
    unittest.main()
