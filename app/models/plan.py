from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey,Text,JSON,Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class PlanStatus(str, enum.Enum):
    PENDING_PAYMENT = "PendingPayment"
    PAYMENT_VERIFIED = "PaymentVerified"
    PENDING_AI_VERIFICATION = "PendingAIVerification"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class PlanStatus(str, enum.Enum):
    PENDING_PAYMENT = "PendingPayment"
    PAYMENT_VERIFIED = "PaymentVerified"
    REJECTED = "Rejected"
    ACTIVE = "Active"

class UserPlan(Base):
    __tablename__ = "user_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(Enum(PlanStatus), default=PlanStatus.PENDING_PAYMENT)
    retention_progress = Column(Float, nullable=True)


    user = relationship("User", back_populates="user_plans")
    plan = relationship("Plan")

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    level = Column(Integer, nullable=False)