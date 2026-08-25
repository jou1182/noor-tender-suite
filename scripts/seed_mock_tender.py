import os
import sys
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.tender_models import Tender

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    tender = db.query(Tender).filter(Tender.id == 1).first()
    if not tender:
        tender = Tender(title="Infrastructure Mega Project Live", client_name="Gov Dept", status="draft")
        db.add(tender)
        db.commit()
    elif tender.status != "draft":
        # Reset for test
        tender.status = "draft"
        tender.technical_score = None
        db.commit()
        
    db.close()
    print("Database seeded with Tender ID 1")

def create_dummy_files():
    os.makedirs("sample_data", exist_ok=True)
    rfp_path = "sample_data/RFP_Document.pdf"
    schedule_path = "sample_data/Schedule.xer"
    
    with open(rfp_path, "w") as f:
        f.write("Dummy RFP PDF content for tender compliance")
        
    with open(schedule_path, "w") as f:
        f.write("%T\tTASK\n%F\ttask_id\ttask_name\n%R\t1\tDesign\n%R\t2\tBuild\n%T\tTASKPRED\n%F\tpred_task_id\tsucc_task_id\n%R\t1\t2")
        
    print("Dummy test files created in sample_data/")

if __name__ == "__main__":
    seed_db()
    create_dummy_files()
    print("\nSetup complete! You can run the backend using:")
    print("uvicorn app.main:app --port 8000")
    print("And the frontend using:")
    print("cd frontend && npm run dev")
