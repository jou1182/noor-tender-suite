from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

class TIAEngine:
    @staticmethod
    def calculate_eot(baseline_completion: datetime, fragnet_delays_days: List[int]) -> Tuple[datetime, int]:
        """
        Calculates Extension of Time (EoT) by simulating a fragnet insertion directly onto the critical path.
        """
        total_delay = sum(fragnet_delays_days)
        new_completion = baseline_completion + timedelta(days=total_delay)
        return new_completion, total_delay

    @staticmethod
    def evaluate_entitlement(event_date: datetime, notice_date: datetime) -> Dict[str, Any]:
        """
        Evaluates contractual entitlement specifically targeting the strict FIDIC Sub-Clause 20.1 (28-day notice limit).
        """
        delta_days = (notice_date - event_date).days
        is_time_barred = delta_days > 28
        
        return {
            "event_date": event_date.strftime("%Y-%m-%d"),
            "notice_date": notice_date.strftime("%Y-%m-%d"),
            "days_elapsed": delta_days,
            "is_time_barred": is_time_barred,
            "warning": "CRITICAL RISK: Notice of Claim is time-barred under FIDIC 20.1 (> 28 days). Employer may reject entirely." if is_time_barred else "Notice submitted successfully within the strict 28-day contractual window."
        }
