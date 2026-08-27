"""Tender Documents API â€” large-scale ingestion, triage, criteria pinning & RAG."""

import os
import shutil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.crypto_vault import decrypt
from app.db.session import SessionLocal, get_db
from app.models.platform_models import PackageDocument, PackageDocumentChunk, TenderRequirement
from app.parsers.criteria_extractor import extract_requirements
from app.parsers.document_classifier import rank_criteria_candidates

try:
    from qdrant_client import models as qdrant_models
except Exception:  # noqa: BLE001 — Qdrant اختياري في بيئات التطوير
    qdrant_models = None

router = APIRouter()

UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", os.path.join(os.getcwd(), "uploads"))
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".md", ".csv",
    ".dxf", ".dwg", ".rvt", ".ifc", ".zip", ".rar",
}
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB per file

from app.services.zip_extractor import extract_zip_to_docs, is_zip


def _doc_folder(tender_id: int) -> str:
    folder = os.path.join(UPLOAD_ROOT, f"tender_{tender_id}")
    os.makedirs(folder, exist_ok=True)
    return folder


def _serialize(doc: PackageDocument, text_sample: str = "") -> Dict[str, Any]:
    return {
        "id": doc.id,
        "tender_id": doc.tender_id,
        "filename": doc.filename,
        "size_bytes": doc.size_bytes,
        "file_ext": doc.file_ext,
        "doc_category": doc.doc_category,
        "classification_confidence": doc.classification_confidence,
        "status": doc.status,
        "process_error": doc.process_error,
        "page_count": doc.page_count,
        "text_chars": doc.text_chars,
        "ocr_used": doc.ocr_used,
        "chunk_count": doc.chunk_count,
        "is_pinned_criteria": doc.is_pinned_criteria,
        "uploaded_at": str(doc.uploaded_at or ""),
        "text_sample": text_sample[:600],
    }


# ------------------------------------------------------------- upload ---

ALLOWED_CATEGORIES = {
    "EVALUATION_CRITERIA", "SPECIFICATIONS", "BOQ", "DRAWINGS",
    "FORMS", "ADDENDUM", "CONTRACT", "PROPOSAL", "OTHER",
}


@router.post("/upload")
async def upload_document(
    tender_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    description: str = "",
    ocr_enabled: bool = False,
    doc_category: str = "",
    db: Session = Depends(get_db),
):
    """يحفظ الملف ويسجّله فوراً، ويؤجل المعالجة الثقيلة (استخراج/OCR/embedding) للخلفية.
    الرد يأتي خلال ثوانٍ — والعميل يتتبع الحالة عبر GET /documents (status=PROCESSING)."""
    filename = os.path.basename(file.filename or "document")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

    folder = _doc_folder(tender_id)
    safe_name = filename.replace(" ", "_")
    dest = os.path.join(folder, safe_name)

    size = 0
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            out.write(chunk)
            if size > MAX_FILE_BYTES:
                out.close()
                os.remove(dest)
                raise HTTPException(status_code=413, detail="File exceeds 2GB limit")

    # تجاوز يدوي للتصنيف (مثل زر «رفع العرض الفني» المخصص) — قبل إنشاء السجل
    force_category = doc_category.strip().upper() if doc_category.strip() else ""
    if force_category and force_category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"invalid doc_category: {force_category}")

    # ---- أرشيف ZIP: استخراج فوري واستيعاب المحتويات المفيدة ثم حذف الأرشيف ----
    if is_zip(filename):
        result = extract_zip_to_docs(dest, folder)
        if result["error"] and not result["accepted"]:
            raise HTTPException(status_code=422, detail=result["error"])

        from app.services.document_pipeline import process_document

        doc_ids: list = []
        for extracted_path in result["accepted"]:
            ex_name = os.path.basename(extracted_path)
            ex_ext = os.path.splitext(ex_name)[1].lower()
            ex_size = os.path.getsize(extracted_path)
            ex_doc = PackageDocument(
                tender_id=tender_id,
                filename=ex_name,
                rel_path=extracted_path,
                size_bytes=ex_size,
                file_ext=ex_ext,
                status="REGISTERED",
                doc_category=force_category or "UNCATEGORIZED",
                classification_confidence=1.0 if force_category else 0.0,
                classification_signals="zip_extract" if not force_category else "manual_override+zip",
            )
            db.add(ex_doc)
            db.commit()
            db.refresh(ex_doc)
            doc_ids.append(ex_doc.id)
            background_tasks.add_task(process_document, ex_doc.id, ocr_enabled, force_category)

        return {
            "document": None,
            "zip_extraction": {
                "accepted": len(result["accepted"]),
                "skipped": result["skipped"][:20],
                "document_ids": doc_ids,
                "note": "archive deleted after extraction — no storage duplication",
            },
            "description": description,
        }

    doc = PackageDocument(
        tender_id=tender_id,
        filename=filename,
        rel_path=dest,
        size_bytes=size,
        file_ext=ext,
        status="REGISTERED",
        doc_category=force_category or "UNCATEGORIZED",
        classification_confidence=1.0 if force_category else 0.0,
        classification_signals="manual_override" if force_category else "",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # المعالجة الثقيلة في الخلفية — الرفع لا ينتظرها
    from app.services.document_pipeline import process_document

    background_tasks.add_task(process_document, doc.id, ocr_enabled, force_category)

    return {
        "document": _serialize(doc),
        "processing": {"status": "QUEUED", "note": "processing continues in background — poll GET /documents"},
        "description": description,
    }


# -------------------------------------------------------- folder scan ---

@router.post("/scan-folder")
def scan_folder(body: Dict[str, str], db: Session = Depends(get_db)):
    """
    Server-side folder scan: registers every supported file found in the given
    folder (recursive) without copying â€” the pipeline reads them in place.
    """
    tender_id_raw = body.get("tender_id")
    folder = body.get("folder", "")
    if not tender_id_raw or not folder:
        raise HTTPException(status_code=422, detail="tender_id and folder are required")
    tender_id = int(tender_id_raw)
    if not os.path.isdir(folder):
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder}")

    registered = []
    skipped = []
    for root, _dirs, files in os.walk(folder):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                skipped.append(filename)
                continue
            full = os.path.join(root, filename)
            size = os.path.getsize(full)
            doc = PackageDocument(
                tender_id=tender_id,
                filename=filename,
                rel_path=full,
                size_bytes=size,
                file_ext=ext,
                status="REGISTERED",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            registered.append(doc.id)

    return {"registered": len(registered), "document_ids": registered, "skipped": skipped[:20]}


# ------------------------------------------------------------ inventory ---

@router.get("")
def list_documents(tender_id: int, db: Session = Depends(get_db)):
    docs = db.query(PackageDocument).filter(PackageDocument.tender_id == tender_id).order_by(PackageDocument.id).all()
    return {"documents": [_serialize(d) for d in docs], "count": len(docs)}


@router.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(PackageDocument).filter(PackageDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    sample = ""
    chunk = db.query(PackageDocumentChunk).filter(PackageDocumentChunk.document_id == doc.id).first()
    if chunk:
        sample = chunk.chunk_text
    return _serialize(doc, sample)


@router.post("/{document_id}/process")
def reprocess_document(document_id: int, ocr_enabled: bool = False, db: Session = Depends(get_db)):
    from app.services.document_pipeline import process_document

    doc = db.query(PackageDocument).filter(PackageDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    summary = process_document(document_id, ocr_enabled=ocr_enabled)
    db.refresh(doc)
    return {"document": _serialize(doc), "processing": summary}


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """حذف مستند نهائياً: الشرائح النصية، متجهات Qdrant، الملف على القرص، ثم سجل قاعدة البيانات."""
    doc = db.query(PackageDocument).filter(PackageDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1) الشرائح النصية
    deleted_chunks = (
        db.query(PackageDocumentChunk)
        .filter(PackageDocumentChunk.document_id == document_id)
        .delete()
    )

    # 2) متجهات Qdrant المرتبطة بالمستند (إن وُجدت المجموعة)
    vectors_deleted = False
    if qdrant_models is not None:
        try:
            from app.core.vector_store import get_global_client

            client = get_global_client()
            collection = f"tender_{doc.tender_id}_docs"
            if client.collection_exists(collection_name=collection):
                client.delete(
                    collection_name=collection,
                    points_selector=qdrant_models.FilterSelector(
                        filter=qdrant_models.Filter(
                            must=[
                                qdrant_models.FieldCondition(
                                    key="document_id",
                                    match=qdrant_models.MatchValue(value=document_id),
                                )
                            ]
                        )
                    ),
                )
                vectors_deleted = True
        except Exception:  # noqa: BLE001 — المتجهات اختيارية؛ الحذف يستمر بدونها
            pass

    # 3) الملف على القرص (فقط إن كان داخل UPLOAD_ROOT فعلياً — حماية من path traversal)
    file_removed = False
    rel_path = doc.rel_path or ""
    upload_root = os.path.realpath(UPLOAD_ROOT)
    if rel_path and os.path.isfile(rel_path):
        real = os.path.realpath(rel_path)
        # os.path.realpath + sep يمنع تجاوز الحماية بمجلدات مثل uploads_evil أو uploads-backup
        if real == upload_root or real.startswith(upload_root + os.sep):
            try:
                os.remove(real)
                file_removed = True
            except OSError:
                pass

    was_pinned = bool(doc.is_pinned_criteria)
    db.delete(doc)
    db.commit()

    return {
        "deleted": document_id,
        "deleted_chunks": deleted_chunks,
        "vectors_deleted": vectors_deleted,
        "file_removed": file_removed,
        "criteria_pin_cleared": was_pinned,
    }



# ------------------------------------------------------------- criteria ---

@router.get("/criteria/detect")
def detect_criteria(tender_id: int, db: Session = Depends(get_db)):
    """Rank documents by likelihood of being THE evaluation-criteria document."""
    docs = db.query(PackageDocument).filter(PackageDocument.tender_id == tender_id).all()
    candidates_input: List[Dict[str, Any]] = []
    for doc in docs:
        text_sample = ""
        chunk = (
            db.query(PackageDocumentChunk)
            .filter(PackageDocumentChunk.document_id == doc.id)
            .order_by(PackageDocumentChunk.chunk_index)
            .first()
        )
        if chunk:
            text_sample = chunk.chunk_text
        candidates_input.append({
            "id": doc.id,
            "filename": doc.filename,
            "doc_category": doc.doc_category,
            "classification_confidence": doc.classification_confidence,
            "text_sample": text_sample,
            "is_pinned_criteria": doc.is_pinned_criteria,
        })

    ranked = rank_criteria_candidates(candidates_input)
    return {
        "candidates": ranked[:8],
        "pinned": [c for c in ranked if c.get("is_pinned_criteria")],
    }


@router.post("/criteria/pin")
def pin_criteria(body: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Pin a document as THE binding evaluation-criteria source, then extract
    mandatory gates, weighted criteria and disqualification conditions.
    """
    tender_id = int(body.get("tender_id", 0))
    document_id = int(body.get("document_id", 0))
    if not tender_id or not document_id:
        raise HTTPException(status_code=422, detail="tender_id and document_id are required")

    doc = db.query(PackageDocument).filter(PackageDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Unpin previous criteria documents for this tender.
    for other in db.query(PackageDocument).filter(
        PackageDocument.tender_id == tender_id, PackageDocument.is_pinned_criteria.is_(True)
    ):
        other.is_pinned_criteria = False
    doc.is_pinned_criteria = True
    db.commit()

    # Gather full text from the pinned document's chunks.
    chunks = (
        db.query(PackageDocumentChunk)
        .filter(PackageDocumentChunk.document_id == document_id)
        .order_by(PackageDocumentChunk.chunk_index)
        .all()
    )
    full_text = "\n".join(c.chunk_text for c in chunks)
    if len(full_text.strip()) < 40:
        raise HTTPException(status_code=422, detail="Pinned document has no extractable text to analyze")

    requirements = extract_requirements(full_text, source_document_id=document_id)

    # Replace previous binding requirements for this tender.
    db.query(TenderRequirement).filter(TenderRequirement.tender_id == tender_id).delete()
    for req in requirements:
        db.add(TenderRequirement(
            tender_id=tender_id,
            source_document_id=document_id,
            requirement_type=req["requirement_type"],
            requirement_text=req["requirement_text"],
            weight=req.get("weight"),
            clause_ref=req.get("clause_ref", ""),
        ))
    db.commit()

    counts = {"MANDATORY": 0, "WEIGHTED": 0, "DISQUALIFICATION": 0}
    for req in requirements:
        counts[req["requirement_type"]] = counts.get(req["requirement_type"], 0) + 1

    return {
        "pinned_document": doc.filename,
        "requirements_extracted": len(requirements),
        "breakdown": counts,
        "requirements": requirements[:40],
    }


@router.get("/criteria/list")
def list_criteria(tender_id: int, db: Session = Depends(get_db)):
    requirements = (
        db.query(TenderRequirement)
        .filter(TenderRequirement.tender_id == tender_id)
        .order_by(TenderRequirement.requirement_type, TenderRequirement.id)
        .all()
    )
    return {
        "requirements": [
            {
                "id": r.id,
                "requirement_type": r.requirement_type,
                "requirement_text": r.requirement_text,
                "weight": r.weight,
                "clause_ref": r.clause_ref,
            }
            for r in requirements
        ],
        "count": len(requirements),
    }


# ----------------------------------------------------------------- RAG ---

@router.post("/ask")
def ask_corpus(body: Dict[str, Any], db: Session = Depends(get_db)):
    """
    RAG query over the ingested RFP corpus with mandatory citations
    (document filename + page). Vector search when embeddings are configured,
    keyword search over DB chunks otherwise.
    """
    tender_id = int(body.get("tender_id", 0))
    question = (body.get("question") or "").strip()
    top_k = int(body.get("top_k", 5))
    if not tender_id or not question:
        raise HTTPException(status_code=422, detail="tender_id and question are required")

    citations: List[Dict[str, Any]] = []

    # 1) Vector search when an embedding provider is available.
    try:
        from app.models.platform_models import LLMProvider
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        from app.core.llm_gateway_v2 import embed
        from app.core.vector_store import get_global_client

        db_prov = SessionLocal()
        provider = (
            db_prov.query(LLMProvider)
            .filter(LLMProvider.enabled.is_(True), LLMProvider.embedding_model.isnot(None),
                    LLMProvider.embedding_model != "")
            .first()
        )
        db_prov.close()

        if provider is not None:
            vector = embed(provider, question)
            if vector:
                client: QdrantClient = get_global_client()
                collection = f"tender_{tender_id}_docs"
                if client.collection_exists(collection_name=collection):
                    hits = client.search(
                        collection_name=collection,
                        query_vector=vector,
                        query_filter=Filter(must=[FieldCondition(key="tender_id_match", match=MatchValue(value=tender_id))]) if False else None,
                        limit=top_k,
                    )
                    docs_by_id = {
                        d.id: d for d in db.query(PackageDocument).filter(PackageDocument.tender_id == tender_id)
                    }
                    for hit in hits:
                        payload = hit.payload or {}
                        doc = docs_by_id.get(payload.get("document_id"))
                        citations.append({
                            "filename": doc.filename if doc else "unknown",
                            "page": payload.get("page", 0),
                            "text": (payload.get("text", "") or "")[:700],
                            "score": round(hit.score, 3),
                            "via": "vector",
                        })
    except Exception:  # noqa: BLE001
        citations = []

    # 2) Keyword fallback over DB chunks.
    if not citations:
        keywords = [w for w in question.split() if len(w) > 2][:8]
        chunk_query = db.query(PackageDocumentChunk).filter(PackageDocumentChunk.tender_id == tender_id)
        rows = chunk_query.all()
        scored = []
        for chunk in rows:
            lowered = (chunk.chunk_text or "").lower()
            score = sum(1 for kw in keywords if kw.lower() in lowered)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        docs_by_id = {d.id: d for d in db.query(PackageDocument).filter(PackageDocument.tender_id == tender_id)}
        for score, chunk in scored[:top_k]:
            doc = docs_by_id.get(chunk.document_id)
            citations.append({
                "filename": doc.filename if doc else "unknown",
                "page": chunk.page_number,
                "text": (chunk.chunk_text or "")[:700],
                "score": score,
                "via": "keyword",
            })

    return {"question": question, "citations": citations, "count": len(citations)}
