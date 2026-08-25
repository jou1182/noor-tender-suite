"""
Gap Remediation Engine.

Applies automated technical patches for discrepancies identified in the
particular-specs audit report (or state payload):

  1. Injects specialized method statement addenda
     (dewatering execution plan, hydrostatic testing protocols).
  2. Applies automatic spec corrections to structural concrete line items
     (Type V cement, f'c >= 35 MPa, w/c <= 0.40).
  3. Re-calculates BOQ indirect cost allowances for temporary geotechnical works.
"""

import re
from typing import Any, Dict, List

DEWATERING_ADDENDUM = (
    "METHOD STATEMENT ADDENDUM — DEWATERING EXECUTION PLAN\n"
    "1. Install perimeter sheet-pile cutoff and deep wells at 15m spacing.\n"
    "2. Maintain water table >= 1.0m below excavation formation level.\n"
    "3. Discharge to approved sedimentation basin; monitor drawdown daily.\n"
    "4. Standby pumps (2x100% duty) with auto-start on level alarm.\n"
)

HYDROSTATIC_TESTING_ADDENDUM = (
    "METHOD STATEMENT ADDENDUM — HYDROSTATIC TESTING PROTOCOL\n"
    "1. Test each pipeline section to 1.5x design pressure for 2 hours.\n"
    "2. Allowable leakage per AWWA M11; record gauge readings every 15 min.\n"
    "3. Flush and disinfect to potable standard before commissioning.\n"
)

SPEC_CORRECTIONS = {
    "cement_type": "Type V (Sulfate-Resisting)",
    "min_fc_mpa": 35.0,
    "max_wc": 0.40,
}


class TechnicalGapRemediator:
    """Deterministic remediation of audit-flagged gaps."""

    def __init__(self) -> None:
        self.remediation_log: List[Dict[str, str]] = []

    def remediate(self, gaps: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply patches for each gap and return the patched state slice."""
        for gap in gaps:
            gap_id = str(gap.get("id", gap.get("clause_id", "GAP")))
            category = str(gap.get("category", gap.get("gap_type", ""))).lower()
            description = str(gap.get("description", ""))

            if "dewater" in description.lower() or "water table" in description.lower():
                state.setdefault("method_addenda", []).append({"id": gap_id, "text": DEWATERING_ADDENDUM})
                self.remediation_log.append({"id": gap_id, "status": "RESOLVED", "action": "dewatering_addendum"})

            elif "hydrostatic" in description.lower() or "pressure test" in description.lower():
                state.setdefault("method_addenda", []).append({"id": gap_id, "text": HYDROSTATIC_TESTING_ADDENDUM})
                self.remediation_log.append({"id": gap_id, "status": "RESOLVED", "action": "hydrostatic_addendum"})

            elif "cement" in description.lower() or "type v" in description.lower() or "sulfate" in description.lower():
                state.setdefault("spec_corrections", []).append(
                    {"id": gap_id, **SPEC_CORRECTIONS, "applied_to": "structural_concrete"}
                )
                self.remediation_log.append({"id": gap_id, "status": "RESOLVED", "action": "spec_correction_type_v"})

            elif "fc" in description.lower() or "f'c" in description.lower() or "strength" in description.lower():
                state.setdefault("spec_corrections", []).append(
                    {"id": gap_id, "min_fc_mpa": SPEC_CORRECTIONS["min_fc_mpa"], "applied_to": "structural_concrete"}
                )
                self.remediation_log.append({"id": gap_id, "status": "RESOLVED", "action": "spec_correction_fc"})

            elif "wc" in description.lower() or "water/cement" in description.lower():
                state.setdefault("spec_corrections", []).append(
                    {"id": gap_id, "max_wc": SPEC_CORRECTIONS["max_wc"], "applied_to": "structural_concrete"}
                )
                self.remediation_log.append({"id": gap_id, "status": "RESOLVED", "action": "spec_correction_wc"})

            elif "indirect" in description.lower() or "geotechnical" in description.lower() or "temporary work" in description.lower():
                state.setdefault("indirect_allowances", []).append(
                    {"id": gap_id, "allowance_sar": 250000.0, "category": "temporary_geotechnical"}
                )
                self.remediation_log.append({"id": gap_id, "status": "RESOLVED", "action": "indirect_cost_allowance"})

            else:
                self.remediation_log.append({"id": gap_id, "status": "UNRESOLVED", "action": "manual_review_required"})

        return state

    def parse_report_markdown(self, markdown_path: str) -> List[Dict[str, Any]]:
        """Parse the audit report markdown into structured gap items."""
        gaps: List[Dict[str, Any]] = []
        try:
            with open(markdown_path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return gaps

        # Match gap lines like "- [GAP-1] ..." or "| GAP-1 | ... |"
        for match in re.finditer(r"(?:^|\|)\s*(GAP-\d+)\s*[|\-]\s*(.*?)(?:\||$)", text, re.MULTILINE):
            gap_id, description = match.group(1), match.group(2).strip()
            category = "TECHNICAL"
            if any(k in description.lower() for k in ("dewater", "water table")):
                category = "GEOTECH"
            elif any(k in description.lower() for k in ("hydrostatic", "pressure")):
                category = "TESTING"
            elif any(k in description.lower() for k in ("cement", "sulfate", "fc", "wc")):
                category = "SPEC"
            elif "indirect" in description.lower():
                category = "COST"
            gaps.append({"id": gap_id, "category": category, "description": description})

        return gaps
