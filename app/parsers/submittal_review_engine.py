from typing import List, Dict, Any

class SubmittalReviewEngine:
    @staticmethod
    def evaluate_submittal(submittal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates manufacturer Technical Data Sheets (TDS) against strict Project Specifications.
        Assigns standard engineering Status Codes (A, B, C, D) based on compliance thresholds.
        """
        material_name = submittal_data.get("material", "Unknown")
        parameters = submittal_data.get("parameters", [])
        
        discrepancies = []
        status_comments = []
        
        for param in parameters:
            name = param.get("name", "Unknown Parameter")
            required = param.get("required_value", 0)
            submitted = param.get("submitted_value", 0)
            operator = param.get("operator", ">=")
            
            passed = False
            if operator == ">=":
                passed = submitted >= required
            elif operator == "<=":
                passed = submitted <= required
            elif operator == "==":
                passed = submitted == required
                
            param["passed"] = passed
            
            if not passed:
                discrepancies.append(f"{name}: Required {operator} {required}, but Submitted is {submitted}.")
                
        # Status Allocation Logic
        if len(discrepancies) == 0:
            status = "CODE_A"
            action = "Approved"
            status_comments.append("All technical parameters meet or exceed project specifications and SASO standards.")
        elif len(discrepancies) == 1 and submittal_data.get("minor_deviation", False):
            status = "CODE_B"
            action = "Approved as Noted"
            status_comments.append("Approved with minor deviations. See discrepancies for required field adjustments.")
            status_comments.extend(discrepancies)
        else:
            status = "CODE_C"
            action = "Revise and Resubmit"
            status_comments.append("CRITICAL: Material fails to meet specified minimum thresholds. Review discrepancies.")
            status_comments.extend(discrepancies)
            
        # Explicit Code D Rejection for severe failures (3 or more failing parameters)
        if len(discrepancies) >= 3:
            status = "CODE_D"
            action = "Rejected"
            status_comments[0] = "FATAL: Material comprehensively fails project specifications. Find alternate supplier."

        return {
            "material_name": material_name,
            "review_status": status,
            "review_action": action,
            "parameters_evaluated": parameters,
            "discrepancies_found": len(discrepancies),
            "technical_commentary": status_comments
        }
