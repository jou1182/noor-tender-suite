"""
Platform Models — Dynamic LLM Providers, Agent Registry & Document Intelligence.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, ForeignKey
from datetime import datetime
from app.db.base import Base


class LLMProvider(Base):
    """Dynamically registered LLM providers (OpenAI / Claude / Gemini / DeepSeek / Ollama / LM Studio)."""

    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    provider_type = Column(String(40), nullable=False, default="openai")  # openai|anthropic|google|deepseek|ollama|lmstudio
    base_url = Column(String(400), default="")
    api_key_encrypted = Column(Text, default="")
    model = Column(String(160), default="")
    embedding_model = Column(String(160), default="")
    enabled = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    privacy_safe = Column(Boolean, default=False)  # local providers (Ollama/LM Studio)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentEntry(Base):
    """Dynamic agent registry — editable identity, role, prompt and model binding."""

    __tablename__ = "agent_registry"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(60), unique=True, nullable=False, index=True)
    name_ar = Column(String(160), default="")
    name_en = Column(String(160), default="")
    avatar_emoji = Column(String(8), default="🤖")
    role = Column(String(240), default="")
    pipeline_type = Column(String(40), default="technical")  # technical|financial|drafting|shared
    system_prompt = Column(Text, default="")
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), nullable=True)
    model_override = Column(String(160), default="")
    temperature = Column(Float, default=0.3)
    enabled = Column(Boolean, default=True)
    execution_order = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)


class PackageDocument(Base):
    """Document inventory for large RFP / proposal packages (5GB+ scale)."""

    __tablename__ = "package_documents"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, index=True, nullable=False)
    filename = Column(String(400), nullable=False)
    rel_path = Column(String(800), default="")
    size_bytes = Column(Integer, default=0)
    file_ext = Column(String(12), default="")
    doc_category = Column(String(60), default="UNCATEGORIZED")  # EVALUATION_CRITERIA|SPECIFICATIONS|BOQ|DRAWINGS|FORMS|ADDENDUM|CONTRACT|OTHER
    classification_confidence = Column(Float, default=0.0)
    classification_signals = Column(Text, default="")
    status = Column(String(30), default="REGISTERED")  # REGISTERED|PROCESSING|PROCESSED|FAILED
    process_error = Column(Text, default="")
    page_count = Column(Integer, default=0)
    text_chars = Column(Integer, default=0)
    ocr_used = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    is_pinned_criteria = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class PackageDocumentChunk(Base):
    """Text chunks per document for RAG / keyword retrieval with citations."""

    __tablename__ = "package_document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True, nullable=False)
    tender_id = Column(Integer, index=True, nullable=False)
    chunk_index = Column(Integer, default=0)
    page_number = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=False)
    vector_id = Column(String(80), default="")


class TenderRequirement(Base):
    """Binding evaluation criteria extracted from the pinned criteria document."""

    __tablename__ = "tender_requirements"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, index=True, nullable=False)
    source_document_id = Column(Integer, nullable=True)
    requirement_type = Column(String(40), default="MANDATORY")  # MANDATORY|WEIGHTED|DISQUALIFICATION
    requirement_text = Column(Text, nullable=False)
    weight = Column(Float, nullable=True)
    clause_ref = Column(String(80), default="")
    created_at = Column(DateTime, default=datetime.utcnow)