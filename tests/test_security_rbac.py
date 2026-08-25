import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.tender_models import Tender

from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///:memory:", 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# NOTE: كان يُسجَّل على مستوى الموديول ولا يُزال أبداً — فيلوّث كل اختبارات
# الحزمة اللاحقة (تظهر أخطاء "no such table: tenders"). نستخدم fixture بدلاً منه.
_app = app


class TestSecurityRBAC(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        _app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(_app)
        db = TestingSessionLocal()
        t = Tender(id=1, title="Test Tender", client_name="Test", status="draft")
        db.add(t)
        db.commit()
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=engine)
        # إزالة التجاوز حتى لا يتسرب إلى بقية اختبارات الحزمة
        _app.dependency_overrides.pop(get_db, None)

    def test_no_token_rejected(self):
        response = self.client.post("/api/v1/audits/1/trigger", files={"rfp_files": ("test.pdf", b"test"), "schedule_file": ("test.xer", b"test")})
        self.assertEqual(response.status_code, 401)

    def test_invalid_role_rejected(self):
        token = create_access_token(subject="user1", role="guest")
        response = self.client.post(
            "/api/v1/audits/1/trigger",
            headers={"Authorization": f"Bearer {token}"},
            files={"rfp_files": ("test.pdf", b"test"), "schedule_file": ("test.xer", b"test")}
        )
        self.assertEqual(response.status_code, 403)

    def test_valid_role_accepted_and_audit_logged(self):
        token = create_access_token(subject="user2", role="lead_architect")
        response = self.client.post(
            "/api/v1/audits/1/trigger",
            headers={"Authorization": f"Bearer {token}"},
            files=[("rfp_files", ("test.pdf", b"test"))],
            data={"schedule_file": ("test.xer", b"test")} # wait, FastAPI File needs form
        )
        
        # TestClient multi-file format:
        response = self.client.post(
            "/api/v1/audits/1/trigger",
            headers={"Authorization": f"Bearer {token}"},
            files=[
                ("rfp_files", ("test.pdf", b"test", "application/pdf")),
                ("schedule_file", ("test.xer", b"test", "application/octet-stream"))
            ]
        )
        
        self.assertEqual(response.status_code, 200)

        db = TestingSessionLocal()
        log = db.query(AuditLog).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user_id, "user2")
        self.assertEqual(log.action, "TRIGGER_AUDIT")
        db.close()

if __name__ == "__main__":
    unittest.main()
