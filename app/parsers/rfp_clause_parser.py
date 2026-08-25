"""
RFP Clause Parsing Engine.

Ingests raw RFP text (or a PDF path) and:
  1. Segments clauses by strictness:
       - Mandatory
       - Technical Specification
       - Commercial/Legal
       - Submittal Requirements
  2. Identifies critical compliance gates:
       - SBC standards citations
       - Key personnel qualification requirements
       - Penalty / liquidated damages thresholds
"""

import re
from typing import Any, Dict, List

from app.parsers.pdf_parser import extract_text_from_pdf

STRICTNESS = "strictness"
CLAUSE_TEXT = "text"
CLAUSE_REF = "ref"
CLAUSE_ID = "clause_id"
SECTION = "section"

# Domain-specific strictness categories are checked before the generic
# mandatory modality keywords so a clause keeps its domain classification
# (e.g. "must submit a method statement" -> Submittal Requirements).
STRICTNESS_RULES: List[Dict[str, Any]] = [
    {
        "strictness": "Technical Specification",
        "patterns": [
            r"\btechnical\s+specification\b",
            r"\bspecification\b",
            r"\bdesign\s+criteria\b",
            r"\bconform(?:s|ance)?\s+to\b",
            r"\bper\s+(?:the\s+)?(?:latest|applicable)?\s*standard",
            r"\bstandards?\b",
            r"\bmaterial(?:s)?\s+(?:shall|must|to)\b",
        ],
    },
    {
        "strictness": "Commercial/Legal",
        "patterns": [
            r"\bcommercial\b",
            r"\blegal\b",
            r"\bcontract\b",
            r"\bliability\b",
            r"\bindemnif",
            r"\binsurance\b",
            r"\bliquidated\s+damages\b",
            r"\bpenalty\b",
            r"\bbond\b",
            r"\bpayment\b",
            r"\bguarantee\b",
            r"\bwarranty\b",
            r"\bdamages\b",
        ],
    },
    {
        "strictness": "Submittal Requirements",
        "patterns": [
            r"\bsubmittal\b",
            r"\bsubmission\b",
            r"\bsubmit\b",
            r"\bshop\s+drawings?\b",
            r"\bmethod\s+statement\b",
            r"\bprogramme\b",
            r"\bschedule\b",
            r"\bdeliverable(?:s)?\b",
            r"\breport(?:s)?\b",
        ],
    },
    {
        "strictness": "Mandatory",
        "patterns": [
            r"\bshall\b",
            r"\bmust\b",
            r"\bmandatory\b",
            r"\bshall not\b",
            r"\bis required\b",
            r"\bits mandatory\b",
        ],
    },
]

# Compliance gate extraction rules (independent of strictness).
SBC_STANDARD_PATTERN = re.compile(r"\bSBC\s*(?:-\s*)?(\d{3}(?:[A-Z])?(?:/\d+)?)\b", re.IGNORECASE)
PERSONNEL_KEYWORDS = (
    "qualification",
    "qualified",
    "certified",
    "credentials",
    "years of experience",
    "professional engineer",
    "registered engineer",
    "licensed",
    "project manager",
    "hse officer",
    "safety officer",
    "civil engineer",
)
PENALTY_KEYWORDS = (
    "penalty",
    "liquidated damages",
    "delay damages",
    "ld",
    "per day",
    "per week",
    "% of the contract",
    "cap",
)


class RfpClauseParser:
    @staticmethod
    def _split_clauses(raw_text: str) -> List[str]:
        """Split RFP text into individual clause strings."""
        if not raw_text or not raw_text.strip():
            return []

        text = raw_text.strip()
        # Numbered clauses (e.g. "3.2.1", "10.", "Section 5", "CL 4-1") or bold marker paragraphs.
        clause_boundary = re.compile(
            r"(?m)(?=^\s*(?:\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+"
            r"|(?:Section|Clause|Article|CL)\s*\d+(?:[\.\-]\d+)*\b"
            r"|[A-Z][A-Z\s]{4,}:))"
        )
        parts = [p.strip() for p in clause_boundary.split(text) if p and p.strip()]
        return parts if parts else [text]

    @staticmethod
    def _classify_strictness(clause_text: str) -> str:
        lowered = clause_text.lower()
        for rule in STRICTNESS_RULES:
            for pattern in rule["patterns"]:
                if re.search(pattern, lowered):
                    return rule["strictness"]
        return "General"

    @staticmethod
    def _extract_sbc_standards(clause_text: str) -> List[str]:
        return sorted({m.group(1).upper() for m in SBC_STANDARD_PATTERN.finditer(clause_text)})

    @staticmethod
    def _extract_penalty_threshold(clause_text: str) -> Dict[str, Any]:
        """Extract penalty / liquidated damages thresholds (rate and cap)."""
        gate: Dict[str, Any] = {"detected": False}
        lowered = clause_text.lower()
        if not any(kw in lowered for kw in PENALTY_KEYWORDS):
            return gate

        gate["detected"] = True
        rate_match = re.search(
            r"(?:sar|sr|usd|us\$|\$)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:per\s+day|per\s+week|/day|/week)",
            clause_text,
            re.IGNORECASE,
        )
        if rate_match:
            gate["rate"] = float(rate_match.group(1).replace(",", ""))

        cap_match = re.search(
            r"(?:capped?\s+at|maximum|max|not\s+to\s+exceed|limit(?:ed)?\s+to)\s*(?:sar|sr|usd|us\$|\$)?\s*"
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
            clause_text,
            re.IGNORECASE,
        )
        if cap_match:
            gate["cap"] = float(cap_match.group(1).replace(",", ""))

        if not rate_match and not cap_match:
            gate["note"] = "Penalty mechanism present without numeric threshold."
        return gate

    @staticmethod
    def _extract_personnel_requirements(clause_text: str) -> List[Dict[str, str]]:
        lowered = clause_text.lower()
        if not any(kw in lowered for kw in PERSONNEL_KEYWORDS):
            return []
        requirements: List[Dict[str, str]] = []
        exp_match = re.search(r"(\d+)\s*\+?\s*years?\s+of\s+experience", clause_text, re.IGNORECASE)
        if exp_match:
            requirements.append(
                {"type": "experience", "requirement": f"{exp_match.group(1)}+ years of experience"}
            )
        cert_match = re.search(r"(?:certified|licensed|registered)\s+([\w\s\-]+?)(?=\.|;|,|\band\b)", clause_text, re.IGNORECASE)
        if cert_match:
            requirements.append({"type": "certification", "requirement": cert_match.group(1).strip().title()})
        if not requirements:
            requirements.append({"type": "general", "requirement": "Key personnel qualification provision."})
        return requirements

    @staticmethod
    def parse_text(raw_text: str) -> Dict[str, Any]:
        """Parse raw RFP text into structured, strictness-segmented clauses."""
        clauses: List[Dict[str, Any]] = []
        sbc_count = 0
        penalties: List[Dict[str, Any]] = []

        for idx, clause_text in enumerate(RfpClauseParser._split_clauses(raw_text), start=1):
            standards = RfpClauseParser._extract_sbc_standards(clause_text)
            penalty_gate = RfpClauseParser._extract_penalty_threshold(clause_text)
            personnel = RfpClauseParser._extract_personnel_requirements(clause_text)

            if standards:
                sbc_count += len(standards)
            if penalty_gate.get("detected"):
                penalties.append({"clause_id": idx, **penalty_gate})

            clauses.append(
                {
                    CLAUSE_ID: idx,
                    CLAUSE_REF: f"RFP-C{idx}",
                    CLAUSE_TEXT: clause_text,
                    STRICTNESS: RfpClauseParser._classify_strictness(clause_text),
                    SECTION: RfpClauseParser._detect_section(clause_text),
                    "sbc_standards": standards,
                    "personnel_requirements": personnel,
                    "penalty_gate": penalty_gate,
                }
            )

        return {
            "clauses": clauses,
            "segment_summary": RfpClauseParser._segment_summary(clauses),
            "compliance_gates": {
                "sbc_standards": sorted({s for c in clauses for s in c["sbc_standards"]}),
                "sbc_citations_total": sbc_count,
                "personnel_requirements_total": sum(len(c["personnel_requirements"]) for c in clauses),
                "penalty_thresholds": penalties,
                "critical_gate_count": sum(1 for c in clauses if c["sbc_standards"] or c["penalty_gate"].get("detected") or c["personnel_requirements"]),
            },
        }

    @staticmethod
    def _detect_section(clause_text: str) -> str:
        lowered = clause_text.lower()
        if "scope of work" in lowered or "scope" in lowered:
            return "Scope of Work"
        if "payment" in lowered or "commercial" in lowered or "bond" in lowered or "insurance" in lowered:
            return "Commercial"
        if "submittal" in lowered or "submission" in lowered or "report" in lowered:
            return "Submittals"
        if "technical" in lowered or "specification" in lowered or "material" in lowered:
            return "Technical"
        return "General"

    @staticmethod
    def _segment_summary(clauses: List[Dict[str, Any]]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for clause in clauses:
            strictness = clause[STRICTNESS]
            summary[strictness] = summary.get(strictness, 0) + 1
        return summary

    @staticmethod
    def parse_pdf(pdf_path: str) -> Dict[str, Any]:
        """Parse an RFP PDF by extracting text then delegating to parse_text."""
        text = extract_text_from_pdf(pdf_path)
        return RfpClauseParser.parse_text(text)
