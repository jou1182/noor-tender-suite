import numpy as np
from typing import Dict, List, Any

class MonteCarloEngine:
    @staticmethod
    def run_simulation(critical_path_activities: List[Dict[str, float]], iterations: int = 5000) -> Dict[str, Any]:
        """
        Executes extremely fast vectorized Monte Carlo simulations using NumPy.
        Samples activity duration probability over thousands of iterations to map a Gaussian confidence curve.
        """
        # Allocate flat zero array for vectorized matrix summation
        total_duration_samples = np.zeros(iterations)
        
        for activity in critical_path_activities:
            # Sample thousands of deterministic durations simultaneously based on three-point estimation
            samples = np.random.triangular(
                left=activity["optimistic"],
                mode=activity["most_likely"],
                right=activity["pessimistic"],
                size=iterations
            )
            total_duration_samples += samples
            
        p50 = np.percentile(total_duration_samples, 50)
        p80 = np.percentile(total_duration_samples, 80)
        p90 = np.percentile(total_duration_samples, 90)
        
        # Build frequency histogram payload for frontend bell-curve plotting
        hist, bin_edges = np.histogram(total_duration_samples, bins=60)
        distribution = [
            {"duration": round(float(bin_edges[i]), 1), "probability": int(hist[i])} 
            for i in range(len(hist))
        ]
        
        return {
            "p50_days": round(float(p50), 1),
            "p80_days": round(float(p80), 1),
            "p90_days": round(float(p90), 1),
            "distribution_curve": distribution
        }
