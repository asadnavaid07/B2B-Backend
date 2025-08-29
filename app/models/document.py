from sqlalchemy import Column, ForeignKey, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum as PyEnum
from sqlalchemy.orm import relationship
from app.schema.document import VerificationStatus

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=True)
    ai_verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    ai_kpi_score = Column(Integer, default=0)
    ai_remarks = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="documents")