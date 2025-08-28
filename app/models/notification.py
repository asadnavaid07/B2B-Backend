from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, ForeignKey,Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum

class NotificationTargetType(str, Enum):
    ALL_USERS = "ALL_USERS"
    BUYERS = "BUYERS"
    VENDORS = "VENDORS"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_id = Column(Integer, nullable=True)
    message = Column(String(500), nullable=False)
    target_type = Column(SQLEnum(NotificationTargetType), nullable=False)
    visibility = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())