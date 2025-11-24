from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import DBAPIError
from app.core.database import get_db, async_session, engine
from asyncpg.exceptions import InvalidCachedStatementError
from app.models.partnership_fees import PartnershipFees, PartnershipLevelGroup
from app.schema.partnership_fees import PartnershipFeesCreate, PartnershipFeesUpdate, PartnershipFeesResponse
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse, UserRole
from typing import List
import logging

logger = logging.getLogger(__name__)
partnership_fees_router = APIRouter(prefix="/admin/partnership-fees", tags=["admin-partnership-fees"])

async def get_admin_role(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@partnership_fees_router.get("/", response_model=List[PartnershipFeesResponse])
async def get_all_partnership_fees(
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get all partnership fees (Admin only)"""
    try:
        result = await db.execute(select(PartnershipFees))
        fees = result.scalars().all()
        logger.info(f"Fetched {len(fees)} partnership fees for admin_id={current_user.id}")
        return fees
    except Exception as e:
        logger.error(f"Error fetching partnership fees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch partnership fees: {str(e)}")

@partnership_fees_router.get("/{level_group}", response_model=PartnershipFeesResponse)
async def get_partnership_fees(
    level_group: PartnershipLevelGroup,
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get fees for a specific level group (Admin only)"""
    try:
        result = await db.execute(
            select(PartnershipFees).filter(PartnershipFees.level_group == level_group)
        )
        fees = result.scalar_one_or_none()
        if not fees:
            raise HTTPException(status_code=404, detail=f"Fees for level group {level_group.value} not found")
        return fees
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching partnership fees for {level_group.value}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch partnership fees: {str(e)}")

async def _create_partnership_fee_record(db: AsyncSession, fees: PartnershipFeesCreate, admin_id: int):
    """Shared logic to insert partnership fee row."""
    # Check if fees already exist for this level group
    result = await db.execute(
        select(PartnershipFees).filter(PartnershipFees.level_group == fees.level_group)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Fees for level group {fees.level_group.value} already exist")

    # Validate lateral_fees structure
    if fees.lateral_fees and not all(key in fees.lateral_fees for key in ["1st", "2nd", "3rd"]):
        raise HTTPException(
            status_code=400,
            detail="lateral_fees must include '1st', '2nd', and '3rd' keys"
        )

    new_fees = PartnershipFees(
        level_group=fees.level_group,
        registration_fee=fees.registration_fee,
        lateral_fees=fees.lateral_fees or {"1st": 0.0, "2nd": 0.0, "3rd": 0.0}
    )
    db.add(new_fees)
    await db.commit()
    await db.refresh(new_fees)
    logger.info(f"Created partnership fees for {fees.level_group.value} by admin_id={admin_id}")
    return new_fees


async def _run_with_cached_plan_retry(fees: PartnershipFeesCreate, admin_id: int, primary_session: AsyncSession):
    """Execute creation logic and transparently retry once if cached plans become invalid."""
    try:
        return await _create_partnership_fee_record(primary_session, fees, admin_id)
    except DBAPIError as db_err:
        await primary_session.rollback()
        if isinstance(getattr(db_err, "orig", None), InvalidCachedStatementError):
            logger.warning("Invalid cached statement detected; disposing engine and retrying with fresh session.")
            await engine.dispose()
            async with async_session() as retry_session:
                return await _create_partnership_fee_record(retry_session, fees, admin_id)
        raise


@partnership_fees_router.post("/", status_code=status.HTTP_201_CREATED, response_model=PartnershipFeesResponse)
async def create_partnership_fees(
    fees: PartnershipFeesCreate,
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Create fees for a level group (Admin only)"""
    try:
        return await _run_with_cached_plan_retry(fees, current_user.id, db)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating partnership fees for {fees.level_group.value}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create partnership fees: {str(e)}")

@partnership_fees_router.put("/{level_group}", status_code=status.HTTP_200_OK, response_model=PartnershipFeesResponse)
async def update_partnership_fees(
    level_group: PartnershipLevelGroup,
    fees_update: PartnershipFeesUpdate,
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Update registration fee and/or lateral fee for a level group (Admin only)"""
    try:
        result = await db.execute(
            select(PartnershipFees).filter(PartnershipFees.level_group == level_group)
        )
        fees = result.scalar_one_or_none()
        if not fees:
            raise HTTPException(status_code=404, detail=f"Fees for level group {level_group.value} not found")
        
        # Update fields if provided
        if fees_update.registration_fee is not None:
            fees.registration_fee = fees_update.registration_fee
        if fees_update.lateral_fees is not None:
            # Validate lateral_fees structure
            if not all(key in fees_update.lateral_fees for key in ["1st", "2nd", "3rd"]):
                raise HTTPException(
                    status_code=400, 
                    detail="lateral_fees must include '1st', '2nd', and '3rd' keys"
                )
            fees.lateral_fees = fees_update.lateral_fees
        
        db.add(fees)
        await db.commit()
        await db.refresh(fees)
        logger.info(f"Updated partnership fees for {level_group.value} by admin_id={current_user.id}")
        return fees
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating partnership fees for {level_group.value}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update partnership fees: {str(e)}")

