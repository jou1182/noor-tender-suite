"""Proposal generation & export endpoint."""

import os
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.generators.docx_engine import DocxProposalGenerator
from app.generators.narrative_engine import ProposalNarrativeEngine
from app.generators.pdf_engine import PdfProposalGenerator
from app.models.tender_models import Tender

router = APIRouter()

EXPORT_DIR = os.path.join(os.getcwd(), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


class ProposalRequest(BaseModel):
    format: str = "both"  # "pdf" | "docx" | "both"


def _build_project_dict(tender: Tender) -> Dict[str, Any]:
    metadata = tender.audit_metadata or {}
    return {
        "name": tender.title or f"Tender #{tender.id}",
        "client": tender.client_name or "Client",
        "tender_reference": f"TEN-{tender.id:04d}",
        "scope": "Structural concrete, earthworks and steel reinforcement works "
                 "per the tender technical specification and SBC-304.",
    }


def _build_state_sections(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract VE proposals, compliance register, risks and evaluation from state."""
    ve_matrix = metadata.get("ve_matrix") or metadata.get("ve_output", {}).get("ve_matrix") or []
    ve_proposals: List[Dict[str, Any]] = []
    if isinstance(ve_matrix, list):
        ve_proposals = ve_matrix
    elif isinstance(ve_matrix, dict):
        ve_proposals = ve_matrix.get("cards") or ve_matrix.get("proposals") or []

    compliance = metadata.get("rfp_compliance_matrix", {}).get("matrix") or metadata.get("cross_exam_output", {}).get("matrix") or []
    if not compliance and isinstance(metadata.get("compliance_records"), list):
        compliance = metadata["compliance_records"]

    risks = metadata.get("tender_evaluation", {}).get("risks") or []
    evaluation = metadata.get("tender_evaluation") or {
        "overall_score": tender_score(metadata),
        "pass_fail": (tender_score(metadata) or 0) >= 70,
        "summary": "Technical evaluation summary.",
    }
    return {"ve_proposals": ve_proposals, "compliance": compliance, "risks": risks, "evaluation": evaluation}


def tender_score(metadata: Dict[str, Any]) -> float:
    arb = metadata.get("arbitrator_output") or {}
    return float(arb.get("final_score", metadata.get("technical_score", 82.5)))


@router.post("/{project_id}/generate-proposal")
async def generate_proposal(
    project_id: int,
    body: ProposalRequest,
    db: Session = Depends(get_db),
):
    """Generate a technical proposal (PDF and/or DOCX) from persisted project state."""
    tender = db.query(Tender).filter(Tender.id == project_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = tender.audit_metadata or {}
    project = _build_project_dict(tender)
    sections = _build_state_sections(metadata)

    narrative_engine = ProposalNarrativeEngine()
    context = narrative_engine.build_context(
        project=project,
        ve_proposals=sections["ve_proposals"],
        compliance=sections["compliance"],
        risks=sections["risks"],
        evaluation=sections["evaluation"],
    )

    run_id = uuid.uuid4().hex[:8]
    base = os.path.join(EXPORT_DIR, f"TEN-{project_id:04d}-{run_id}")
    urls: Dict[str, str] = {}
    fmt = body.format.lower()

    if fmt in ("pdf", "both"):
        pdf_path = f"{base}.pdf"
        PdfProposalGenerator().generate(context, pdf_path)
        urls["pdf"] = f"/api/v1/exports/download/{os.path.basename(pdf_path)}"
    if fmt in ("docx", "both"):
        docx_path = f"{base}.docx"
        DocxProposalGenerator().generate(context, docx_path)
        urls["docx"] = f"/api/v1/exports/download/{os.path.basename(docx_path)}"
    if not urls:
        raise HTTPException(status_code=422, detail="Unsupported format")

    return {"project_id": project_id, "run_id": run_id, "downloads": urls}


@router.get("/download/{filename}")
async def download_proposal(filename: str):
    """Serve a generated proposal artifact."""
    safe = os.path.basename(filename)
    path = os.path.join(EXPORT_DIR, safe)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path, filename=safe)
