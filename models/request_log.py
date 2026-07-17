from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String(255), nullable=False, index=True)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
