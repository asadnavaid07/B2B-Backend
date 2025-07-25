from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Literal, Dict
from datetime import datetime, date
import enum




class PlanStatus(str, enum.Enum):
    PENDING_PAYMENT = "PendingPayment"
    PAYMENT_VERIFIED = "PaymentVerified"
    PENDING_AI_VERIFICATION = "PendingAIVerification"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class PlanCreate(BaseModel):
    level: int = Field(..., ge=1, le=8)
    name: str = Field(..., min_length=1)
    price_usd: Optional[float] = None
    description: Optional[str] = None

class PlanResponse(BaseModel):
    id: int
    level: int
    name: str
    price_usd: Optional[float]
    description: Optional[str]

    class Config:
        from_attributes = True


class UserPlanCreate(BaseModel):
    plan_id: int

class UserPlanResponse(BaseModel):
    user_id: int
    plan_id: int
    status: PlanStatus
    retention_start_date: Optional[datetime]
    retention_progress: Optional[float]
    created_at: datetime
    updated_at: datetime
    plan: PlanResponse

    class Config:
        from_attributes = True