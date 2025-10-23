from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from app.models.payment import PaymentType, PaymentStatus, PaymentPlan
from app.models.registration import PartnershipLevel

class PaymentRequest(BaseModel):
    partnership_level: PartnershipLevel
    plan: PaymentPlan
    payment_type: PaymentType

class PaymentResponse(BaseModel):
    payment_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    subscription_id: Optional[str] = None
    amount: float
    currency: str = "usd"
    status: str

class SubscriptionResponse(BaseModel):
    subscription_id: str
    client_secret: Optional[str] = None
    amount: float
    currency: str = "usd"
    next_payment_due: datetime

class PaymentWebhook(BaseModel):
    id: str
    object: str
    type: str
    data: Dict

class PaymentHistoryResponse(BaseModel):
    id: int
    partnership_level: str
    plan: str
    amount: float
    payment_type: str
    payment_status: str
    created_at: datetime
    next_payment_due: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaymentNotificationResponse(BaseModel):
    id: int
    notification_type: str
    days_overdue: int
    sent_at: datetime
    is_read: bool
    message: str

    class Config:
        from_attributes = True

class PartnershipDeactivationResponse(BaseModel):
    id: int
    partnership_level: str
    deactivation_reason: str
    deactivated_at: datetime
    reactivation_available: bool
    reactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaymentAnalyticsResponse(BaseModel):
    total_payments: int
    successful_payments: int
    failed_payments: int
    total_revenue: float
    monthly_recurring_revenue: float
    overdue_payments: int
    deactivated_partnerships: int
    payment_success_rate: float

# ThreeTierPricing schemas removed - use partnership-level schemas instead
# Use PartnershipLevelCreate, PartnershipLevelUpdate, PartnershipLevelResponse from partnership_level.py
