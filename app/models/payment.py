from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum
from app.core.database import Base
from enum import Enum

class PaymentType(str, Enum):
    LATERAL = "LATERAL"
    MONTHLY = "MONTHLY"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DELINQUENT = "DELINQUENT"

class PaymentPlan(str, Enum):
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    ENTERPRISE = "ENTERPRISE"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    partnership_level = Column(String, nullable=False)
    plan = Column(String, nullable=False) 
    amount = Column(Float, nullable=False)
    payment_type = Column(SQLEnum(PaymentType), nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    stripe_payment_id = Column(String, nullable=True) 
    next_payment_due = Column(DateTime, nullable=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PaymentNotification(Base):
    __tablename__ = "payment_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    notification_type = Column(String, nullable=False)  # e.g., "PAYMENT_DUE", "PAYMENT_OVERDUE", "PAYMENT_SUCCESS"
    days_overdue = Column(Integer, nullable=True)
    message = Column(String, nullable=False)
    is_read = Column(String, default="false")  # Using string to match schema
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PartnershipDeactivation(Base):
    __tablename__ = "partnership_deactivations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    partnership_level = Column(String, nullable=False)
    deactivation_reason = Column(String, nullable=False)
    deactivated_at = Column(DateTime(timezone=True), server_default=func.now())
    reactivation_available = Column(String, default="true")  # Using string to match schema
    reactivated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())