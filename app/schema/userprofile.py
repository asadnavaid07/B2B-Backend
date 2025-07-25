from pydantic import BaseModel,Field
from typing import Optional, Dict
from datetime import datetime, date



class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1)
    dob: date
    cnic_passport: str = Field(..., min_length=5)
    phone_number: str = Field(..., regex=r"^\+?1?\d{9,15}$")
    business_name: str = Field(..., min_length=1)
    business_type: str = Field(..., min_length=1)
    business_reg_number: str = Field(..., min_length=1)
    business_address: str = Field(..., min_length=1)
    business_phone: str = Field(..., regex=r"^\+?1?\d{9,15}$")
    website: Optional[str] = None
    socials: Optional[Dict[str, str]] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
    cnic_passport: Optional[str] = None
    phone_number: Optional[str] = Field(None, regex=r"^\+?1?\d{9,15}$")
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_reg_number: Optional[str] = None
    business_address: Optional[str] = None
    business_phone: Optional[str] = Field(None, regex=r"^\+?1?\d{9,15}$")
    website: Optional[str] = None
    socials: Optional[Dict[str, str]] = None

class UserProfileResponse(BaseModel):
    user_id: int
    name: str
    dob: date
    cnic_passport: str
    phone_number: str
    business_name: str
    business_type: str
    business_reg_number: str
    business_address: str
    business_phone: str
    website: Optional[str]
    socials: Optional[Dict[str, str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
