from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional, Dict, List
from app.models.user import UserRole


class UserRole(str, Enum):
    vendor = "vendor"
    buyer = "buyer"
    super_admin = "super_admin"
    sub_admin = "sub_admin"

class ResendOTPRequest(BaseModel):
    email: str

class GoogleLoginRequest(BaseModel):
    id_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
def get_buyer_role() -> UserRole:
    return UserRole.buyer

def get_vendor_role() -> UserRole:
    return UserRole.vendor

def get_super_admin_role() -> UserRole:
    return UserRole.super_admin

def get_sub_admin_role() -> UserRole:
    return UserRole.sub_admin




class PlanStatus(str, Enum):
    PENDING_PAYMENT = "PendingPayment"
    PAYMENT_VERIFIED = "PaymentVerified"
    REJECTED = "Rejected"
    ACTIVE = "Active"

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str

class SubAdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    visibility_level: int = Field(..., ge=1, le=5, description="Access level 1-5")
    ownership: Optional[Dict[str, List[str]]] = None  # e.g., {"modules": ["users", "documents"]}

class SubAdminUpdate(BaseModel):
    visibility_level: Optional[int] = Field(None, ge=1, le=5, description="Access level 1-5")
    ownership: Optional[Dict[str, List[str]]] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    user_role: str
    user_id: int
    visibility_level: Optional[int] = None
    ownership: Optional[Dict[str, List[str]]] = None
    is_registered: Optional[str] = "PENDING"
    registration_step: Optional[int] = 0


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    visibility_level: Optional[int] = None
    ownership: Optional[Dict[str, List[str]]] = None
    is_registered: Optional[str] = "PENDING"
    registration_step: Optional[int] = 0


    class Config:
        orm_mode = True

class UserDashboardResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    visibility_level: Optional[int] = None
    ownership: Optional[Dict[str, List[str]]] = None
    kpi_score: Optional[float] = None         
    partnership_level: Optional[str] = None  
    retention_period: Optional[str] = None 

    class Config:
        orm_mode = True


class SubAdminResponse(BaseModel):
    username: str
    email: str
    password: str
    visibility_level: int
    ownership: Dict[str, List[str]]

class PlanResponse(BaseModel):
    id: int
    name: str
    level: int

    class Config:
        orm_mode = True

class UserPlanResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    status: PlanStatus
    retention_progress: Optional[float]

    class Config:
        orm_mode = True