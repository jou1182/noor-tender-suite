import unittest
import multiprocessing.pool
import time
import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.tender_models import Tender
from app.core.security import create_access_token

from app.db.session import engine, SessionLocal

class TestStressPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        for i in range(10):
            t = db.query(Tender).filter(Tender.id == 100 + i).first()
            if not t:
                t = Tender(id=100 + i, title=f"Stress Test Tender {i}", client_name="Stress Client", status="draft")
                db.add(t)
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        db = SessionLocal()
        for i in range(10):
            db.query(Tender).filter(Tender.id == 100 + i).delete()
        db.commit()
        db.close()
        
    def setUp(self):
        self.client = TestClient(app)
        self.token = create_access_token(subject="stress_tester", role="lead_architect")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        os.makedirs("sample_data", exist_ok=True)
        self.rfp_path = "sample_data/stress_rfp.pdf"
        self.xer_path = "sample_data/stress_schedule.xer"
        with open(self.rfp_path, "w") as f:
            f.write("DUMMY RFP DATA FOR STRESS TESTING")
        with open(self.xer_path, "w") as f:
            f.write("DUMMY XER DATA FOR STRESS TESTING")

    def test_concurrent_tender_uploads(self):
        """Simulates 10 concurrent tender submissions to ensure background workers don't lock and response time is minimal."""
        def submit_tender(task_id):
            client = TestClient(app)
            start_time = time.time()
            with open(self.rfp_path, "rb") as rfp, open(self.xer_path, "rb") as xer:
                response = client.post(
                    f"/api/v1/audits/{100 + task_id}/trigger",
                    headers=self.headers,
                    files=[
                        ("rfp_files", ("stress_rfp.pdf", rfp, "application/pdf")),
                        ("schedule_file", ("stress_schedule.xer", xer, "application/octet-stream"))
                    ]
                )
            duration = time.time() - start_time
            return response.status_code, duration

        pool = multiprocessing.pool.ThreadPool(processes=10)
        results = pool.map(submit_tender, range(10))
        pool.close()
        pool.join()
        
        for status_code, duration in results:
            self.assertEqual(status_code, 200, f"Expected 200, got {status_code}")
            self.assertLess(duration, 5.0, "API response exceeded 5 second SLA")

if __name__ == '__main__':
    unittest.main()
