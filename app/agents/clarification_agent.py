"""
Clarification & RFI Assistant (LangGraph node).

Formulates professional technical clarification inquiries (RFIs) from detected
tender ambiguities, ingests owner responses to retire affected contractual risk
flags, and selectively re-invokes SBC-304 / VE engines on impacted BOQ items
without full pipeline re-execution.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.parsers.addenda_diff_engine import AddendaDiffEngine
from app.parsers.sbc_standards_engine import Sbc304Engine
from app.parsers.value_engineering_engine import ValueEngineeringEngine
from app.schemas.clarifications import AddendumImpactSummary, ClarificationRFI, TenderAddendum

AMBIGUITY_PATTERNS = [
    ("quantity basis", "Please confirm the measurement basis (net vs gross) for the stated BOQ quantities."),
    ("exposure class", "Please confirm the governing exposure class for substructure concrete elements."),
    ("work hours", "Please confirm permitted working hours and any night-work restrictions near residential zones."),
    ("sample approval", "Please confirm the sample approval lead time and the number of material samples required."),
    ("interface", "Please clarify the interface responsibility between this package and adjacent contractor scopes."),
]


class ClarificationAgent:
    """Deterministic RFI formulation + owner-response ingestion."""

    @staticmethod
    def detect_ambiguities(state: Dict[str, Any]) -> List[ClarificationRFI]:
        """Scan raw tender text for ambiguity keywords and draft RFIs."""
        raw = str(state.get("raw_specs_text", state.get("rfp_text", "")) or "")
        if not raw:
            return []
        lowered = raw.lower()

        rfis: List[ClarificationRFI] = []
        for idx, (keyword, question) in enumerate(AMBIGUITY_PATTERNS, start=1):
            if keyword in lowered:
                rfis.append(
                    ClarificationRFI(
                        rfi_id=f"RFI-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{idx:02d}",
                        subject=f"Clarification: {keyword.title()}",
                        question=question,
                        reference_clause="",
                        status="OPEN",
                        created_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
        return rfis

    @staticmethod
    def ingest_owner_response(
        risk_register: List[Dict[str, Any]],
        rfi: ClarificationRFI,
        response_text: str,
    ) -> List[Dict[str, Any]]:
        """
        Apply an owner RFI response: retire affected contractual risk flags.

        Risks whose description matches the RFI's subject/keywords are either
        removed or downgraded, and the RFI is marked RESPONDED.
        """
        rfi.client_response = response_text
        rfi.status = "RESPONDED"

        subject_tokens = rfi.subject.lower().replace("clarification:", "").strip().split()
        updated: List[Dict[str, Any]] = []
        for risk in risk_register:
            desc = str(risk.get("description", "")).lower()
            if any(tok in desc for tok in subject_tokens if len(tok) > 3):
                if risk.get("severity") == "FATAL_FLAW":
                    risk = {**risk, "severity": "MEDIUM", "resolved_by_rfi": rfi.rfi_id}
                else:
                    risk = {**risk, "resolved_by_rfi": rfi.rfi_id}
            updated.append(risk)
        return updated

    @staticmethod
    def selective_reaudit(impact: AddendumImpactSummary, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-run SBC-304 + VE engines only on BOQ items flagged HIGH impact.

        Returns a dict of updated state slices for affected items.
        """
        affected_descriptions = set(impact.reaudited_items)
        if not affected_descriptions:
            return {}

        boq_items = state.get("boq_items", []) or []
        affected = [i for i in boq_items if str(i.get("item_no", i.get("description"))) in affected_descriptions]

        reaudit: Dict[str, Any] = {"reaudited_items": []}
        for item in affected:
            sbc_result = Sbc304Engine.evaluate_material(
                fc_mpa=item.get("fc_mpa"),
                wc=item.get("wc"),
                fy_mpa=item.get("fy_mpa"),
                cover_depth_mm=item.get("cover_depth_mm"),
            )
            ve_cards = ValueEngineeringEngine.generate_ve_matrix([item])
            reaudit["reaudited_items"].append(
                {
                    "item_no": item.get("item_no"),
                    "description": item.get("description"),
                    "sbc_verdict": "COMPLIANT" if sbc_result.is_compliant else "NON_COMPLIANT",
                    "sbc_violations": sbc_result.violations,
                    "ve_candidates": [c.model_dump() for c in ve_cards],
                }
            )
        return reaudit


def clarification_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: addenda diff + clarification assistant.

    State keys consumed: raw_specs_text, boq_items, contractual_risk_register.
    State keys produced: addenda_history, clarification_rfis, addenda_impacts,
      contractual_risk_register (updated), reaudit_results.
    """
    print("--- [AGENT] Tender Addenda & Clarification Assistant ---")

    # 1. Detect ambiguities in the current tender package and draft RFIs.
    rfis = ClarificationAgent.detect_ambiguities(state)

    # 2. Process any uploaded addenda in state.
    impacts: List[AddendumImpactSummary] = []
    addenda = state.get("pending_addenda", []) or []
    reaudit_results: Dict[str, Any] = {"reaudited_items": []}

    for addendum_data in addenda:
        addendum = TenderAddendum(**addendum_data) if isinstance(addendum_data, dict) else addendum_data
        impact = AddendaDiffEngine.analyze(state, addendum)
        impacts.append(impact)
        partial = ClarificationAgent.selective_reaudit(impact, state)
        for item in partial.get("reaudited_items", []):
            reaudit_results["reaudited_items"].append(item)

    # 3. Apply owner responses already present in state.
    risk_register = state.get("contractual_risk_register", []) or []
    for rfi in rfis:
        if state.get("owner_responses", {}).get(rfi.rfi_id):
            risk_register = ClarificationAgent.ingest_owner_response(
                risk_register, rfi, state["owner_responses"][rfi.rfi_id]
            )

    return {
        "clarification_rfis": [r.model_dump() for r in rfis],
        "addenda_impacts": [i.model_dump() for i in impacts],
        "contractual_risk_register": risk_register,
        "reaudit_results": reaudit_results,
    }
