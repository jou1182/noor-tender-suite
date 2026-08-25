"""
Criteria Extractor — converts the pinned evaluation-criteria document text
into structured, binding TenderRequirement records:

  - MANDATORY gates (Pass/Fail conditions)
  - WEIGHTED scoring criteria (with percentage weights)
  - DISQUALIFICATION conditions (auto-rejection triggers)
"""

import re
from typing import Any, Dict, List

from app.parsers.rfp_clause_parser import RfpClauseParser

MANDATORY_SIGNALS = re.compile(
    r"(shall\s+be\s+)?(mandatory|إلزامي|الزامي|pass\s*/?\s*fail|شرط\s*إلزامي|يجب|لا\s*يقل|لا\s*يتجاوز)",
    re.IGNORECASE,
)
DISQUALIFICATION_SIGNALS = re.compile(
    r"(استبعاد|يستبعد|يُستبعد|استبعد|استبعاد\s*من\s*المنافسة|disqualif|rejected\s+outright|عدم\s*قبول)",
    re.IGNORECASE,
)
WEIGHT_PATTERN = re.compile(r"(\d{1,3})\s*%")
EVALUATION_CONTEXT = re.compile(
    r"(التقييم|الدرج|الوزن|التسجيل|evaluation|scoring|weight|mark|grade)", re.IGNORECASE
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_requirements(document_text: str, source_document_id: int = 0,
                         max_requirements: int = 200) -> List[Dict[str, Any]]:
    """
    Deterministic extraction of binding requirements from the pinned
    evaluation-criteria document text.
    """
    requirements: List[Dict[str, Any]] = []
    seen: set = set()

    # 1) Clause-level parse for mandatory gates.
    try:
        parsed = RfpClauseParser.parse_text(document_text)
        clauses = parsed.get("clauses", [])
    except Exception:  # noqa: BLE001
        clauses = []

    for clause in clauses:
        text = _clean(clause.get("text", ""))
        if len(text) < 15:
            continue
        ref = clause.get("ref", "")
        req_type = None
        if DISQUALIFICATION_SIGNALS.search(text):
            req_type = "DISQUALIFICATION"
        elif MANDATORY_SIGNALS.search(text):
            req_type = "MANDATORY"

        weight = None
        if EVALUATION_CONTEXT.search(text):
            weights = WEIGHT_PATTERN.findall(text)
            if weights:
                weight = float(max(int(w) for w in weights))
                if req_type is None:
                    req_type = "WEIGHTED"

        if req_type is None:
            continue

        key = text[:120].lower()
        if key in seen:
            continue
        seen.add(key)

        requirements.append({
            "requirement_type": req_type,
            "requirement_text": text[:1200],
            "weight": weight,
            "clause_ref": ref,
            "source_document_id": source_document_id,
        })
        if len(requirements) >= max_requirements:
            return requirements

    # 2) Line-level fallback for percentage-weighted evaluation tables.
    for line in document_text.splitlines():
        line = _clean(line)
        if len(line) < 12 or not EVALUATION_CONTEXT.search(line):
            continue
        weights = WEIGHT_PATTERN.findall(line)
        if not weights:
            continue
        key = line[:120].lower()
        if key in seen:
            continue
        seen.add(key)
        requirements.append({
            "requirement_type": "WEIGHTED",
            "requirement_text": line[:1200],
            "weight": float(max(int(w) for w in weights)),
            "clause_ref": "",
            "source_document_id": source_document_id,
        })
        if len(requirements) >= max_requirements:
            break

    return requirements