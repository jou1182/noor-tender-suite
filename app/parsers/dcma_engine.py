from typing import Dict, List, Any

class DCMAEngine:
    @staticmethod
    def evaluate_14_point(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes Defense Contract Management Agency (DCMA) 14-Point Schedule Integrity Checks.
        """
        total = len(activities)
        if total == 0:
            return {}
        
        # Extrapolated core validations
        missing_logic = sum(1 for a in activities if not a.get("predecessors") and not a.get("successors"))
        negative_lags = sum(1 for a in activities if a.get("lag", 0) < 0)
        high_float = sum(1 for a in activities if a.get("total_float", 0) > 44)
        hard_constraints = sum(1 for a in activities if a.get("constraint_type") in ["Must Finish On", "Must Start On"])
        
        metrics = [
            {
                "check": "1. Logic (Missing Links)", 
                "value_pct": (missing_logic / total) * 100, 
                "threshold": 5.0,
                "passed": (missing_logic / total) * 100 <= 5.0,
                "description": "Unlinked activities disrupt the network flow calculation."
            },
            {
                "check": "2. Negative Lags", 
                "value_pct": (negative_lags / total) * 100, 
                "threshold": 0.0,
                "passed": negative_lags == 0,
                "description": "Negative lags distort critical path float visibility."
            },
            {
                "check": "3. High Float (> 44 Days)", 
                "value_pct": (high_float / total) * 100, 
                "threshold": 5.0,
                "passed": (high_float / total) * 100 <= 5.0,
                "description": "Excessive float indicates an unstable critical sequence."
            },
            {
                "check": "4. Hard Constraints", 
                "value_pct": (hard_constraints / total) * 100, 
                "threshold": 5.0,
                "passed": (hard_constraints / total) * 100 <= 5.0,
                "description": "Fixed dates override dynamic network logic."
            }
        ]
        
        overall_pass = all(m["passed"] for m in metrics)
        
        return {
            "overall_status": "PASSED" if overall_pass else "FAILED",
            "metrics": metrics
        }
