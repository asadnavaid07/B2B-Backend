from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, delete, text
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.document import Document
from app.models.user import RegistrationStatus, User
from app.models.registration import RegistrationAgreement, RegistrationInfo, RegistrationLevel, RegistrationProduct, PartnershipLevel
from app.models.payment import PartnershipDeactivation
from app.services.auth.jwt import get_current_user
from app.schema.user import (
    UserDashboardResponse,
    UserResponse,
    UserRole,
    get_super_admin_role,
    PartnershipLevelStatusResponse,
)
from pydantic import BaseModel
from typing import Optional, List
import logging
from app.utils.partnership_level_mapping import (
    get_partnership_level_group,
    get_level_number,
    LEVEL_PARTNERSHIPS,
)
from app.models.partnership_fees import PartnershipLevelGroup

logger = logging.getLogger(__name__)
user_router = APIRouter(prefix="/user", tags=["user"])

LEVEL_GROUP_ORDER = [
    PartnershipLevelGroup.LEVEL_1,
    PartnershipLevelGroup.LEVEL_2,
    PartnershipLevelGroup.LEVEL_3,
    PartnershipLevelGroup.LEVEL_4,
]

class UserUpdate(BaseModel):
    email: Optional[str] = None

class PartnershipDeactivationRequest(BaseModel):
    partnership_level: PartnershipLevel
    deactivation_reason: Optional[str] = "User requested deactivation"

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
    

@user_router.get("/is-registered", status_code=200 )
async def check_registration_status(
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
        
        return{
            "is_registered": user.is_registered
        }
    except Exception as e:
        logger.error(f"Error checking registration status for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check registration status: {str(e)}")
    

@user_router.get("/user-product_data/{user_id}", status_code=200)
async def get_user_product_data(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(RegistrationProduct).filter(RegistrationProduct.user_id == user_id)
        )
        user_products = result.scalars().all()
        if not user_products:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Group products by category
        categories_dict = {}
        
        for product in user_products:
            product_data = product.product_data
            category_id = product_data.get("categoryId")
            category_name = product_data.get("categoryName")
            subcategory_id = product_data.get("subcategoryId")
            subcategory_name = product_data.get("subcategoryName")
            specifications = product_data.get("specifications", {})
            
            # Create category if it doesn't exist
            if category_id not in categories_dict:
                categories_dict[category_id] = {
                    "categoryId": category_id,
                    "categoryName": category_name,
                    "subcategories": []
                }
            
            # Add subcategory to the category
            subcategory = {
                "subcategoryId": subcategory_id,
                "subcategoryName": subcategory_name,
                "specifications": specifications
            }
            
            categories_dict[category_id]["subcategories"].append(subcategory)
        
        # Convert to the expected format
        selected_data = list(categories_dict.values())
        
        return {
            "selectedData": selected_data
        }
    

    except Exception as e:
        logger.error(f"Error fetching product data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch product data: {str(e)}")


@user_router.post("/user-lateral", status_code=200)
async def mark_user_as_lateral(
    is_lateral: bool,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    try:
        result = await db.execute(
            Select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_lateral = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User {user.email} marked as {'lateral' if is_lateral else 'non-lateral'} by admin_id={current_user.id}")
        return {
            "message": f"User marked as {'lateral' if is_lateral else 'non-lateral'} successfully",
            "user_id": user.id,
            "email": user.email,
            "is_lateral": user.is_lateral
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking user as lateral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark user as lateral: {str(e)}")
    
from fastapi import HTTPException

@user_router.get("/registration-selected", status_code=200)
async def registration_selected(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(RegistrationLevel).filter(RegistrationLevel.user_id == current_user.id)
        )
        levels = result.scalars().all()  
        if not levels:
            raise HTTPException(status_code=404, detail="No registration levels found for this user")

        return {
            "registration_selected": [level.level for level in levels]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching registration levels for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch registration info"
        )

@user_router.get("/partnership-level", response_model=PartnershipLevelStatusResponse)
async def get_partnership_level_status(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Provide the user's current partnership level group along with available partnerships
    in that group and information about the next level group.
    """
    try:
        result = await db.execute(
            select(RegistrationLevel).filter(RegistrationLevel.user_id == current_user.id)
        )
        levels = result.scalars().all()
        if not levels:
            raise HTTPException(status_code=404, detail="No partnership levels found for this user")

        level_groups = []
        for level in levels:
            group = get_partnership_level_group(level.level)
            if group:
                level_groups.append((level, group))

        if not level_groups:
            raise HTTPException(status_code=404, detail="No partnership level groups mapped for this user")

        # Determine highest level group achieved
        highest_level, current_group = max(
            level_groups,
            key=lambda item: get_level_number(item[1])
        )
        current_level_number = get_level_number(current_group)

        current_partnerships = [
            lvl.level.value for lvl, group in level_groups if group == current_group
        ]
        available_partnerships_in_group = [
            partnership.value for partnership in LEVEL_PARTNERSHIPS.get(current_group, [])
        ]

        # Determine next level group if any
        next_group = None
        if current_group in LEVEL_GROUP_ORDER:
            idx = LEVEL_GROUP_ORDER.index(current_group)
            if idx < len(LEVEL_GROUP_ORDER) - 1:
                next_group = LEVEL_GROUP_ORDER[idx + 1]

        next_level_partnerships = [
            partnership.value for partnership in LEVEL_PARTNERSHIPS.get(next_group, [])
        ] if next_group else []

        return PartnershipLevelStatusResponse(
            current_level_group=current_group,
            current_level_number=current_level_number,
            current_partnerships=current_partnerships,
            available_partnerships_in_group=available_partnerships_in_group,
            next_level_group=next_group,
            next_level_number=get_level_number(next_group) if next_group else None,
            next_level_partnerships=next_level_partnerships,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching partnership level info for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch partnership level information"
        )

@user_router.post("/first-register", status_code=200)
async def mark_user_as_first(
    is_first_register: bool,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    try:
        result = await db.execute(
            Select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.first_register = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return {
            "message": f"User marked as {'lateral' if is_first_register else 'non-lateral'} successfully",
            "user_id": user.id,
            "email": user.email,
            "is_lateral": user.first_register
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking user as lateral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark user as lateral: {str(e)}")
    


@user_router.post("/deactivate-partnership", status_code=200)
async def deactivate_partnership(
    request: PartnershipDeactivationRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a specific partnership for the current user.
    Removes the partnership from the user's active partnerships array.
    Ensures the user has at least one partnership (defaults to DROP_SHIPPING if empty).
    """
    try:
        # Get user from database
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get current active partnerships
        active_partnerships = []
        if user.partnership_level:
            if isinstance(user.partnership_level, list):
                active_partnerships = [PartnershipLevel(p) if isinstance(p, str) else p for p in user.partnership_level]
            elif isinstance(user.partnership_level, str):
                active_partnerships = [PartnershipLevel(user.partnership_level)]
        
        # Check if the partnership is active
        if request.partnership_level not in active_partnerships:
            raise HTTPException(
                status_code=400,
                detail=f"Partnership {request.partnership_level.value} is not active for this user"
            )
        
        # Check if this is the only partnership
        if len(active_partnerships) == 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate the only active partnership. You must have at least one active partnership."
            )
        
        # Remove the partnership from active list
        active_partnerships.remove(request.partnership_level)
        
        # Ensure user has at least DROP_SHIPPING if list becomes empty (safety check)
        if not active_partnerships:
            active_partnerships = [PartnershipLevel.DROP_SHIPPING]
        
        # Update user's partnership level
        user.partnership_level = [p.value for p in active_partnerships]
        
        # Check if deactivation record already exists
        existing_deactivation = await db.execute(
            select(PartnershipDeactivation).filter(
                PartnershipDeactivation.user_id == current_user.id,
                PartnershipDeactivation.partnership_level == request.partnership_level
            )
        )
        deactivation_record = existing_deactivation.scalar_one_or_none()
        
        if not deactivation_record:
            # Create deactivation record
            deactivation = PartnershipDeactivation(
                user_id=current_user.id,
                partnership_level=request.partnership_level,
                deactivation_reason=request.deactivation_reason or "User requested deactivation"
            )
            db.add(deactivation)
        else:
            # Update existing deactivation record if it was reactivated
            if deactivation_record.reactivated_at:
                deactivation_record.reactivated_at = None
                deactivation_record.deactivation_reason = request.deactivation_reason or "User requested deactivation"
                deactivation_record.deactivated_at = func.now()
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Partnership {request.partnership_level.value} deactivated for user_id={current_user.id}")
        
        return {
            "message": f"Partnership {request.partnership_level.value} deactivated successfully",
            "user_id": user.id,
            "active_partnerships": [p.value for p in active_partnerships],
            "deactivated_partnership": request.partnership_level.value
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deactivating partnership for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate partnership: {str(e)}")


@user_router.post("/rejected/{user_id}", status_code=200)
async def rejected_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        print(user.is_registered)

        if user.is_registered != RegistrationStatus.REJECTED:
            raise HTTPException(status_code=400, detail="User is not in REJECTED status")

        # Delete related records safely
        await db.execute(delete(RegistrationInfo).where(RegistrationInfo.user_id == user_id))
        await db.execute(delete(RegistrationLevel).where(RegistrationLevel.user_id == user_id))
        await db.execute(delete(RegistrationProduct).where(RegistrationProduct.user_id == user_id))
        await db.execute(delete(Document).where(Document.user_id == user_id))
        await db.execute(delete(RegistrationAgreement).where(RegistrationAgreement.user_id == user_id))


        user.is_registered = RegistrationStatus.PENDING
        db.add(user)

        await db.commit()
        await db.refresh(user)

        return {"message": "User reset to PENDING and related data deleted successfully"}

    except HTTPException:
        raise  # Re-raise known exceptions
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")




        





