from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
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

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    partnership_level = Column(String, nullable=False)
    plan = Column(String, nullable=False) 
    amount = Column(Float, nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    stripe_payment_id = Column(String, nullable=True) 
    next_payment_due = Column(DateTime, nullable=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())