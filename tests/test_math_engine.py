import unittest
from app.parsers.engineering_math_engine import EngineeringMathEngine

class TestEngineeringMathEngine(unittest.TestCase):
    def test_manning_capacity_undersized(self):
        # 0.5m pipe with 0.01 slope and 0.013 roughness -> Capacity ~0.53 m3/s
        # Required flow is 1.2 m3/s, so it should fail
        result = EngineeringMathEngine.check_manning_capacity(0.5, 0.01, 0.013, 1.2)
        self.assertFalse(result["is_safe"])
        self.assertIn("undersized", result["warning"].lower())
        self.assertEqual(result["required_value"], 1.2)
        self.assertLess(result["calculated_value"], 1.2)
        
    def test_manning_capacity_sufficient(self):
        # 1.0m pipe with 0.01 slope -> Capacity ~3.0 m3/s
        result = EngineeringMathEngine.check_manning_capacity(1.0, 0.01, 0.013, 1.2)
        self.assertTrue(result["is_safe"])
        self.assertIn("sufficient", result["warning"].lower())

    def test_concrete_durability_fails(self):
        # Cement 320 (req 350), w/c 0.50 (req <= 0.45)
        result = EngineeringMathEngine.check_concrete_durability(320, 0.50)
        self.assertFalse(result[0]["is_safe"]) # Cement content check
        self.assertFalse(result[1]["is_safe"]) # W/C check
        
    def test_concrete_durability_passes(self):
        result = EngineeringMathEngine.check_concrete_durability(400, 0.40)
        self.assertTrue(result[0]["is_safe"])
        self.assertTrue(result[1]["is_safe"])

    def test_soil_bearing_capacity(self):
        # SBC 303: min FOS = 3.0
        result_unsafe = EngineeringMathEngine.check_soil_bearing(200, 500) # FOS = 2.5
        self.assertFalse(result_unsafe["is_safe"])
        self.assertIn("too low", result_unsafe["warning"])
        
        result_safe = EngineeringMathEngine.check_soil_bearing(100, 500) # FOS = 5.0
        self.assertTrue(result_safe["is_safe"])

if __name__ == "__main__":
    unittest.main()
