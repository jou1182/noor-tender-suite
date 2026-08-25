from typing import Dict, Any, List

class EtimadValidator:
    @staticmethod
    def validate_submission(tender_payload: Dict[str, Any]) -> Dict[str, Any]:
        docs = tender_payload.get("documents", {})
        
        missing_mandatories = []
        
        # Check Initial Bank Guarantee (GTPL Requires at least 90 days validity)
        bg = docs.get("bank_guarantee")
        if not bg or bg.get("validity_days", 0) < 90:
            missing_mandatories.append("Initial Bank Guarantee (Missing or < 90 days validity)")
            
        # Check Classification Certificate (Contractors must be classified)
        if not docs.get("classification_certificate"):
            missing_mandatories.append("Contractor Classification Certificate (Missing or Invalid)")
            
        # Check Local Content Baseline (e.g., minimum 10% threshold)
        local_content = docs.get("local_content_score", 0.0)
        if local_content < 10.0:
            missing_mandatories.append(f"Local Content Baseline too low ({local_content}% < 10%)")
            
        readiness_score = 100.0
        penalty_per_missing = 33.33
        readiness_score -= len(missing_mandatories) * penalty_per_missing
        readiness_score = max(0, round(readiness_score, 2))
        
        status = "COMPLIANT" if not missing_mandatories else "NON-COMPLIANT"
        
        return {
            "status": status,
            "readiness_score": readiness_score,
            "local_content_score": local_content,
            "missing_mandatory_attachments": missing_mandatories
        }
