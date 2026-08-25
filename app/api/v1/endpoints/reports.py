from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import os
import shutil
import tempfile
from app.db.session import get_db
from app.models.tender_models import Tender, ComplianceRecord
from app.services.executive_report_service import ExecutiveReportService
from app.services.report_generator import ReportGenerator

router = APIRouter()

@router.get("/{tender_id}/bundle")
async def download_report_bundle(tender_id: int, db = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
        
    records = db.query(ComplianceRecord).filter(ComplianceRecord.tender_id == tender_id).all()
    record_dicts = [{"clause_code": r.clause_code, "status": r.status, "gap_analysis": r.gap_analysis} for r in records]
    
    tender_data = {
        "id": tender.id,
        "score": tender.technical_score,
        "records": record_dicts
    }
    
    metadata = tender.audit_metadata or {}
    rfis = metadata.get("rfi_drafts", []) if isinstance(metadata, dict) else []
    
    tmpdir = tempfile.mkdtemp()
    
    pdf_path = os.path.join(tmpdir, f"Tender_{tender_id}_Executive_Report.pdf")
    ExecutiveReportService.generate_pdf_report(tender_data, pdf_path)
    
    docx_path = os.path.join(tmpdir, f"Tender_{tender_id}_RFIs.docx")
    ExecutiveReportService.generate_rfi_docx(rfis, docx_path)
    
    xlsx_path = os.path.join(tmpdir, f"Tender_{tender_id}_Compliance.xlsx")
    ReportGenerator.generate_excel_matrix(records, xlsx_path)
    
    zip_base = os.path.join(tempfile.gettempdir(), f"Tender_{tender_id}_Bundle")
    shutil.make_archive(zip_base, 'zip', tmpdir)
    
    return FileResponse(f"{zip_base}.zip", filename=f"Tender_{tender_id}_Audit_Bundle.zip")
