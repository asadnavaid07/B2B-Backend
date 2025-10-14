from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.registration import PartnershipLevel
import enum
from datetime import datetime

class PaymentType(enum.Enum):
    LATERAL = "lateral"
    MONTHLY = "monthly"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentPlan(enum.Enum):
    FIRST = "1st"
    SECOND = "2nd"
    THIRD = "3rd"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    partnership_level = Column(Enum(PartnershipLevel), nullable=False)
    plan = Column(Enum(PaymentPlan), nullable=False)
    amount = Column(Float, nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    stripe_payment_id = Column(String(255), nullable=True)  # For Stripe payment intent or subscription ID
    stripe_customer_id = Column(String(255), nullable=True)  # For Stripe customer ID
    next_payment_due = Column(DateTime(timezone=True), nullable=True)  # For monthly payments
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="payments")

class PaymentNotification(Base):
    __tablename__ = "payment_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # "7_days", "14_days", "21_days", "30_days_deactivation"
    days_overdue = Column(Integer, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User")
    payment = relationship("Payment")

class PartnershipDeactivation(Base):
    __tablename__ = "partnership_deactivations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    partnership_level = Column(Enum(PartnershipLevel), nullable=False)
    deactivation_reason = Column(String(255), nullable=False, default="Non-payment after 30 days")
    deactivated_at = Column(DateTime(timezone=True), server_default=func.now())
    reactivation_available = Column(Boolean, default=True)
    reactivated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User")