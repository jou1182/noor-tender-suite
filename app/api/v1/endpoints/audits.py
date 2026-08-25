from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from typing import List
import shutil
import os
import hashlib

from app.db.session import get_db
from app.services.audit_service import AuditService
from app.services.report_generator import ReportGenerator
from app.models.tender_models import Tender, ComplianceRecord
from app.models.audit_log import AuditLog
from app.api.deps import require_role, CurrentUser

router = APIRouter()

def process_audit_background(tender_id: int, rfp_paths: List[str], schedule_path: str):
    db = next(get_db())
    try:
        service = AuditService(db)
        service.run_full_audit(tender_id, rfp_paths, schedule_path)
    finally:
        db.close()

@router.post("/{tender_id}/trigger")
async def trigger_audit(
    tender_id: int,
    background_tasks: BackgroundTasks,
    rfp_files: List[UploadFile] = File(...),
    schedule_file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role(["lead_architect", "auditor"])),
    db: Session = Depends(get_db)
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    upload_dir = f"uploads/{tender_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    rfp_paths = []
    for rfp in rfp_files:
        path = os.path.join(upload_dir, rfp.filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(rfp.file, buffer)
        rfp_paths.append(path)
        
    schedule_path = os.path.join(upload_dir, schedule_file.filename)
    with open(schedule_path, "wb") as buffer:
        shutil.copyfileobj(schedule_file.file, buffer)

    background_tasks.add_task(process_audit_background, tender_id, rfp_paths, schedule_path)
    
    tender.status = "processing"
    
    # Immutable Audit Logging
    audit_entry = AuditLog(
        tender_id=tender_id,
        user_id=current_user.user_id,
        action="TRIGGER_AUDIT",
        agent_name="orchestrator",
        payload_hash=hashlib.sha256(f"{rfp_paths}{schedule_path}".encode()).hexdigest()
    )
    db.add(audit_entry)
    
    db.commit()
    return {"message": "Audit processing started in background", "tender_id": tender_id}

@router.get("/{tender_id}")
async def get_tender_status(tender_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role(["lead_architect", "auditor", "viewer"]))):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    records = db.query(ComplianceRecord).filter(ComplianceRecord.tender_id == tender_id).all()
    
    return {
        "tender_id": tender.id,
        "status": tender.status,
        "technical_score": tender.technical_score,
        "audit_metadata": tender.audit_metadata or {},
        "records": [
            {
                "clause_code": r.clause_code,
                "requirement": r.requirement,
                "status": r.status,
                "severity": r.severity,
                "gap_analysis": r.gap_analysis
            } for r in records
        ]
    }

@router.get("/{tender_id}/export")
async def export_tender_report(tender_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role(["lead_architect", "auditor", "viewer"]))):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    records = db.query(ComplianceRecord).filter(ComplianceRecord.tender_id == tender_id).all()
    output_path = f"report_{tender_id}.xlsx"
    ReportGenerator.generate_excel_matrix(records, output_path)
    
    audit_entry = AuditLog(
        tender_id=tender_id,
        user_id=current_user.user_id,
        action="EXPORT_REPORT",
        agent_name="system"
    )
    db.add(audit_entry)
    db.commit()
    
    return FileResponse(output_path, filename=f"Tender_{tender_id}_Audit_Report.xlsx")
