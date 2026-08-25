"""
Asynchronous persistence models for the vector retrieval layer.

Declarative SQLAlchemy 2.0 models (async-compatible) backed by PostgreSQL 16
+ pgvector. Includes the embedding store used by the hybrid retriever.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

EMBEDDING_DIM = 3072


class Project(Base):
    """A tender/project container for documents, BOQ items and VE results."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    boq_items: Mapped[List["BOQItem"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    ve_evaluations: Mapped[List["VEEvaluation"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    embeddings: Mapped[List["DocumentEmbedding"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class BOQItem(Base):
    """Normalized BOQ line item (mirrors BOQLineItem from the parsing pipeline)."""

    __tablename__ = "boq_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    item_no: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="")
    qty: Mapped[float] = mapped_column(Float, default=0.0)
    unit_rate: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    exposure_class: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    placement_context: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="boq_items")

    __table_args__ = (Index("ix_boq_items_project_id", "project_id"),)


class VEEvaluation(Base):
    """Value-engineering evaluation result for a BOQ item (VEOpportunityCard)."""

    __tablename__ = "ve_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    boq_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("boq_items.id", ondelete="SET NULL"), nullable=True)
    boq_item: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_alternative: Mapped[str] = mapped_column(Text, nullable=False)
    net_savings_sar: Mapped[float] = mapped_column(Float, default=0.0)
    speed_index_gain_percent: Mapped[float] = mapped_column(Float, default=0.0)
    sbc_status: Mapped[str] = mapped_column(String(16), default="COMPLIANT")
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=True)
    sbc_304_references: Mapped[List[str]] = mapped_column(JSONB, default=list)
    technical_justification: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="ve_evaluations")

    __table_args__ = (Index("ix_ve_evaluations_project_id", "project_id"),)


class DocumentEmbedding(Base):
    """Chunked document embedding stored as a pgvector Vector(3072)."""

    __tablename__ = "document_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    document_type: Mapped[str] = mapped_column(String(32), default="spec")  # spec | boq | clause
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    # OpenAI text-embedding-3-large -> 3072 dimensions.
    embedding: Mapped[List[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    standard: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)      # e.g. SBC-304
    section: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)       # e.g. 7.7
    exposure_class: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)  # e.g. S2
    source_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Optional["Project"]] = relationship(back_populates="embeddings")

    __table_args__ = (
        # HNSW index for fast approximate cosine similarity on the dense vector.
        Index(
            "ix_document_embeddings_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # GIN index for full-text keyword search (tsvector).
        Index(
            "ix_document_embeddings_chunk_tsv",
            func.to_tsvector("english", func.coalesce(chunk_text, "")),
            postgresql_using="gin",
        ),
        UniqueConstraint("project_id", "document_type", "chunk_index", name="uq_embedding_chunk"),
    )
