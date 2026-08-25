from typing import List, Dict, Any

class ReconciliationEngine:
    @staticmethod
    def calculate_variances(methodology_rates: Dict[str, float], boq_quantities: Dict[str, float], p6_durations: Dict[str, float]) -> List[Dict[str, Any]]:
        discrepancies = []
        
        # Cross-reference common activities across the three sources
        for activity, quantity in boq_quantities.items():
            rate = methodology_rates.get(activity)
            duration = p6_durations.get(activity)
            
            if rate and duration:
                expected_duration = quantity / rate if rate > 0 else 0
                if expected_duration > 0:
                    variance = abs(duration - expected_duration) / expected_duration * 100
                    if variance > 10.0:
                        discrepancies.append({
                            "activity": activity,
                            "boq_quantity": quantity,
                            "method_rate": rate,
                            "p6_duration": duration,
                            "expected_duration": round(expected_duration, 2),
                            "variance_percent": round(variance, 2),
                            "severity": "High" if variance > 25.0 else "Medium",
                            "conflict": f"Duration variance of {round(variance, 2)}% exceeds 10% threshold."
                        })
        return discrepancies
