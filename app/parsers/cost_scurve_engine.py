from typing import List, Dict, Any

class CostSCurveEngine:
    @staticmethod
    def generate_scurve(activities: List[Dict[str, Any]], max_month: int) -> List[Dict[str, Any]]:
        monthly_data = []
        cum_early = 0.0
        cum_late = 0.0
        total_cost = sum(a.get("cost", 0) for a in activities)
        
        for m in range(max_month + 1):
            early_cost_this_month = 0.0
            late_cost_this_month = 0.0
            
            for act in activities:
                cost = act.get("cost", 0.0)
                dur = max(1, act.get("duration", 1))
                monthly_burn = cost / dur
                
                # Early distribution allocation
                es = act.get("early_start", 0)
                if es <= m < es + dur:
                    early_cost_this_month += monthly_burn
                    
                # Late distribution allocation
                ls = act.get("late_start", es)
                if ls <= m < ls + dur:
                    late_cost_this_month += monthly_burn
                    
            cum_early += early_cost_this_month
            cum_late += late_cost_this_month
            
            monthly_data.append({
                "month": m + 1,
                "early_cost": round(early_cost_this_month, 2),
                "late_cost": round(late_cost_this_month, 2),
                "cum_early": round(cum_early, 2),
                "cum_late": round(cum_late, 2),
                "cum_early_pct": round((cum_early / total_cost) * 100, 2) if total_cost else 0,
                "cum_late_pct": round((cum_late / total_cost) * 100, 2) if total_cost else 0
            })
        
        # Hard lock final month to 100% to resolve tiny floating point drifts
        if monthly_data:
            monthly_data[-1]["cum_early_pct"] = 100.0
            monthly_data[-1]["cum_late_pct"] = 100.0
            
        return monthly_data
        
    @staticmethod
    def detect_front_loading(activities: List[Dict[str, Any]], historical_baselines: Dict[str, float]) -> List[Dict[str, Any]]:
        front_loaded = []
        for act in activities:
            item = act.get("item", "")
            unit_rate = act.get("unit_rate", 0)
            baseline = historical_baselines.get(item, 0)
            early_start = act.get("early_start", 0)
            
            # Rule: Flag items happening in first 2 months if rate is > 20% over baseline
            if early_start <= 2 and baseline > 0:
                if unit_rate > baseline * 1.20:
                    front_loaded.append({
                        "item": item,
                        "proposed_rate": unit_rate,
                        "baseline_rate": baseline,
                        "variance_pct": round(((unit_rate - baseline) / baseline) * 100, 2)
                    })
        return front_loaded
