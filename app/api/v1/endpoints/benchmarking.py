from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.db.session import get_db
from app.models.tender_models import Tender
from app.services.comparative_service import ComparativeService

router = APIRouter()

@router.get("/compare")
async def compare_tenders(tender_ids: List[int] = Query(...), db = Depends(get_db)):
    tenders = db.query(Tender).filter(Tender.id.in_(tender_ids)).all()
    if len(tenders) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least 2 valid tender IDs for benchmarking.")
        
    benchmark = ComparativeService.generate_benchmark(tenders)
    return benchmark
