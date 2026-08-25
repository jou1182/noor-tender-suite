from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, index=True, nullable=True)
    user_id = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    agent_name = Column(String, nullable=True)
    payload_hash = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
