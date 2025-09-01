from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.partnership_pricing import PartnershipLevelModel
from app.schema.partnership_level import PartnershipLevelCreate, PartnershipLevelUpdate, PartnershipLevelResponse
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse, UserRole
import logging
from typing import List

logger = logging.getLogger(__name__)
partnership_level_router = APIRouter(prefix="/partnership-levels", tags=["partnership-levels"])

async def get_admin_role(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@partnership_level_router.get("/", response_model=List[PartnershipLevelResponse])
async def get_partnership_levels(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(PartnershipLevelModel))
        levels = result.scalars().all()
        logger.info(f"Fetched {len(levels)} partnership levels for user_id={current_user.id}")
        return levels
    except Exception as e:
        logger.error(f"Error fetching partnership levels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch partnership levels: {str(e)}")

@partnership_level_router.post("/", status_code=status.HTTP_201_CREATED, response_model=PartnershipLevelResponse)
async def create_partnership_level(
    level: PartnershipLevelCreate,
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Validate prices structure
        if not all(key in level.prices for key in ["1st", "2nd", "3rd"]):
            raise HTTPException(status_code=400, detail="Prices must include '1st', '2nd', and '3rd' keys")
        
        # Check if partnership_name already exists
        result = await db.execute(
            select(PartnershipLevelModel).filter(PartnershipLevelModel.partnership_name == level.partnership_name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Partnership level '{level.partnership_name}' already exists")
        
        new_level = PartnershipLevelModel(
            partnership_name=level.partnership_name,
            prices=level.prices
        )
        db.add(new_level)
        await db.commit()
        await db.refresh(new_level)
        logger.info(f"Created partnership level '{level.partnership_name}' by admin_id={current_user.id}")
        return new_level
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating partnership level '{level.partnership_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create partnership level: {str(e)}")

@partnership_level_router.put("/{id}", status_code=status.HTTP_200_OK, response_model=PartnershipLevelResponse)
async def update_partnership_level(
    id: int,
    level_update: PartnershipLevelUpdate,
    current_user: UserResponse = Depends(get_admin_role),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Fetch existing level
        result = await db.execute(select(PartnershipLevelModel).filter(PartnershipLevelModel.id == id))
        level = result.scalar_one_or_none()
        if not level:
            raise HTTPException(status_code=404, detail="Partnership level not found")
        
        # Update fields if provided
        if level_update.partnership_name is not None:
            # Check if new name already exists
            result = await db.execute(
                select(PartnershipLevelModel).filter(
                    PartnershipLevelModel.partnership_name == level_update.partnership_name,
                    PartnershipLevelModel.id != id
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"Partnership level '{level_update.partnership_name}' already exists")
            level.partnership_name = level_update.partnership_name
        
        if level_update.prices is not None:
            if not all(key in level_update.prices for key in ["1st", "2nd", "3rd"]):
                raise HTTPException(status_code=400, detail="Prices must include '1st', '2nd', and '3rd' keys")
            level.prices = level_update.prices
        
        db.add(level)
        await db.commit()
        await db.refresh(level)
        logger.info(f"Updated partnership level id={id} by admin_id={current_user.id}")
        return level
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating partnership level id={id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update partnership level: {str(e)}")