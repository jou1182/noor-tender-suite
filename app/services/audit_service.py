import os
from typing import List
from sqlalchemy.orm import Session
from app.models.tender_models import Tender, TenderDocument, ComplianceRecord
from app.core.vector_store import VectorStoreAdapter
from app.agents.graph import build_orchestration_graph

class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStoreAdapter()
        self.graph = build_orchestration_graph()

    def run_full_audit(self, tender_id: int, rfp_files: List[str], schedule_file: str) -> dict:
        tender = self.db.query(Tender).filter(Tender.id == tender_id).first()
        if not tender:
            raise ValueError(f"Tender {tender_id} not found")

        # 1. Ingestion Phase: Save document metadata and index into Qdrant
        for file in rfp_files:
            doc = TenderDocument(tender_id=tender.id, document_type="RFP", file_path=file)
            self.db.add(doc)
            # Simulated: self.vector_store.client.upsert(collection_name=self.vector_store.collection_name, points=[...])
            
        self.db.commit()

        # 2. Execution Phase: Trigger LangGraph workflow
        initial_state = {
            "project_id": str(tender_id),
            "rfp_documents": rfp_files,
            "methodology_documents": [],
            "schedule_file": schedule_file,
            "boq_file": "",
            "extracted_requirements": [],
            "methodology_findings": [],
            "schedule_audit": {},
            "qaqc_findings": [],
            "red_team_feedback": [],
            "final_score": 0.0,
            "summary": "",
            "status": "started"
        }
        
        final_state = self.graph.invoke(initial_state)

        # 3. Persistence Phase: Save extracted records and scores to PostgreSQL
        tender.technical_score = final_state.get("final_score", 0.0)
        tender.status = final_state.get("status", "audited")
        tender.audit_metadata = {
            "red_team_feedback": final_state.get("red_team_feedback", []),
            "rfi_drafts": final_state.get("rfi_drafts", [])
        }
        
        for req in final_state.get("extracted_requirements", []):
            record = ComplianceRecord(
                tender_id=tender.id,
                clause_code=req.get("req_id", "N/A"),
                requirement=req.get("desc", "N/A"),
                status="Compliant",
                severity="Low"
            )
            self.db.add(record)
            
        self.db.commit()
        
        return final_state
