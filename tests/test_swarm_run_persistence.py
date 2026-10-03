import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main_mod
from app.db.base import Base
from app.models.tender_models import ComplianceRecord, Tender


@pytest.fixture
def db_factory(monkeypatch):
    import app.models.audit_log, app.models.platform_models, app.models.tender_models  # noqa: F401

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(main_mod, "SessionLocal", factory)
    return factory


def _tender(factory):
    with factory() as db:
        t = Tender(title="T", client_name="C", status="processing")
        db.add(t)
        db.commit()
        return t.id


def test_failed_run_with_arabic_error_marks_tender_failed(db_factory, tmp_path):
    tid = _tender(db_factory)
    empty = tmp_path / "empty.txt"
    empty.write_text(" ")
    main_mod._run_swarm_audit(tid, [str(empty)], str(tmp_path / "x.xer"), "C")
    with db_factory() as db:
        t = db.get(Tender, tid)
        assert t.status == "failed"
        assert t.technical_score is None
        assert t.audit_metadata["error"]["type"] == "InsufficientInputError"


def test_successful_run_persists_clause_level_compliance_records(db_factory, rfp_file, xer_file):
    tid = _tender(db_factory)
    main_mod._run_swarm_audit(tid, [rfp_file], xer_file, "C")
    with db_factory() as db:
        t = db.get(Tender, tid)
        assert t.status == "completed" and t.technical_score is not None
        records = db.query(ComplianceRecord).filter_by(tender_id=tid).all()
        assert len(records) >= 1
        assert {r.status for r in records} <= {"Compliant", "Deviation", "Gap"}
