"""Client RFP Agent (LangGraph node).

Ingests the uploaded RFP documents, parses them into a structured clause
schema via the RfpClauseParser (strictness segmentation + compliance gates),
and publishes the schema into the orchestration state for downstream agents
(cross-exam, methodology, standards, commercial).
"""

from typing import Any, Dict, List

from app.agents.errors import InsufficientInputError
from app.parsers.arabic_text import fix_presentation_forms
from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.rfp_clause_parser import RfpClauseParser


def _read_document(path: str) -> str:
    return fix_presentation_forms(_read_document_raw(path))


def _read_document_raw(path: str) -> str:
    """Read an RFP document (real PDF, text-in-.pdf, or plain text) into raw text."""
    try:
        with open(path, "rb") as probe:
            is_pdf = probe.read(5).startswith(b"%PDF")
        if path.lower().endswith(".pdf") and is_pdf:
            try:
                from pypdf import PdfReader

                text = "\n\f".join((p.extract_text() or "") for p in PdfReader(path).pages)
                if text.strip():
                    return text
            except Exception:
                pass
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
        raise InsufficientInputError(
            "لم يُستخرج أي نص من ملفات كراسة الشروط (RFP). تأكد أن الملفات نصية أو فعّل OCR للملفات الممسوحة ضوئياً."
            " / No readable text could be extracted from the RFP files."
        )

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
        "requirement_count": 0,
        "referenced_standards": set(),
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
        compliance_gates["requirement_count"] += gates.get("requirement_count", 0)
        compliance_gates["referenced_standards"].update(gates.get("referenced_standards", []))

    compliance_gates["sbc_standards"] = sorted(compliance_gates["sbc_standards"])
    compliance_gates["referenced_standards"] = sorted(compliance_gates["referenced_standards"])

    return {
        "rfp_output": {
            "clauses": clauses,
            "segment_summary": segment_summary,
            "compliance_gates": compliance_gates,
            "document_count": len(parsed_docs),
        }
    }
