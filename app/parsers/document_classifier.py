"""
Document Triage Classifier.

Deterministic scoring engine that classifies uploaded tender-package documents
into categories (EVALUATION_CRITERIA / SPECIFICATIONS / BOQ / DRAWINGS / FORMS /
ADDENDUM / CONTRACT / OTHER) using filename + content signals, with an
optional LLM enrichment pass.

The EVALUATION_CRITERIA category is the platform's crown jewel: the pinned
criteria document becomes the binding gate for all proposal evaluations.
"""

import re
from typing import Any, Dict, List, Tuple

# Weighted signals per category: (pattern, score).
CATEGORY_SIGNALS: Dict[str, List[Tuple[str, float]]] = {
    "EVALUATION_CRITERIA": [
        (r"معايير\s*التقييم", 5.0),
        (r"evaluation\s+criteria", 5.0),
        (r"تقييم\s+العروض", 4.0),
        (r"technical\s+evaluation", 4.0),
        (r"جدول\s*الدرجات", 4.0),
        (r"درجات\s*التقييم", 4.0),
        (r"pass\s*/\s*fail", 3.0),
        (r"الشروط\s*الالزامية|الشروط\s*إلزامية", 3.0),
        (r"mandatory\s+requirement", 2.5),
        (r"الوزن\s*النسبي|weighting|weights?", 2.0),
        (r"استبعاد", 2.0),
        (r"disqualif", 2.0),
        (r"عبور|اجتياز", 1.5),
        (r"العروض\s*الفنية", 1.5),
        (r"technical\s+proposal\s+evaluation", 3.0),
        (r"\b(\d{1,2})\s*%\b.*\b(\d{1,2})\s*%\b", 1.5),  # multiple percentage weights
    ],
    "SPECIFICATIONS": [
        (r"المواصفات\s*الفنية", 4.0),
        (r"technical\s+specification", 4.0),
        (r"\bSBC\s*\d{3}", 2.5),
        (r"specifications?", 1.5),
        (r"مواصفات", 1.5),
    ],
    "BOQ": [
        (r"جدول\s*الكميات", 4.0),
        (r"bill\s+of\s+quantities|\bBOQ\b", 4.0),
        (r"كميات", 2.0),
        (r"unit\s+rate", 1.5),
    ],
    "DRAWINGS": [
        (r"\.(dxf|dwg)\b", 4.0),
        (r"مخططات?|لوحات?", 2.5),
        (r"drawings?", 2.5),
    ],
    "FORMS": [
        (r"نماذج|استمارة", 3.0),
        (r"\bforms?\b", 2.5),
        (r"تعبئة", 2.0),
    ],
    "ADDENDUM": [
        (r"ملحق\s*(رقم)?", 3.5),
        (r"addend(um|a)", 4.0),
        (r"إضافة\s*للكراسة", 3.0),
    ],
    "CONTRACT": [
        (r"شروط\s*عامة", 3.0),
        (r"العقد|عقد\s*التنفيذ", 3.0),
        (r"\bcontract\b(?!or)", 2.0),
        (r"conditions\s+of\s+contract", 3.5),
    ],
}

# Filename-only boosters (checked against the filename, stronger weight).
FILENAME_SIGNALS: Dict[str, List[Tuple[str, float]]] = {
    "EVALUATION_CRITERIA": [(r"معايير|تقييم|criteria|evaluation|درجات|scoring", 4.0)],
    "SPECIFICATIONS": [(r"مواصفات|spec|specification", 3.0)],
    "BOQ": [(r"boq|كميات|quantit", 3.0)],
    "DRAWINGS": [(r"drawing|dwg|dxf|مخطط|لوح", 3.0)],
    "ADDENDUM": [(r"addend|ملحق", 3.5)],
    "FORMS": [(r"form|نموذج|استمارة", 2.5)],
}

DEFAULT_CATEGORY = "OTHER"


def _score_text(text: str, signals: List[Tuple[str, float]]) -> float:
    lowered = text.lower()
    return sum(weight for pattern, weight in signals if re.search(pattern, lowered, re.IGNORECASE))


def classify_document(filename: str, text_sample: str) -> Dict[str, Any]:
    """
    Deterministic triage: returns {category, confidence, signals} where
    confidence is a normalized 0-1 score across category matches.
    """
    filename_score: Dict[str, float] = {}
    content_score: Dict[str, float] = {}

    sample = (text_sample or "")[:6000]

    for category, signals in FILENAME_SIGNALS.items():
        score = _score_text(filename or "", signals)
        if score > 0:
            filename_score[category] = filename_score.get(category, 0.0) + score

    for category, signals in CATEGORY_SIGNALS.items():
        score = _score_text(sample, signals)
        if score > 0:
            content_score[category] = content_score.get(category, 0.0) + score

    totals: Dict[str, float] = {}
    for category in set(filename_score) | set(content_score):
        totals[category] = (
            filename_score.get(category, 0.0) * 1.5 + content_score.get(category, 0.0)
        )

    if not totals:
        return {"category": DEFAULT_CATEGORY, "confidence": 0.0, "signals": {}}

    best = max(totals, key=totals.get)
    max_possible = 0.0
    for category in totals:
        max_possible += sum(w for _, w in CATEGORY_SIGNALS.get(category, []))
        max_possible += sum(w for _, w in FILENAME_SIGNALS.get(category, [])) * 1.5
    confidence = round(min(1.0, totals[best] / max(1.0, max_possible * 0.35)), 2)

    signals_summary = {
        "filename": round(filename_score.get(best, 0.0), 2),
        "content": round(content_score.get(best, 0.0), 2),
    }
    return {"category": best, "confidence": confidence, "signals": signals_summary}


def rank_criteria_candidates(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank documents by likelihood of being THE evaluation-criteria document."""
    ranked = []
    for doc in documents:
        score = 0.0
        if doc.get("doc_category") == "EVALUATION_CRITERIA":
            score += doc.get("classification_confidence", 0.0) * 60.0
        sample = (doc.get("text_sample") or "").lower()
        for pattern, weight in [
            (r"معايير\s*التقييم", 12), (r"evaluation\s+criteria", 12),
            (r"جدول\s*الدرجات", 10), (r"pass\s*/\s*fail", 8),
            (r"الوزن\s*النسبي|weighting", 7), (r"استبعاد|disqualif", 7),
            (r"العرض\s*الفني", 4), (r"technical\s+proposal", 4),
            (r"\b60\s*%\b|\b40\s*%\b", 5),
        ]:
            if re.search(pattern, sample, re.IGNORECASE):
                score += weight
        if score > 0:
            ranked.append({**doc, "criteria_score": round(score, 1)})
    ranked.sort(key=lambda d: d["criteria_score"], reverse=True)
    return ranked