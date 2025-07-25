from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

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
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=False)
    visibility_level = Column(Integer, default=1)  # 1-5 for sub_admin access level
    ownership = Column(JSON, nullable=True)  # JSON for resources/scopes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    user_plans = relationship("UserPlan", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    name = Column(String, nullable=False)
    dob = Column(DateTime, nullable=False)
    cnic_passport = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    business_reg_number = Column(String, nullable=False)
    business_address = Column(Text, nullable=False)
    business_phone = Column(String, nullable=False)
    website = Column(String, nullable=True)
    socials = Column(JSON, nullable=True)
    user = relationship("User", back_populates="profile")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)