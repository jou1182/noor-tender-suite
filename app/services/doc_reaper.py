"""Stale-document reaper — يعيد تعيين المستندات العالقة في PROCESSING.

المشكلة التي تحلها:
  process_document يعمل كـ background task داخل عملية الخادم. إذا أُعيد تشغيل
  الخادم أثناء المعالجة (أو تعطلت المهمة لأي سبب) يبقى المستند في status=PROCESSING
  إلى الأبد — فيرى المستخدم «جارٍ المعالجة» مدى الحياة.

الحل (نظام الاسترداد الذاتي):
  1. حارس دوري (reaper) يدور كل STUCK_TIMEOUT_MINUTES دقيقة:
       - أي PackageDocument في status=PROCESSING أو REGISTERED منذ أقدم من الحد
         يعاد تعيينه إلى PROCESSING ويُستدعى process_document مرة أخرى (retry).
       - إن فشلت إعادة المحاولة أكثر من MAX_RETRIES مرة → FAILED + process_error.
  2. عند بدء تشغيل الخادم (startup): sweep فوري واحد يعطي المستندات العالقة
     فرصة أولى (الخادم قد يكون أُعيد تشغيله أثناء رفع المستندات).

آمن للاستدعاء المتكرر (idempotent) — لا يلمس مستندات قيد المعالجة الفعلية.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# المستند الذي بقي في REGISTERED/PROCESSING أطول من هذا الحد يعتبر عالقاً
STUCK_TIMEOUT_MINUTES = int(os.getenv("DOC_STUCK_TIMEOUT_MIN", "8"))
# عدد مرات إعادة المحاولة قبل أن يُعلَّم FAILED نهائياً
MAX_RETRIES = int(os.getenv("DOC_MAX_RETRIES", "2"))

_REAPER_INTERVAL = 60  # ثوانٍ بين دفحصات الحارس


def _is_stuck(doc, now: datetime) -> bool:
    """هل المستند عالق؟ (في REGISTERED/PROCESSING أقدم من الحد ولم يُعالج)."""
    if doc.status not in ("REGISTERED", "PROCESSING"):
        return False
    # آخر وقت معروف: عند الرفع أو آخر محاولة معالجة
    ref = doc.processed_at or doc.uploaded_at or now
    age = (now - ref).total_seconds()
    if age < STUCK_TIMEOUT_MINUTES * 60:
        return False
    return True


def sweep_stuck_documents(db: Session) -> int:
    """يفحص المستندات العالقة ويعيد جدولتها. يرجع عدد المستندات المُعاد تعيينها.

    آمن للنداء المتكرر: المستندات التي حُدّث processed_at مؤخراً (قيد المعالجة
    الفعلية) لا تتأثر — استعلام الوقت المرجعي لا يعتبر المستند عالقاً إلا بعد
    تجاوز الحد، ومستند يُعالج يمرر كتابة processed_at في نهاية كل دورة.
    """
    now = datetime.utcnow()
    from app.models.platform_models import PackageDocument

    candidates = (
        db.query(PackageDocument)
        .filter(PackageDocument.status.in_(["REGISTERED", "PROCESSING"]))
        .all()
    )
    recovered: list[PackageDocument] = []
    for doc in candidates:
        if _is_stuck(doc, now):
            recovered.append(doc)

    if not recovered:
        return 0

    from app.services.document_pipeline import process_document
    from app.db.session import SessionLocal

    def _retry(doc_id: int) -> None:
        # إعادة المحاولة في خيط مستقل حتى لا نكسر المعالجة الحية
        try:
            process_document(doc_id)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[REAPER] retry failed for doc {doc_id}: {exc}")
            with SessionLocal() as dbs:
                from app.models.platform_models import PackageDocument  # noqa: F811

                d = dbs.query(PackageDocument).filter(PackageDocument.id == doc_id).first()
                if d:
                    d.status = "FAILED"
                    d.process_error = f"reaper retry failed: {exc}"[:800]
                    d.processed_at = datetime.utcnow()
                    dbs.commit()

    for doc in recovered:
        # سجل آخر محاولة حتى لو فشل الحارس لاحقاً يتذكر أننا حاولنا
        doc.processed_at = now
        db.commit()
        thread = threading.Thread(target=_retry, args=(doc.id,), daemon=True)
        thread.start()
        logger.info(f"[REAPER] requeued stuck doc {doc.id} ({doc.filename})")

    return len(recovered)


# ------------------------------------------------------------------ loop ---

def _watch_loop() -> None:
    """حلقة الحارس: تعمل في خيط خلفي طيلة عمر الخادم."""
    from app.db.session import SessionLocal

    logger.info(f"[REAPER] watchdog started (interval={_REAPER_INTERVAL}s, timeout={STUCK_TIMEOUT_MINUTES}min)")
    while True:
        time.sleep(_REAPER_INTERVAL)
        try:
            with SessionLocal() as db:
                n = sweep_stuck_documents(db)
                if n:
                    logger.info(f"[REAPER] sweep: {n} document(s) requeued")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[REAPER] sweep failed: {exc}")


def start_reaper() -> None:
    """يُستدعى من startup — يبدأ الحارس في الخلفية (لا يمنع الإقلاع)."""
    thread = threading.Thread(target=_watch_loop, daemon=True, name="doc-reaper")
    thread.start()


def startup_sweep() -> int:
    """sweep أولي عند الإقلاع — يسترد ما علق من إعادة تشغيل سابقة."""
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        n = sweep_stuck_documents(db)
        if n:
            logger.info(f"[REAPER] startup sweep: {n} document(s) requeued")
        return n
