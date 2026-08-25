"""Proposal Drafting API — compliance response skeletons + method statements."""

from typing import Any, Dict

from fastapi import APIRouter

from app.services.proposal_drafter import ProposalDrafter

router = APIRouter()


@router.get("/{tender_id}")
def get_drafts(tender_id: int):
    """Generate (deterministic template) drafting package for the tender."""
    return ProposalDrafter.generate(tender_id, enrich=False)


@router.post("/{tender_id}/enrich")
def enrich_drafts(tender_id: int):
    """Generate drafts with LLM enrichment via the bound provider (if enabled)."""
    return ProposalDrafter.generate(tender_id, enrich=True)