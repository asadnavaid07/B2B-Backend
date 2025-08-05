from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)  # Removed unique=True
    otp_code = Column(String(6), nullable=False)
    __table_args__ = (
        CheckConstraint("otp_code ~ '^[0-9]{6}$'", name="valid_otp_code"),
    )