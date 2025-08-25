from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.models.registration import RegistrationInfo
from app.services.auth.jwt import get_current_user
from app.schema.user import UserDashboardResponse, UserResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
user_router = APIRouter(prefix="/user", tags=["user"])

class UserUpdate(BaseModel):
    email: Optional[str] = None

class RegistrationInfoUpdate(BaseModel):
    business_name: Optional[str] = None
    business_legal_structure: Optional[str] = None
    business_type: Optional[str] = None
    year_established: Optional[int] = None
    business_registration_number: Optional[str] = None
    brand_affiliations: Optional[str] = None
    website: Optional[str] = None
    annual_turnover: Optional[str] = None
    gst_number: Optional[str] = None
    tax_identification_number: Optional[str] = None
    import_export_code: Optional[str] = None
    street_address_1: Optional[str] = None
    street_address_2: Optional[str] = None
    city: Optional[str] = None
    state_region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_district: Optional[str] = None
    contact_pin_code: Optional[str] = None
    contact_state: Optional[str] = None
    contact_country: Optional[str] = None
    material_standard: Optional[int] = None
    quality_level: Optional[int] = None
    sustainability_level: Optional[int] = None
    service_level: Optional[int] = None
    standards_level: Optional[int] = None
    ethics_level: Optional[int] = None
    certifications: Optional[List[str]] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    swift_bis_code: Optional[str] = None
    iban_code: Optional[str] = None

@user_router.put("/profile", status_code=200)
async def update_profile(
    user_update: UserUpdate,
    registration_info_update: RegistrationInfoUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Fetch user
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update user info (only email is editable)
        if user_update.email and user_update.email != user.email:
            # Check if new email is unique
            result = await db.execute(
                select(User).filter(User.email == user_update.email)
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already exists")
            user.email = user_update.email

        # Fetch or create registration info
        result = await db.execute(
            select(RegistrationInfo).filter(RegistrationInfo.user_id == current_user.id)
        )
        reg_info = result.scalar_one_or_none()
        if not reg_info:
            reg_info = RegistrationInfo(user_id=current_user.id)

        # Update registration info
        for field, value in registration_info_update.dict(exclude_unset=True).items():
            setattr(reg_info, field, value)

        db.add(user)
        db.add(reg_info)
        await db.commit()
        await db.refresh(user)
        await db.refresh(reg_info)

        logger.info(f"Profile updated for user {current_user.id}: {user.email}")
        return {
            "message": "Profile updated successfully",
            "user_id": user.id,
            "email": user.email,
            "registration_info": reg_info.__dict__
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating profile for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@user_router.get("/profile", response_model=UserDashboardResponse)
async def get_profile(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except Exception as e:
        logger.error(f"Error fetching profile for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")