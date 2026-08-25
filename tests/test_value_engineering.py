import unittest
from app.parsers.value_engineering_engine import ValueEngineeringEngine

class TestValueEngineering(unittest.TestCase):
    def test_valid_sbc_substitutions_calculate_savings(self):
        # Provide structural BOQ elements matching the catalog
        boq = [
            {"description": "Standard Portland Cement", "qty": 100, "unit_rate": 200}, # Original: 20000, Savings: 12.5% = 2500
            {"description": "Grade 60 Steel Rebar", "qty": 10, "unit_rate": 3000}      # Original: 30000, Savings: 8% = 2400
        ]
        
        result = ValueEngineeringEngine.evaluate_boq(boq)
        
        # Verify strict mathematical accumulation
        self.assertEqual(result["total_proposals"], 2)
        self.assertEqual(result["total_original_cost_sar"], 50000)
        self.assertEqual(result["total_projected_savings_sar"], 4900)
        self.assertEqual(result["savings_percentage"], 9.8) # (4900 / 50000) * 100
        
    def test_invalid_sbc_substitution_rejected_by_engine(self):
        # Provide a BOQ element explicitly mapped as SBC non-compliant
        boq = [
            {"description": "Non-Compliant Glass", "qty": 100, "unit_rate": 500} # Original: 50000
        ]
        
        result = ValueEngineeringEngine.evaluate_boq(boq)
        
        # Verify the authorization gate strictly blocked the proposal
        self.assertEqual(result["total_proposals"], 0)
        self.assertEqual(result["total_projected_savings_sar"], 0)
        self.assertEqual(len(result["proposals"]), 0)

if __name__ == "__main__":
    unittest.main()
