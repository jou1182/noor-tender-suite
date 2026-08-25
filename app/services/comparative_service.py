import statistics

class ComparativeService:
    @staticmethod
    def generate_benchmark(tenders: list) -> dict:
        if not tenders:
            return {}
        
        # Rank by technical score descending
        ranked = sorted(tenders, key=lambda x: x.technical_score or 0, reverse=True)
        
        scores = [t.technical_score for t in tenders if t.technical_score is not None]
        mean_score = statistics.mean(scores) if scores else 0
        stdev_score = statistics.stdev(scores) if len(scores) > 1 else 0
        
        results = []
        outliers = []
        
        for idx, t in enumerate(ranked):
            is_outlier = False
            if stdev_score > 0 and t.technical_score is not None:
                # Flag as outlier if > 1 standard deviation from the mean
                if abs(t.technical_score - mean_score) > stdev_score:
                    is_outlier = True
                    outliers.append(t.id)
            
            # Extract budget if available in audit_metadata
            budget = 0
            if isinstance(t.audit_metadata, dict):
                boq_out = t.audit_metadata.get("boq_output", {}).get("boq_financials", {})
                budget = boq_out.get("total_budget", 0)
                
            results.append({
                "tender_id": t.id,
                "client_name": getattr(t, 'client_name', f"Bidder {t.id}"),
                "rank": idx + 1,
                "score": t.technical_score or 0,
                "budget": budget,
                "is_outlier": is_outlier,
                "variance_from_mean": round((t.technical_score or 0) - mean_score, 2)
            })
            
        return {
            "mean_score": round(mean_score, 2),
            "stdev_score": round(stdev_score, 2),
            "rankings": results,
            "outliers": outliers
        }
