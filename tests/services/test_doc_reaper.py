"""Tests for the stale-document reaper (self-healing of PROCESSING deadlock)."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.models.platform_models import PackageDocument
from app.services.doc_reaper import _is_stuck, MAX_RETRIES, STUCK_TIMEOUT_MINUTES


def _doc(status: str, age_minutes: float, success: bool = True) -> PackageDocument:
    now = datetime.utcnow()
    doc = PackageDocument(
        id=1,
        tender_id=1,
        filename="test.pdf",
        rel_path="uploads/1/test.pdf",
        status=status,
        doc_category="UNCATEGORIZED",
    )
    doc.uploaded_at = now - timedelta(minutes=age_minutes)
    doc.processed_at = now - timedelta(minutes=age_minutes)
    return doc


class TestIsStuck:
    def test_fresh_registered_not_stuck(self):
        assert not _is_stuck(_doc("REGISTERED", 1), datetime.utcnow())

    def test_fresh_processing_not_stuck(self):
        assert not _is_stuck(_doc("PROCESSING", 1), datetime.utcnow())

    def test_stale_processing_is_stuck(self):
        assert _is_stuck(_doc("PROCESSING", STUCK_TIMEOUT_MINUTES + 5), datetime.utcnow())

    def test_stale_registered_is_stuck(self):
        assert _is_stuck(_doc("REGISTERED", STUCK_TIMEOUT_MINUTES + 5), datetime.utcnow())

    def test_processed_never_stuck(self):
        assert not _is_stuck(_doc("PROCESSED", STUCK_TIMEOUT_MINUTES * 10), datetime.utcnow())

    def test_failed_never_stuck(self):
        assert not _is_stuck(_doc("FAILED", STUCK_TIMEOUT_MINUTES * 10), datetime.utcnow())


class TestSweep:
    def test_sweep_requeues_stale_only(self):
        """فقط المستندات العالقة تُعاد جدولتها — السليمة تبقى بلا لمس."""
        stale = PackageDocument(status="PROCESSING", filename="stale.pdf")
        stale.uploaded_at = datetime.utcnow() - timedelta(minutes=STUCK_TIMEOUT_MINUTES * 2)
        stale.processed_at = stale.uploaded_at

        fresh = PackageDocument(status="PROCESSING", filename="fresh.pdf")
        fresh.uploaded_at = datetime.utcnow()
        fresh.processed_at = None
        # fresh: processed_at None -> uses uploaded_at (now) -> not stuck

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [stale, fresh]

        with patch("app.services.doc_reaper.threading.Thread") as mock_thread:
            with patch("app.services.document_pipeline.process_document") as mock_process:
                n = None
                # استيراد المودول مباشرة لتجنب إعادة الاستيراد
                import app.services.doc_reaper as reaper

                # استبدل thread.start بنسخة لا تعمل فعلياً — فقط نتحقق من التوزيع الصحيح
                mock_thread.return_value.start.return_value = None
                n = reaper.sweep_stuck_documents(db)

        # فقط المستند العالق يُعاد جدولته
        assert n == 1
        assert mock_thread.call_count == 1

    def test_sweep_noop_when_nothing_stuck(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        import app.services.doc_reaper as reaper

        assert reaper.sweep_stuck_documents(db) == 0

    def test_sweep_updates_processed_at_to_future(self):
        """المستند المعاد جدولته يجب أن يُحدَّث processed_at حتى لا يُلتقط
        في دورة الحارس التالية قبل انتهاء محاولة إعادة المعالجة."""
        stale = PackageDocument(status="PROCESSING", filename="stale.pdf")
        stale.uploaded_at = datetime.utcnow() - timedelta(minutes=STUCK_TIMEOUT_MINUTES * 3)
        stale.processed_at = stale.uploaded_at

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [stale]

        import app.services.doc_reaper as reaper

        with patch("app.services.doc_reaper.threading.Thread"):
            with patch("app.services.document_pipeline.process_document"):
                reaper.sweep_stuck_documents(db)

        # processed_at أُحدّث إلى الآن تقريباً — المستند لم يعد "عالقاً" في النافذة
        assert (datetime.utcnow() - stale.processed_at).total_seconds() < 5
        assert db.commit.called

    def test_max_retries_constant_sane(self):
        assert 0 < MAX_RETRIES <= 10
