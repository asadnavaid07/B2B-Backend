from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import enum
from typing import Optional

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

class DocumentCreate(BaseModel):
    document_type: DocumentType
    file_path: str  # Will be populated after file upload

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    document_type: DocumentType
    file_path: str
    uploaded_at: datetime
    ai_verification_status: VerificationStatus
    ai_kpi_score: Optional[float]
    ai_remarks: Optional[str]

    class Config:
        from_attributes = True