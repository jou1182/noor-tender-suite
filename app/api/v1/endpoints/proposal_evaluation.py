"""Proposal Evaluation API — تقييم العرض الفني الوارد ضد معايير المنافسة.

يستخرج معايير التقييم من وثيقة المعايير المثبتة (pinned criteria) أو من
كل نصوص كراسة RFP، ثم يقيّم العرض الفني (فئة PROPOSAL) ضدها:
نقاط القوة، فجوات الاستبعاد، ودرجة توافق /100.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.platform_models import PackageDocument, PackageDocumentChunk
from app.parsers.proposal_evaluator import BidVsRFPEvaluator

router = APIRouter()


def _doc_text(db: Session, document_id: int) -> str:
    chunks = (
        db.query(PackageDocumentChunk)
        .filter(PackageDocumentChunk.document_id == document_id)
        .order_by(PackageDocumentChunk.chunk_index)
        .all()
    )
    return "\n".join(c.chunk_text for c in chunks)


def _tender_rfp_text(db: Session, tender_id: int) -> str:
    """يجمع نصوص كل مستندات الكراسة (عدا العروض نفسها) لبناء البنود الإلزامية."""
    docs = (
        db.query(PackageDocument)
        .filter(
            PackageDocument.tender_id == tender_id,
            PackageDocument.doc_category.in_(["EVALUATION_CRITERIA", "SPECIFICATIONS", "ADDENDUM", "CONTRACT"]),
        )
        .all()
    )
    parts: List[str] = []
    for doc in docs:
        text = _doc_text(db, doc.id)
        if text.strip():
            parts.append(text)
    return "\n\n".join(parts)[:120_000]


@router.post("/evaluate")
def evaluate_proposal(body: Dict[str, Any], db: Session = Depends(get_db)):
    """
    يقيّم العرض الفني ضد معايير المنافسة.
    Body: {tender_id, proposal_document_id?}
    - إن حُدد proposal_document_id يُستخدم؛ وإلا يُختار أول مستند PROPOSAL في المنافسة.
    """
    tender_id = int(body.get("tender_id") or 0)
    if not tender_id:
        raise HTTPException(status_code=422, detail="tender_id is required")

    proposal_doc_id = body.get("proposal_document_id")

    docs = db.query(PackageDocument).filter(PackageDocument.tender_id == tender_id).all()
    if not docs:
        raise HTTPException(status_code=404, detail="No documents ingested for this tender")

    proposal_doc = None
    if proposal_doc_id:
        proposal_doc = next((d for d in docs if d.id == int(proposal_doc_id)), None)
        if proposal_doc is None:
            raise HTTPException(status_code=404, detail="Proposal document not found")
    else:
        proposal_doc = next(
            (d for d in docs if d.doc_category == "PROPOSAL" and d.status == "PROCESSED"), None
        )
    if proposal_doc is None:
        raise HTTPException(
            status_code=422,
            detail="لا يوجد عرض فني مرفوع — ارفع ملف العرض الفني أولاً (يُصنَّف تلقائياً كـ PROPOSAL)",
        )

    proposal_text = _doc_text(db, proposal_doc.id)
    if len(proposal_text.strip()) < 50:
        raise HTTPException(status_code=422, detail="ملف العرض الفني بلا نص قابل للتحليل (قد يكون ممسوحاً ضوئياً — أعد رفعه مع تفعيل OCR)")

    rfp_text = _tender_rfp_text(db, tender_id)
    mandates = BidVsRFPEvaluator.parse_mandates(rfp_text) if rfp_text else None
    evaluator = BidVsRFPEvaluator(mandates)
    scorecard = evaluator.evaluate(proposal_text)

    # نقاط القوة = البنود المُجابة بعمق FULL
    strengths = [
        {
            "clause_id": m.clause_id,
            "section": m.section_title,
            "similarity": m.similarity,
            "keywords": m.matched_keywords,
        }
        for m in scorecard.matches
        if m.depth == "FULL"
    ]
    # نقاط الضعف = الفجوات (بنود غير مجابة أو مرفقات ناقصة)
    weaknesses = [
        {
            "clause_id": g.clause_id,
            "type": g.gap_type,
            "description": g.description,
            "penalty_points": g.penalty_points,
        }
        for g in scorecard.gaps
    ]
    # تغطية جزئية — تحتاج تعميقاً
    partials = [
        {"clause_id": m.clause_id, "section": m.section_title, "similarity": m.similarity}
        for m in scorecard.matches
        if m.depth == "PARTIAL"
    ]

    return {
        "tender_id": tender_id,
        "proposal_document": {"id": proposal_doc.id, "filename": proposal_doc.filename},
        "mandates_source": "rfp_corpus" if mandates else "default_mandates",
        "mandates_count": scorecard.clauses_checked,
        "score": scorecard.total_score,
        "addressed": scorecard.clauses_addressed,
        "total": scorecard.clauses_checked,
        "summary": scorecard.summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "partial_coverage": partials,
    }
