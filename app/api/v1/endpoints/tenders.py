"""Tenders API — dynamic workspace list, cascade delete & swarm launch.

يغطي دورة حياة المنافسة كاملة:
- GET    /tenders                قائمة ديناميكية (تغذي القائمة العلوية والفلاتر)
- POST   /tenders                إنشاء منافسة يدوية (بدون ملفات — تُرفع لاحقاً)
- DELETE /tenders/{id}           حذف متسلسل (مستندات + سجلات + ملفات القرص)
- POST   /tenders/{id}/launch    إطلاق سرب الوكلاء على منافسة قائمة (بعد الرفع)

المنصة لا تحتفظ بأي عملاء ثابتين في الكود — كل شيء يُدار من قاعدة البيانات.
"""

import os
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.tender_models import ComplianceRecord, Tender, TenderDocument

router = APIRouter()


def _serialize(tender: Tender, document_count: int = 0) -> Dict[str, Any]:
    return {
        "id": tender.id,
        "title": tender.title,
        "client_name": tender.client_name,
        "status": tender.status,
        "technical_score": tender.technical_score,
        "created_at": str(tender.created_at or ""),
        "document_count": document_count,
    }


def _document_count(db: Session, tender_id: int) -> int:
    return db.query(TenderDocument).filter(TenderDocument.tender_id == tender_id).count()


@router.get("")
def list_tenders(db: Session = Depends(get_db)):
    """قائمة المنافسات الحية — مصدر الحقيقة الوحيد للقائمة العلوية والفلاتر."""
    tenders = db.query(Tender).order_by(Tender.created_at.desc(), Tender.id.desc()).all()
    counts: Dict[int, int] = {}
    if tenders:
        rows = (
            db.query(TenderDocument.tender_id, func.count(TenderDocument.id))
            .group_by(TenderDocument.tender_id)
            .all()
        )
        counts = {tender_id: count for tender_id, count in rows}
    return {
        "tenders": [_serialize(t, counts.get(t.id, 0)) for t in tenders],
        "count": len(tenders),
    }


@router.post("")
def create_tender(body: Dict[str, Any], db: Session = Depends(get_db)):
    """إنشاء منافسة جديدة يدوياً (العنوان والعميل فقط — الملفات تُرفع لاحقاً)."""
    title = (body.get("title") or "").strip()
    client_name = (body.get("client_name") or "").strip() or title or "Unnamed Client"
    if not title:
        raise HTTPException(status_code=422, detail="title is required")
    tender = Tender(title=title, client_name=client_name, status="draft")
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return _serialize(tender, 0)


@router.get("/{tender_id}")
def get_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return _serialize(tender, _document_count(db, tender_id))


@router.patch("/{tender_id}")
def update_tender(tender_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    """إعادة تسمية المنافسة أو تعديل اسم العميل أو الحالة يدوياً."""
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if "title" in body and str(body["title"]).strip():
        tender.title = str(body["title"]).strip()
    if "client_name" in body and str(body["client_name"]).strip():
        tender.client_name = str(body["client_name"]).strip()
    if "status" in body and str(body["status"]).strip():
        tender.status = str(body["status"]).strip()
    db.commit()
    db.refresh(tender)
    return _serialize(tender, _document_count(db, tender_id))


@router.delete("/{tender_id}")
def delete_tender(tender_id: int, db: Session = Depends(get_db)):
    """
    حذف متسلسل للمنافسة بكل ما يرتبط بها:
    سجلات الامتثال، مستندات الحزمة، سجل التدقيق، الملفات على القرص، ثم المنافسة نفسها.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    removed_files = 0
    docs = db.query(TenderDocument).filter(TenderDocument.tender_id == tender_id).all()
    for doc in docs:
        path = doc.file_path or ""
        if path and os.path.isfile(path):
            try:
                os.remove(path)
                removed_files += 1
            except OSError:
                pass  # الملف مقفل أو خارج نطاقنا — نكمل حذف السجلات
    # مجلد الرفع الخاص بالمنافسة إن صار فارغاً
    upload_dir = os.path.join(os.getenv("UPLOAD_ROOT_FALLBACK", "uploads"), f"{tender_id}")
    if os.path.isdir(upload_dir) and not os.listdir(upload_dir):
        try:
            os.rmdir(upload_dir)
        except OSError:
            pass

    deleted_compliance = (
        db.query(ComplianceRecord).filter(ComplianceRecord.tender_id == tender_id).delete()
    )
    deleted_docs = (
        db.query(TenderDocument).filter(TenderDocument.tender_id == tender_id).delete()
    )
    deleted_logs = db.query(AuditLog).filter(AuditLog.tender_id == tender_id).delete()
    db.delete(tender)
    db.commit()

    return {
        "deleted": tender_id,
        "removed_files": removed_files,
        "deleted_documents": deleted_docs,
        "deleted_compliance_records": deleted_compliance,
        "deleted_audit_logs": deleted_logs,
    }


@router.post("/{tender_id}/launch")
async def launch_tender_swarm(
    tender_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    زر «إنطلقوا أيها الوكلاء» — يطلق سرب اللانغجراف على منافسة موجودة أصلاً.
    يعتمد على المستندات المسجلة في tender_documents (من رفع سابق عبر /audits/trigger).
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    if tender.status == "processing":
        raise HTTPException(status_code=409, detail="Swarm already running for this tender")

    rfp_paths: list[str] = []
    schedule_path = ""
    for doc in db.query(TenderDocument).filter(TenderDocument.tender_id == tender_id).all():
        if not doc.file_path or not os.path.isfile(doc.file_path):
            continue
        if doc.document_type == "SCHEDULE" and not schedule_path:
            schedule_path = doc.file_path
        elif doc.document_type == "RFP":
            rfp_paths.append(doc.file_path)

    if not rfp_paths or not schedule_path:
        raise HTTPException(
            status_code=422,
            detail="Cannot launch: at least one RFP file and one SCHEDULE file must be uploaded first",
        )

    tender.status = "processing"
    db.add(AuditLog(tender_id=tender_id, action="TRIGGER_AUDIT", user_id="workspace_launch"))
    db.commit()

    from app.main import _run_swarm_audit

    background_tasks.add_task(
        _run_swarm_audit, tender_id, rfp_paths, schedule_path, tender.client_name
    )
    return {
        "tender_id": tender_id,
        "status": "processing",
        "message": "Audit triggered — swarm orchestration running",
    }
