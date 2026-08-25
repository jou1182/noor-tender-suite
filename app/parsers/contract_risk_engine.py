import re
from typing import List, Dict, Any

class ContractRiskEngine:
    @staticmethod
    def analyze_clauses(clauses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        risks = []
        
        for clause in clauses:
            text_lower = clause.get("text", "").lower()
            ref = clause.get("ref", "Unknown")
            
            # 1. Time-Bar Claim Deadlines (< 28 days)
            if "notice" in text_lower and "claim" in text_lower:
                match = re.search(r'(\d+)\s+days', text_lower)
                if match:
                    days = int(match.group(1))
                    if days < 28:
                        risks.append({
                            "clause_ref": ref,
                            "clause_text": clause.get("text"),
                            "risk_type": "Time-Bar Limit",
                            "severity": "High",
                            "summary": f"Onerous notice period of {days} days. Standard FIDIC Sub-Clause 20.1 dictates 28 days.",
                            "counter_clause": "The Contractor shall give notice to the Engineer as soon as practicable, and not later than 28 days after the Contractor became aware of the event."
                        })
                        continue
                        
            # 2. Uncapped Liquidated Damages
            if "liquidated damages" in text_lower or "delay damages" in text_lower:
                if "uncapped" in text_lower or "no maximum" in text_lower or "without limit" in text_lower:
                    risks.append({
                        "clause_ref": ref,
                        "clause_text": clause.get("text"),
                        "risk_type": "Uncapped Liability",
                        "severity": "High",
                        "summary": "Liquidated damages are uncapped, presenting infinite financial exposure to the Contractor.",
                        "counter_clause": "Delay damages shall not exceed 10% of the Accepted Contract Amount."
                    })
                    continue
                    
            # 3. Broad Indemnity & Consequential Loss
            if "indemnify" in text_lower or "indemnity" in text_lower:
                if "consequential" in text_lower or "indirect loss" in text_lower:
                    risks.append({
                        "clause_ref": ref,
                        "clause_text": clause.get("text"),
                        "risk_type": "Broad Indemnity",
                        "severity": "Medium",
                        "summary": "Contractor indemnifies Employer for consequential and indirect losses, skewing the risk profile.",
                        "counter_clause": "Neither Party shall be liable to the other Party for loss of use of any Works, loss of profit, loss of any contract or for any indirect or consequential loss."
                    })
                    continue
                    
        return risks
