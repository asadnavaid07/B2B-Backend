from sqlalchemy import Column, Float, Integer, String, Boolean, Enum, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum
from enum import Enum as PyEnum

class RegistrationStatus(PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class UserRole(str, enum.Enum):
    vendor = "vendor"
    buyer = "buyer"
    super_admin = "super_admin"
    sub_admin = "sub_admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=False)
    visibility_level = Column(Integer, default=1)  
    ownership = Column(JSON, nullable=True)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    google_id = Column(String, unique=True, nullable=True) 
    kpi_score = Column(Float, default=0.0)
    partnership_level = Column(String, default="DROP_SHIPPING")
    retention_period = Column(String, default="None")
    retention_start_date = Column(DateTime, nullable=True) 
    is_registered = Column(Enum(RegistrationStatus), nullable=False, default=RegistrationStatus.PENDING)
    registration_step = Column(Integer, nullable=False, default=1)
    is_lateral=Column(Boolean, default=False)
    first_register=Column(Boolean, default=False)
    payment_status=Column(Boolean, default=False)
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
   