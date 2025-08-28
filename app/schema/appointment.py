from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from app.utils.appointment import get_available_dates, TIME_SLOTS_CONFIG



class AppointmentCreate(BaseModel):
    user_id: Optional[int] = None
    user_type: str
    appointment_type: str
    virtual_platform: Optional[str] = None
    office_location: Optional[str] = None
    appointment_date: date
    appointment_time: str
    time_zone: str
    purpose: str
    first_name: str
    last_name: str
    business_name: str
    website: Optional[str] = None
    email: EmailStr
    phone_number: str

    @validator("office_location")
    def validate_office_location(cls, v, values):
        if "appointment_type" in values and values["appointment_type"] == "virtual" and v is not None:
            raise ValueError("Office location should not be provided for virtual appointments")
        if "appointment_type" in values and values["appointment_type"] == "offline" and v is None:
            raise ValueError("Office location is required for offline appointments")
        return v

    @validator("virtual_platform")
    def validate_virtual_platform(cls, v, values):
        if "appointment_type" in values and values["appointment_type"] == "virtual" and v is None:
            raise ValueError("Virtual platform is required for virtual appointments")
        if "appointment_type" in values and values["appointment_type"] != "virtual" and v is not None:
            raise ValueError("Virtual platform should not be provided for non-virtual appointments")
        return v

    @validator("time_zone")
    def validate_time_zone(cls, v):
        if v not in ["EST", "IST"]:
            raise ValueError("Time zone must be EST or IST")
        return v

    @validator("email")
    def validate_email(cls, v):
        if not v:
            raise ValueError("Email is required")
        return v

    @validator("phone_number")
    def validate_phone_number(cls, v):
        if not v:
            raise ValueError("Phone number is required")
        if len(v) > 20:
            raise ValueError("Phone number must be 20 characters or less")
        return v

class AppointmentResponse(BaseModel):
    id: int
    user_type: str
    first_name: str
    last_name: str
    business_name: str
    email: str
    appointment_type: str
    virtual_platform: Optional[str]
    office_location: Optional[str]
    appointment_date: date
    appointment_time: time
    time_zone: str
    purpose: str
    file_path: Optional[str]
    file_name: Optional[str]
    verification_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AvailableTimeResponse(BaseModel):
    date: date
    time_slots: List[str]
    time_zone: str


class AppointmentByDayResponseItem(BaseModel):
    appointment_type: str
    appointment_time: str
    time_zone: str
    user_type: str

    class Config:
        from_attributes = True
        json_encoders = {
            time: lambda v: v.strftime("%I:%M %p")
        }

class AppointmentByDayResponse(BaseModel):
    date: str
    appointments: List[AppointmentByDayResponseItem]

class AvailableTimeResponse(BaseModel):
    date: date
    time_slots: List[str]
    time_zone: str