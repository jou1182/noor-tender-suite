"""Bid-vs-RFP evaluation endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tender_models import Tender
from app.parsers.proposal_evaluator import BidVsRFPEvaluator
from app.schemas.proposal_evaluation import (
    RFPClauseMandate,
    TechnicalEvaluationScorecard,
)

router = APIRouter()


class EvaluateRequest(BaseModel):
    rfp_text: str = ""
    proposal_text: str = ""


@router.post("/{project_id}/evaluate-submittal")
async def evaluate_submittal(
    project_id: int,
    body: EvaluateRequest,
    db: Session = Depends(get_db),
):
    """Run the comparative bid-vs-RFP audit against a draft submittal."""
    tender = db.query(Tender).filter(Tender.id == project_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = tender.audit_metadata or {}
    rfp_text = body.rfp_text or str(metadata.get("rfp_output", {}).get("raw_text", "") or "")
    proposal_text = body.proposal_text or str(
        (metadata.get("proposal_artifacts") or {}).get("narrative", "") or ""
    )

    if not proposal_text:
        raise HTTPException(status_code=422, detail="No proposal draft text provided")

    mandates = BidVsRFPEvaluator.parse_mandates(rfp_text) if rfp_text else None
    scorecard: TechnicalEvaluationScorecard = BidVsRFPEvaluator(mandates).evaluate(proposal_text)

    return {"project_id": project_id, "scorecard": scorecard.model_dump()}


@router.get("/{project_id}/compliance-matrix")
async def compliance_matrix(project_id: int, db: Session = Depends(get_db)):
    """Return the clause-by-clause compliance breakdown with pass/fail flags."""
    tender = db.query(Tender).filter(Tender.id == project_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = tender.audit_metadata or {}
    existing = metadata.get("compliance_matrix")
    if existing:
        return {"project_id": project_id, "compliance_matrix": existing}

    # Deterministic default matrix from the built-in mandate set.
    evaluator = BidVsRFPEvaluator()
    rows = []
    for mandate in evaluator.mandates:
        rows.append(
            {
                "clause_id": mandate.clause_id,
                "category": mandate.category,
                "requirement": mandate.requirement,
                "weight": mandate.weight,
                "addressed": False,
                "status": "UNVERIFIED",
            }
        )
    return {"project_id": project_id, "compliance_matrix": {"clauses_checked": len(rows), "rows": rows}}
