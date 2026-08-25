"""Cross-Exam Agent (LangGraph node).

Ingests the extracted RFP clause schema and the contractor's technical
proposal draft, executes deterministic clause-by-clause verification through
the CrossExamMatrixEngine, mutates the orchestration state with the
``rfp_compliance_matrix``, and streams real-time compliance telemetry into
the shared SSE bus consumed by the dashboard.
"""

from typing import Any, Dict, Iterator, List

from app.core.swarm_telemetry import emit as default_emit
from app.parsers.cross_exam_matrix_engine import CrossExamMatrixEngine
from app.parsers.rfp_clause_parser import RfpClauseParser

# Streaming callback signature: (event_type, payload) pairs.
EventCallback = Any


def _extract_clauses(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Resolve parsed RFP clauses from state, parsing raw text on demand."""
    rfp_output = state.get("rfp_output", {}) or {}
    clauses = rfp_output.get("clauses") or rfp_output.get("extracted_requirements")

    if clauses is None and rfp_output.get("raw_text"):
        parsed = RfpClauseParser.parse_text(rfp_output["raw_text"])
        clauses = parsed["clauses"]

    if clauses is None:
        # Fallback demonstration schema mirrors the upstream mock RFP agent.
        parsed = RfpClauseParser.parse_text(
            "Clause 1: All works shall comply with SBC 304 for concrete. "
            "Clause 2: Contractor must submit a method statement. "
            "Clause 3: Liquidated damages capped at 10% of contract value."
        )
        clauses = parsed["clauses"]
    return clauses


def _extract_proposal_sections(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Resolve the proposal draft into [{title, text}] sections."""
    proposal = state.get("generated_proposal_output", []) or []

    sections: List[Dict[str, Any]] = []
    for item in proposal:
        if isinstance(item, dict):
            text = (
                item.get("method_statement_text")
                or item.get("text")
                or item.get("content")
                or ""
            )
            if text:
                sections.append(
                    {
                        "title": item.get("boq_item") or item.get("title") or f"Section {len(sections) + 1}",
                        "text": text,
                    }
                )
    return sections


def _compliance_events(
    summary: Dict[str, Any], matrix: List[Dict[str, Any]]
) -> Iterator[Dict[str, Any]]:
    """Yield a stream of compliance metric events for the payload."""
    counts = summary["status_counts"]
    yield {"event": "cross_exam.start", "payload": {"total_clauses": summary["total_clauses"]}}
    yield {
        "event": "cross_exam.metrics",
        "payload": {
            "compliance_score": summary["compliance_score"],
            "status_counts": counts,
            "mandatory_gap_count": summary["mandatory_gap_count"],
        },
    }
    for row in matrix:
        yield {
            "event": "cross_exam.clause",
            "payload": {
                "clause_ref": row["clause_ref"],
                "status": row["status"],
                "match_score": row["match_score"],
            },
        }
    yield {"event": "cross_exam.complete", "payload": {"compliance_score": summary["compliance_score"]}}


def _shorten(text: str, limit: int = 110) -> str:
    """Short first-sentence summary for telemetry lines."""
    import re as _re

    first = _re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return first if len(first) <= limit else first[: limit - 3] + "..."


def _reconcile_plan_versus_budget(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Cross-audit reconciliation: BOQ quantities vs methodology productivity rates
    vs P6 scheduled durations. Flags >10% schedule variances as discrepancies.
    Falls back to a deterministic demonstration set when the state lacks the
    structured maps (mirrors the upstream mock).
    """
    from app.parsers.reconciliation_engine import ReconciliationEngine

    rates: Dict[str, float] = {}
    quantities: Dict[str, float] = {}
    durations: Dict[str, float] = {}

    proposal = state.get("generated_proposal_output", []) or []
    for item in proposal:
        if isinstance(item, dict) and item.get("productivity_rate"):
            name = item.get("boq_item") or item.get("title")
            if name:
                rates[name] = float(item["productivity_rate"])

    boq = state.get("boq_output", {}) or {}
    for key in ("quantities", "items", "line_items"):
        if isinstance(boq.get(key), dict):
            quantities = {str(k): float(v) for k, v in boq[key].items()}
            break

    p6 = state.get("p6_output", {}) or {}
    if isinstance(p6.get("activity_durations"), dict):
        durations = {str(k): float(v) for k, v in p6["activity_durations"].items()}

    if not (rates and quantities and durations):
        # Deterministic cross-audit mock: 10,000 m3 @ 400 m3/day vs 15 scheduled days = 40%.
        rates = {"Excavation": 400.0, "Concrete": 100.0}
        quantities = {"Excavation": 10000.0, "Concrete": 1000.0}
        durations = {"Excavation": 15.0, "Concrete": 10.0}

    return ReconciliationEngine.calculate_variances(rates, quantities, durations)


def cross_exam_agent(
    state: Dict[str, Any], emit: EventCallback = None
) -> Dict[str, Any]:
    """
    LangGraph node: deterministic RFP clause vs proposal cross-examination.

    State keys consumed: rfp_output, generated_proposal_output.
    State keys produced: rfp_compliance_matrix, cross_exam_output.

    Publishes real-time telemetry to the shared SSE bus (via app.core.swarm_telemetry)
    so the AgentFlowCanvas receives live status transitions + gap findings.
    """
    if emit is None:
        emit = default_emit

    clauses = _extract_clauses(state)
    sections = _extract_proposal_sections(state)

    emit("Cross-Exam Agent running — executing clause-by-clause RFP vs proposal verification...")

    result = CrossExamMatrixEngine.compare(clauses, sections)
    matrix = result["matrix"]
    stream = list(_compliance_events(result, matrix))

    # Publish critical-gap findings (keyword-free so node status stays stable).
    for row in matrix:
        if row["status"] == "CRITICAL_GAP":
            emit(f"VERIFY [CRITICAL_GAP] {row['clause_ref']}: {_shorten(row.get('clause_text', ''))}")

    emit(
        f"Cross-Exam Agent completed — "
        f"{result['status_counts'].get('COMPLIANT', 0)} compliant, "
        f"{result['status_counts'].get('MINOR_DEVIATION', 0)} minor deviations, "
        f"{result['status_counts'].get('CRITICAL_GAP', 0)} critical gaps "
        f"(compliance score {result['compliance_score']}%)."
    )

    rfp_compliance_matrix: Dict[str, Any] = {
        "compliance_score": result["compliance_score"],
        "status_counts": result["status_counts"],
        "mandatory_gap_count": result["mandatory_gap_count"],
        "clause_count": len(clauses),
        "section_count": len(sections),
        "matrix": matrix,
    }

    discrepancies = _reconcile_plan_versus_budget(state)

    return {
        "rfp_compliance_matrix": rfp_compliance_matrix,
        "discrepancy_output": {"discrepancies": discrepancies},
        "cross_exam_output": {
            "clause_count": len(clauses),
            "section_count": len(sections),
            "compliance_score": result["compliance_score"],
            "status_counts": result["status_counts"],
            "mandatory_gap_count": result["mandatory_gap_count"],
            "matrix": matrix,
            "metrics_stream": stream,
        },
    }