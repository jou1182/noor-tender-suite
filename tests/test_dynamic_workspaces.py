"""
Tenders API — دورة الحياة الديناميكية (إنشاء/إعادة تسمية/حذف متسلسل/إطلاق السرب)
وثائق المكتبة — DELETE المتسلسل
غرفة تدريب الوكلاء — preview
"""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _cleanup_tender(client: TestClient, tender_id: int):
    client.delete(f"/api/v1/tenders/{tender_id}")


class TestTenderLifecycle:
    def test_create_list_rename_delete(self, client):
        # إنشاء
        res = client.post("/api/v1/tenders", json={"title": "T-TEST ديناميكي", "client_name": "عميل الاختبار"})
        assert res.status_code == 200, res.text
        created = res.json()
        tid = created["id"]
        try:
            assert created["title"] == "T-TEST ديناميكي"
            assert created["client_name"] == "عميل الاختبار"
            assert created["status"] == "draft"

            # يظهر في القائمة
            lst = client.get("/api/v1/tenders").json()
            ids = [t["id"] for t in lst["tenders"]]
            assert tid in ids

            # إعادة تسمية عبر PATCH
            res = client.patch(f"/api/v1/tenders/{tid}", json={"title": "T-TEST معدّل"})
            assert res.status_code == 200
            assert res.json()["title"] == "T-TEST معدّل"

            # GET فردي
            res = client.get(f"/api/v1/tenders/{tid}")
            assert res.status_code == 200
            assert res.json()["document_count"] == 0
        finally:
            _cleanup_tender(client, tid)

        # اختفى بعد الحذف
        assert client.get(f"/api/v1/tenders/{tid}").status_code == 404

    def test_create_requires_title(self, client):
        res = client.post("/api/v1/tenders", json={"title": "   "})
        assert res.status_code == 422

    def test_launch_requires_documents(self, client):
        res = client.post("/api/v1/tenders", json={"title": "T-LAUNCH"})
        tid = res.json()["id"]
        try:
            res = client.post(f"/api/v1/tenders/{tid}/launch")
            assert res.status_code == 422
            assert "RFP" in res.json()["detail"]
        finally:
            _cleanup_tender(client, tid)

    def test_launch_unknown_tender_404(self, client):
        assert client.post("/api/v1/tenders/999999/launch").status_code == 404

    def test_delete_missing_404(self, client):
        assert client.delete("/api/v1/tenders/999999").status_code == 404


class TestDocumentDelete:
    def test_document_delete_missing_404(self, client):
        assert client.delete("/api/v1/documents/999999").status_code == 404

    def test_upload_then_delete_cleans_everything(self, client, tmp_path):
        """رفع مستند صغير ثم حذفه يجب أن يمسح السجل والشرائح والملف من القرص."""
        pdf = tmp_path / "mini.pdf"
        pdf.write_bytes(b"%PDF-1.4 minimal test content for deletion pipeline")

        with open(pdf, "rb") as fh:
            res = client.post(
                "/api/v1/documents/upload?tender_id=1",
                files={"file": ("mini_test.pdf", fh, "application/pdf")},
            )
        if res.status_code != 200:
            pytest.skip(f"upload pipeline unavailable here: {res.status_code}")

        doc_id = res.json()["document"]["id"]
        rel_path = res.json()["document"].get("rel_path") or ""

        res = client.delete(f"/api/v1/documents/{doc_id}")
        assert res.status_code == 200
        payload = res.json()
        assert payload["deleted"] == doc_id
        # الملف كان تحت UPLOAD_ROOT فيجب أن يُمسح فعلياً
        if rel_path and "uploads" in rel_path:
            assert payload["file_removed"] is True
            assert not os.path.isfile(rel_path)

        # السجل لم يعد موجوداً
        assert client.get(f"/api/v1/documents/{doc_id}").status_code == 404


class TestAgentPreview:
    def test_preview_unknown_agent_404(self, client):
        res = client.post("/api/v1/agents/__nope__/preview", json={"draft": {}})
        assert res.status_code == 404

    def test_preview_without_enabled_provider_is_actionable_409(self, client):
        """يجب أن يكون رفض المعاينة واضحاً وقابلاً للإصلاح من الواجهة (وليس 500 صامتة)."""
        from app.db.session import SessionLocal
        from app.models.platform_models import LLMProvider

        db = SessionLocal()
        enabled = db.query(LLMProvider).filter(LLMProvider.enabled.is_(True)).all()
        states = [(p.id, p.enabled) for p in enabled]
        for pid, _ in states:
            db.query(LLMProvider).filter(LLMProvider.id == pid).update({"enabled": False})
        db.commit()
        db.close()
        try:
            res = client.post("/api/v1/agents/client_rfp/preview",
                              json={"draft": {}, "message": "من أنت؟"})
            assert res.status_code == 409
            assert "مزوّد" in res.json()["detail"]
        finally:
            if states:
                db = SessionLocal()
                for pid, was in states:
                    db.query(LLMProvider).filter(LLMProvider.id == pid).update({"enabled": was})
                db.commit()
                db.close()

    def test_agent_update_accepts_english_and_arabic_names(self, client):
        """الاسم الإنجليزي ليس صلباً — قابل للتعديل مثل العربي تماماً."""
        res = client.put("/api/v1/agents/client_rfp", json={"name_en": "Aria X"})
        assert res.status_code == 200
        agents = client.get("/api/v1/agents").json()["agents"]
        aria = next(a for a in agents if a["key"] == "client_rfp")
        assert aria["name_en"] == "Aria X"
        # إرجاع الأصل
        client.put("/api/v1/agents/client_rfp", json={"name_en": "Aria"})


class TestDynamicWorkspaceContract:
    def test_no_static_tenants_in_header_source(self):
        """القائمة العلوية لا تحتفظ بعملاء ثابتين في الكود — يجب أن تبقى ديناميكية."""
        header_src = os.path.join(
            os.path.dirname(__file__), "..", "frontend", "src", "components", "DashboardHeader.tsx"
        )
        with open(header_src, encoding="utf-8") as fh:
            src = fh.read()
        for banned in ["Saudi Aramco", "ROSHN", "Qiddiya", "Red Sea Global"]:
            assert banned not in src, f"static tenant leaked back into the header: {banned}"
