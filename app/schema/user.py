from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum
from typing import Optional, Dict, List
from app.models.user import UserRole
from app.schema.document import DocumentResponse


class UserRole(str, Enum):
    vendor = "vendor"
    buyer = "buyer"
    super_admin = "super_admin"
    sub_admin = "sub_admin"

class ResendOTPRequest(BaseModel):
    email: str

class GoogleLoginRequest(BaseModel):
    id_token: str
    role: str

    @validator("role")
    def validate_role(cls, value):
        try:
            role = UserRole(value.lower())
            if role not in [UserRole.buyer, UserRole.vendor]:
                raise ValueError("Role must be 'buyer' or 'vendor'")
            return value
        except ValueError:
            raise ValueError("Invalid role. Must be 'buyer' or 'vendor'")


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
    first_register: Optional[bool] = False
    is_lateral: Optional[bool] = False
    payment_status: Optional[bool] = False


class UserResponse(BaseModel):
    id: int
    username: Optional[str] = None
    email: EmailStr
    role: UserRole
    is_active: bool
    visibility_level: Optional[int] = None
    ownership: Optional[Dict[str, List[str]]] = None
    is_registered: Optional[str] = "PENDING"
    registration_step: Optional[int] = 0
    first_register: Optional[bool] = False  
    is_lateral: Optional[bool] = False
    payment_status: Optional[bool] = False


    class Config:
        from_attributes = True

class UserDashboardResponse(BaseModel):
    id: int
    username: Optional[str] = None
    email: EmailStr
    role: UserRole
    is_active: bool
    visibility_level: Optional[int] = None
    ownership: Optional[Dict[str, List[str]]] = None
    kpi_score: Optional[float] = None         
    partnership_level: Optional[List[str]] = None  # Array of active partnerships
    retention_period: Optional[int] = 0
    is_registered: Optional[str] = "PENDING"
    registration_step: Optional[int] = 0 
    is_lateral: Optional[bool] = False
    payment_status: Optional[bool] = False

    class Config:
        from_attributes = True
        

    class Config:
        from_attributes = True

class SubAdminResponse(BaseModel):
    username: Optional[str] = None
    email: str
    password: str
    visibility_level: int
    ownership: Dict[str, List[str]]

class PlanResponse(BaseModel):
    id: int
    name: str
    level: int

    class Config:
        from_attributes = True

class UserPlanResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    status: PlanStatus
    retention_progress: Optional[float]

    class Config:
        from_attributes = True