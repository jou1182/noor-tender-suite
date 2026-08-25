"""Client RFP Agent (LangGraph node).

Ingests the uploaded RFP documents, parses them into a structured clause
schema via the RfpClauseParser (strictness segmentation + compliance gates),
and publishes the schema into the orchestration state for downstream agents
(cross-exam, methodology, standards, commercial).
"""

from typing import Any, Dict, List

from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.rfp_clause_parser import RfpClauseParser


def _read_document(path: str) -> str:
    """Read an RFP document (PDF or plain text) into raw text."""
    try:
        if path.lower().endswith(".pdf"):
            return extract_text_from_pdf(path)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return ""


def client_rfp_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: parse RFP documents into a structured clause schema.

    State keys consumed: rfp_documents (list of file paths).
    State keys produced: rfp_output { clauses, segment_summary, compliance_gates }.
    """
    rfp_paths: List[str] = state.get("rfp_documents") or []
    raw_chunks: List[str] = []
    for path in rfp_paths:
        text = _read_document(path)
        if text.strip():
            raw_chunks.append(text)

    if not raw_chunks:
        # Demo fallback so downstream agents always receive a clause schema.
        demo_text = (
            "Clause 1: All concrete works shall comply with SBC 304 for structural requirements.\n"
            "Clause 2: Contractor must submit method statements and shop drawings for approval prior to commencement.\n"
            "Clause 3: Liquidated damages shall be capped at 10% of the contract value.\n"
            "Clause 4: Technical specification: Concrete mix design achieves 40 MPa with 0.38 water-cement ratio.\n"
            "Clause 5: Contractor shall provide a qualified project manager with 10+ years of experience.\n"
            "Clause 6: Submittal: Provide shop drawings, method statements and as-built reports."
        )
        raw_chunks.append(demo_text)

    parsed_docs = [RfpClauseParser.parse_text(chunk) for chunk in raw_chunks]

    # Merge clauses across documents, re-indexing for stable clause ids.
    clauses: List[Dict[str, Any]] = []
    segment_summary: Dict[str, int] = {}
    compliance_gates: Dict[str, Any] = {
        "sbc_standards": set(),
        "sbc_citations_total": 0,
        "personnel_requirements_total": 0,
        "penalty_thresholds": [],
        "critical_gate_count": 0,
    }

    clause_id = 0
    for parsed in parsed_docs:
        for clause in parsed.get("clauses", []):
            clause_id += 1
            clause = dict(clause)
            clause["clause_id"] = clause_id
            clause["ref"] = f"RFP-C{clause_id}"
            clauses.append(clause)

        for strictness, count in parsed.get("segment_summary", {}).items():
            segment_summary[strictness] = segment_summary.get(strictness, 0) + count

        gates = parsed.get("compliance_gates", {})
        compliance_gates["sbc_standards"].update(gates.get("sbc_standards", []))
        compliance_gates["sbc_citations_total"] += gates.get("sbc_citations_total", 0)
        compliance_gates["personnel_requirements_total"] += gates.get("personnel_requirements_total", 0)
        compliance_gates["penalty_thresholds"].extend(gates.get("penalty_thresholds", []))
        compliance_gates["critical_gate_count"] += gates.get("critical_gate_count", 0)

    compliance_gates["sbc_standards"] = sorted(compliance_gates["sbc_standards"])

    return {
        "rfp_output": {
            "clauses": clauses,
            "segment_summary": segment_summary,
            "compliance_gates": compliance_gates,
            "document_count": len(parsed_docs),
        }
    }
