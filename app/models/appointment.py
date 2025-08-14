from sqlalchemy import Column, Integer, String, Enum, Date, Time, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM
from app.core.database import Base
import enum

class UserType(str, enum.Enum):
    BUYER = "buyer"
    VENDOR = "vendor"
    GUEST = "guest"

class AppointmentType(str, enum.Enum):
    VIRTUAL = "virtual"
    OFFLINE = "offline"

class VirtualPlatform(str, enum.Enum):
    ZOOM = "Zoom"
    GOOGLE_MEET = "Google Meet"
    MS_TEAMS = "MS Teams"

class OfficeLocation(str, enum.Enum):
    USA = "USA Office – HQ"
    INDIA = "Kashmir India"

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for guests
    user_type = Column(Enum(UserType), nullable=False)
    appointment_type = Column(Enum(AppointmentType), nullable=False)
    virtual_platform = Column(Enum(VirtualPlatform), nullable=True)  # Required for virtual
    office_location = Column(Enum(OfficeLocation), nullable=True)  # Required for offline
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)  # Stored in UTC
    time_zone = Column(String(10), nullable=False)  # EST or IST
    purpose = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # Optional file
    file_name = Column(String(255), nullable=True)
    verification_status = Column(
        ENUM("PASS", "FAIL", "AWAITINGADDITIONAL", "PENDING", name="VerificationStatus"),
        default="PENDING"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())