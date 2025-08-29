from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import enum
from typing import Optional



class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    PASS = "Pass"
    FAIL = "Fail"
    AWAITING_ADDITIONAL = "AwaitingAdditional"



class DocumentResponse(BaseModel):
    id: int
    user_id: int
    document_type: str
    ai_verification_status: VerificationStatus


    class Config:
        from_attributes = True


class DocumentReuploadRequest(BaseModel):
    document_id: int
    file_url: str

class DocumentApproveRequest(BaseModel):
    document_id: int
    approve: bool
