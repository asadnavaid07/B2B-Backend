from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey,Text,JSON,Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class DocumentType(str, enum.Enum):
    CNIC = "CNIC"
    UTILITY_BILL = "UtilityBill"
    BUSINESS_LICENSE = "BusinessLicense"
    OTHER = "Other"

class VerificationStatus(str, enum.Enum):
    PENDING = "Pending"
    PASS = "Pass"
    FAIL = "Fail"
    AWAITING_ADDITIONAL = "AwaitingAdditional"


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    ai_verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    ai_kpi_score = Column(Float, nullable=True)
    ai_remarks = Column(Text, nullable=True)
    user = relationship("User", back_populates="documents")