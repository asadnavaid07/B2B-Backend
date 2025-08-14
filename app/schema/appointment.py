from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from app.utils.appointment import get_available_dates, TIME_SLOTS_CONFIG


class AppointmentCreate(BaseModel):
    user_type: str = Field(..., pattern="^(buyer|vendor|guest)$")
    appointment_type: str = Field(..., pattern="^(virtual|offline)$")
    virtual_platform: Optional[str] = Field(None, pattern="^(Zoom|Google Meet|MS Teams)$")
    office_location: Optional[str] = Field(None, pattern="^(USA Office – HQ|Kashmir India)$")
    country: Optional[str] = Field(None, pattern="^(USA|India)$")  # For guests
    appointment_date: date
    appointment_time: time
    purpose: str = Field(..., max_length=255)

    @validator("virtual_platform")
    def validate_virtual_platform(cls, v, values):
        if "appointment_type" in values and values["appointment_type"] == "virtual" and not v:
            raise ValueError("Virtual platform is required for virtual appointments")
        if "appointment_type" in values and values["appointment_type"] == "offline" and v:
            raise ValueError("Virtual platform should not be provided for offline appointments")
        return v

    @validator("office_location")
    def validate_office_location(cls, v, values):
        if "appointment_type" in values and values["appointment_type"] == "offline" and not v:
            raise ValueError("Office location is required for offline appointments")
        if "appointment_type" in values and values["appointment_type"] == "virtual" and v:
            raise ValueError("Office location should not be provided for virtual appointments")
        return v

    @validator("country")
    def validate_country(cls, v, values):
        if "user_type" in values and values["user_type"] == "guest" and not v:
            raise ValueError("Country is required for guest users")
        if "user_type" in values and values["user_type"] != "guest" and v:
            raise ValueError("Country should only be provided for guest users")
        return v

    @validator("appointment_date")
    def validate_date(cls, v):
        available_dates = get_available_dates(date(2025, 8, 14))
        if v not in available_dates:
            raise ValueError(f"Invalid date. Available dates: {available_dates}")
        return v

    @validator("appointment_time")
    def validate_time(cls, v, values):
        if "user_type" not in values or "appointment_type" not in values:
            raise ValueError("User type and appointment type must be specified")
        user_type = values["user_type"]
        appointment_type = values["appointment_type"]
        office_location = values.get("office_location")
        country = values.get("country")

        if user_type == "guest":
            config = TIME_SLOTS_CONFIG[user_type][country or "USA"][appointment_type]
        else:
            config = TIME_SLOTS_CONFIG[user_type][appointment_type]
            if appointment_type == "offline":
                config = config[office_location]

        valid_times = config["times"]
        if v not in valid_times:
            raise ValueError(f"Invalid time for {user_type}/{appointment_type}. Available times: {valid_times}")
        values["time_zone"] = config["time_zone"]  # Store time zone for later use
        return v

class AppointmentResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_type: str
    appointment_type: str
    virtual_platform: Optional[str]
    office_location: Optional[str]
    appointment_date: date
    appointment_time: str
    time_zone: str
    purpose: str
    file_path: Optional[str]
    file_name: Optional[str]
    verification_status: str
    created_at: datetime

    class Config:
        orm_mode = True

class AvailableTimeResponse(BaseModel):
    date: date
    time_slots: List[str]
    time_zone: str
