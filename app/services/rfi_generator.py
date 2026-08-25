from typing import List, Dict

class RFIGenerator:
    @staticmethod
    def draft_rfis(vulnerabilities: List[Dict]) -> List[str]:
        """
        Drafts formal Contractor Pre-Bid Request for Information (RFI) letters
        based on identified high-severity ambiguities and vulnerabilities.
        """
        rfis = []
        for i, vuln in enumerate(vulnerabilities):
            if vuln["severity"] in ["High", "Medium"]:
                rfi = f"""REQUEST FOR INFORMATION (RFI) #{i+1}
Date: [Current Date]
Subject: Clarification on {vuln['risk_type']} Constraints

To the Employer / Engineer,

During our rigorous tender review, we identified the following risk/ambiguity:
{vuln['description']}

Could you please clarify the acceptable tolerances or approve our proposed mitigation:
{vuln['mitigation']}

Sincerely,
Contractor Tendering Team
"""
                rfis.append(rfi.strip())
        return rfis
