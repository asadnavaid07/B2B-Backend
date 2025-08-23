from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    location = Column(String, nullable=False)
    type = Column(String, nullable=False)  # e.g., full-time, part-time, remote
    summary = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    salary_range = Column(String, nullable=True)
    application_deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=False)