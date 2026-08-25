import unittest
import numpy as np
from app.parsers.dcma_engine import DCMAEngine
from app.parsers.monte_carlo_engine import MonteCarloEngine

class TestDCMAAndMonteCarlo(unittest.TestCase):
    def test_dcma_metrics_failure_thresholds(self):
        # Create a deliberately flawed project schedule vector mapping
        activities = [
            {"predecessors": [], "successors": [], "lag": -2, "total_float": 50, "constraint_type": "Must Finish On"}
        ] * 10 
        
        res = DCMAEngine.evaluate_14_point(activities)
        
        self.assertEqual(res["overall_status"], "FAILED")
        
        # Validate Missing Links calculation
        missing_links = next(m for m in res["metrics"] if "Logic" in m["check"])
        self.assertEqual(missing_links["value_pct"], 100.0)
        self.assertFalse(missing_links["passed"])
        
        # Validate Negative Lags calculation
        negative_lags = next(m for m in res["metrics"] if "Negative Lags" in m["check"])
        self.assertFalse(negative_lags["passed"])

    def test_monte_carlo_simulation_percentiles(self):
        # Run deterministic inputs through the probability sampler
        activities = [
            {"optimistic": 9, "most_likely": 10, "pessimistic": 11}
        ] * 5 # Roughly 50 days sum
        
        res = MonteCarloEngine.run_simulation(activities, iterations=500)
        
        # With 5 activities distributed between 9 and 11, the P50 is approx 50
        self.assertAlmostEqual(res["p50_days"], 50.0, delta=1.5)
        self.assertAlmostEqual(res["p80_days"], 51.0, delta=1.5)
        self.assertAlmostEqual(res["p90_days"], 52.0, delta=1.5)
        
        # Ensure the distribution curve payload populated successfully
        self.assertTrue(len(res["distribution_curve"]) > 0)

if __name__ == "__main__":
    unittest.main()
