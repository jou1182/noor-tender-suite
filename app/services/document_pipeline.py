"""
Document Processing Pipeline.

Background pipeline for each registered tender document:
  REGISTERED -> PROCESSING -> PROCESSED | FAILED

Stages:
  1. Text extraction  â€” pypdf (PDF), python-docx (DOCX), openpyxl (XLSX),
     ezdxf (DXF), plain text; OCR fallback (Tesseract) for scanned PDFs when
     available and enabled.
  2. Triage classification â€” deterministic signal scoring (document_classifier).
  3. Chunking â€” ~900-char chunks with page tracking.
  4. Vector indexing â€” Qdrant collection per tender when an embedding provider
     is configured; keyword retrieval over DB chunks as fallback.
"""

import io
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db.session import SessionLocal
from app.models.platform_models import PackageDocument, PackageDocumentChunk

CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
OCR_TEXT_FLOOR = 200  # chars per page below which OCR is attempted


# ------------------------------------------------------------ extraction ---

def _extract_pdf(path: str, ocr_enabled: bool) -> tuple[str, int, bool]:
    """PDF text via pypdf; raw-stream fallback; OCR fallback per scanned pages."""
    page_count = 0
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        page_count = len(reader.pages)
        pages_text: List[str] = []
        ocr_used = False
        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            if not text and ocr_enabled:
                ocr_text = _ocr_pdf_page(path, len(pages_text))
                if ocr_text:
                    text = ocr_text
                    ocr_used = True
            pages_text.append(text)
        joined = "\n\f".join(pages_text)
        if len(joined.strip()) >= 50:
            return joined, page_count, ocr_used
    except Exception as exc:  # noqa: BLE001
        pages_text = []

    # Fallback: dependency-free extractor (handles raw-text content streams).
    try:
        from app.parsers.pdf_parser import extract_text_from_pdf as raw_extract

        text = raw_extract(path)
        if text and text.strip():
            pages = text.split("\f") if "\f" in text else [text]
            return text, max(1, len(pages)), False
    except Exception:  # noqa: BLE001
        pass

    # Last resort: OCR the whole document when enabled and available.
    if ocr_enabled:
        try:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(path, dpi=200)
            text = "\n\f".join((pytesseract.image_to_string(img) or "") for img in images)
            if text.strip():
                return text, len(images), True
        except Exception:  # noqa: BLE001
            pass
    return "", page_count, False


def _ocr_pdf_page(path: str, page_index: int) -> str:
    """OCR a single PDF page via pdf2image + pytesseract (graceful if absent)."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image  # noqa: F401  (pdf2image dependency check)

        images = convert_from_path(path, first_page=page_index + 1, last_page=page_index + 1, dpi=200)
        if not images:
            return ""
        return pytesseract.image_to_string(images[0]) or ""
    except Exception:  # noqa: BLE001
        return ""


def _extract_docx(path: str) -> tuple[str, int, bool]:
    try:
        from docx import Document

        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text, 0, False
    except Exception as exc:  # noqa: BLE001
        return f"[DOCX extraction error: {exc}]", 0, False


def _extract_xlsx(path: str) -> tuple[str, int, bool]:
    try:
        from app.parsers.excel_parser import extract_boq_from_workbook

        rows = extract_boq_from_workbook(path)
        lines = [
            f"{r['description']} | qty {r['qty']} | rate {r['unit_rate']} | total {r['total_amount']}"
            for r in rows
        ]
        return "\n".join(lines), 0, False
    except Exception as exc:  # noqa: BLE001
        return f"[XLSX extraction error: {exc}]", 0, False


def _extract_text(path: str, ext: str, ocr_enabled: bool) -> tuple[str, int, bool]:
    ext = ext.lower()
    if ext == ".pdf":
        # Guard: files saved with .pdf extension but containing plain text.
        try:
            with open(path, "rb") as probe:
                if not probe.read(5).startswith(b"%PDF"):
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        return fh.read(), 0, False
        except OSError:
            pass
        return _extract_pdf(path, ocr_enabled)
    if ext in (".docx", ".doc"):
        return _extract_docx(path)
    if ext in (".xlsx", ".xls"):
        return _extract_xlsx(path)
    if ext in (".txt", ".md", ".rft", ".csv"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            return text, 0, False
        except Exception as exc:  # noqa: BLE001
            return f"[text extraction error: {exc}]", 0, False
    return "", 0, False


# ------------------------------------------------------------ chunking ---

def _chunk_text(text: str) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks while PRESERVING line structure
    (clause boundaries must survive for downstream requirement extraction)."""
    chunks: List[Dict[str, Any]] = []
    page = 1
    current = ""
    for segment in text.split("\f"):
        for line in segment.splitlines():
            line = line.strip()
            if not line:
                continue
            if len(current) + len(line) + 1 > CHUNK_SIZE:
                if current.strip():
                    chunks.append({"page": page, "text": current.strip()})
                current = ""
            current += line + "\n"
        page += 1
    if current.strip():
        chunks.append({"page": page, "text": current.strip()})
    return [c for c in chunks if len(c["text"]) > 20]


# ------------------------------------------------------------- pipeline ---

def _get_embedding_provider():
    from app.models.platform_models import LLMProvider

    db = SessionLocal()
    try:
        provider = (
            db.query(LLMProvider)
            .filter(LLMProvider.enabled.is_(True), LLMProvider.embedding_model.isnot(None),
                    LLMProvider.embedding_model != "")
            .first()
        )
        return provider
    finally:
        db.close()


def _index_to_qdrant(tender_id: int, document_id: int, chunks: List[Dict[str, Any]]) -> int:
    """Vector-index chunks into the tender's Qdrant collection. Returns indexed count."""
    provider = _get_embedding_provider()
    if provider is None:
        return 0
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams

        from app.core.llm_gateway_v2 import embed
        from app.core.vector_store import get_global_client

        client: QdrantClient = get_global_client()
        collection = f"tender_{tender_id}_docs"
        if not client.collection_exists(collection_name=collection):
            sample = embed(provider, chunks[0]["text"] if chunks else "probe")
            if not sample:
                return 0
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=len(sample), distance=Distance.COSINE),
            )
        points = []
        for idx, chunk in enumerate(chunks):
            vector = embed(provider, chunk["text"])
            if not vector:
                continue
            points.append(PointStruct(
                id=hash(f"{document_id}-{idx}") % (10 ** 12),
                vector=vector,
                payload={"document_id": document_id, "page": chunk["page"], "text": chunk["text"][:1200]},
            ))
        if points:
            client.upsert(collection_name=collection, points=points)
        return len(points)
    except Exception as exc:  # noqa: BLE001
        print(f"[PIPELINE] vector indexing skipped: {exc}")
        return 0


def process_document(document_id: int, ocr_enabled: bool = False, force_category: str = "") -> Dict[str, Any]:
    """
    Process a registered document end-to-end. Safe to run in a background task.
    force_category يتجاوز التصنيف التلقائي (مثال: PROPOSAL من زر الرفع المخصص).
    Returns a summary dict {status, category, confidence, chunks, pages}.
    """
    from app.parsers.document_classifier import classify_document

    db = SessionLocal()
    doc = db.query(PackageDocument).filter(PackageDocument.id == document_id).first()
    if doc is None:
        db.close()
        return {"status": "NOT_FOUND"}

    doc.status = "PROCESSING"
    db.commit()

    try:
        path = doc.rel_path
        ext = doc.file_ext.lower()
        text, page_count, ocr_used = "", 0, False

        if is_cad_file(doc.filename):
            from app.parsers.cad_parser import extract_cad_summary

            summary = extract_cad_summary(path, doc.filename)
            text = json_text = str(summary.get("text_samples", "") or "")[:4000]
            text = f"CAD file {doc.filename}: layers={summary.get('layer_count', 0)}, blocks={summary.get('block_count', 0)}. " + \
                   " ".join(summary.get("text_samples", [])[:20])
            page_count = 0
        else:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Document file missing on disk: {path}")
            text, page_count, ocr_used = _extract_text(path, ext, ocr_enabled)

        from app.parsers.arabic_text import fix_presentation_forms

        text = fix_presentation_forms(text)
        classification = classify_document(doc.filename, text)

        if force_category:
            # تجاوز يدوي موثوق (زر الرفع المخصص) — نسجل أن المستخدم حدد الفئة
            doc.doc_category = force_category
            doc.classification_confidence = 1.0
            doc.classification_signals = f"manual_override:{classification['category']}"
        else:
            doc.doc_category = classification["category"]
            doc.classification_confidence = classification["confidence"]
            doc.classification_signals = str(classification["signals"])
        doc.page_count = page_count
        doc.text_chars = len(text)
        doc.ocr_used = ocr_used

        chunks = _chunk_text(text)
        doc.chunk_count = len(chunks)

        for chunk in chunks:
            db.add(PackageDocumentChunk(
                document_id=doc.id,
                tender_id=doc.tender_id,
                chunk_index=len(chunks) and chunks.index(chunk) or 0,
                page_number=chunk["page"],
                chunk_text=chunk["text"],
            ))

        indexed = _index_to_qdrant(doc.tender_id, doc.id, chunks)

        doc.status = "PROCESSED"
        doc.processed_at = datetime.utcnow()
        db.commit()
        print(f"[PIPELINE] {doc.filename} -> {doc.doc_category} ({doc.classification_confidence}), "
              f"{len(chunks)} chunks, {indexed} vector-indexed")
        return {
            "status": "PROCESSED", "category": doc.doc_category,
            "confidence": doc.classification_confidence, "chunks": len(chunks),
            "pages": page_count, "vector_indexed": indexed,
        }
    except Exception as exc:  # noqa: BLE001
        doc.status = "FAILED"
        doc.process_error = str(exc)[:800]
        doc.processed_at = datetime.utcnow()
        db.commit()
        print(f"[PIPELINE] {doc.filename} FAILED: {exc}")
        return {"status": "FAILED", "error": str(exc)[:400]}
    finally:
        db.close()


def is_cad_file(filename: str) -> bool:
    return (filename or "").lower().endswith((".dxf", ".dwg"))
