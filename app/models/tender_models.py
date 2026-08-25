from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    contract_type = Column(String)
    status = Column(String, default="draft")
    technical_score = Column(Float, nullable=True)
    audit_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("TenderDocument", back_populates="tender")
    compliance_records = relationship("ComplianceRecord", back_populates="tender")

class TenderDocument(Base):
    __tablename__ = "tender_documents"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    document_type = Column(String)
    file_path = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)  # Using metadata_json to avoid conflict with Base.metadata

    tender = relationship("Tender", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("tender_documents.id"), nullable=False)
    chunk_text = Column(String, nullable=False)
    page_number = Column(Integer, nullable=True)
    is_table = Column(Boolean, default=False)
    qdrant_id = Column(String, nullable=True)

    document = relationship("TenderDocument", back_populates="chunks")

class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    clause_code = Column(String, nullable=False)
    requirement = Column(String, nullable=False)
    status = Column(String, nullable=False)
    severity = Column(String)
    gap_analysis = Column(String, nullable=True)

    tender = relationship("Tender", back_populates="compliance_records")
