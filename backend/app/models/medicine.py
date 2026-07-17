from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from ..database import Base

class MedicineRecord(Base):
    __tablename__ = "medicine_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    batch = Column(String, index=True, nullable=True)
    manufacturer = Column(String, nullable=True)
    status = Column(String, nullable=False, default="unsafe")
    authority = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
