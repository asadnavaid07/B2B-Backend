from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.retention_service import RetentionService
from app.services.background_tasks import background_task_service
from app.schema.user import UserResponse, get_super_admin_role, get_sub_admin_role, UserRole
from app.services.auth.jwt import get_current_user
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

retention_router = APIRouter(prefix="/retention", tags=["retention"])

class RetentionUpdateResponse(BaseModel):
    message: str
    summary: Dict[str, Any]

class RetentionAnalyticsResponse(BaseModel):
    total_users: int
    average_retention: float
    retention_distribution: Dict[int, int]
    users_by_partnership_level: Dict[str, int]
    timestamp: str

class UserRetentionResponse(BaseModel):
    user_id: int
    email: str
    current_retention_months: int
    retention_start_date: str
    partnership_level: str

@retention_router.post("/update-all", response_model=RetentionUpdateResponse)
async def update_all_retention_periods(
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger retention period update for all users
    Requires super admin access
    """
    if role != get_super_admin_role():
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        # Run the update in background
        background_tasks.add_task(
            background_task_service.run_immediate_retention_update
        )
        
        return RetentionUpdateResponse(
            message="Retention update process started in background",
            summary={"status": "started", "triggered_by": current_user.email}
        )
        
    except Exception as e:
        logger.error(f"Error starting retention update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start retention update: {str(e)}")

@retention_router.post("/update-user/{user_id}", response_model=UserRetentionResponse)
async def update_user_retention_period(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Update retention period for a specific user
    Requires super admin access
    """
    if role not in [get_super_admin_role(), get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        new_retention_period = await RetentionService.update_user_retention_period(user_id, db)
        
        if new_retention_period is None:
            raise HTTPException(status_code=404, detail="User not found or not approved for retention tracking")
        
        # Get updated user data
        from sqlalchemy import Select
        from app.models.user import User
        
        result = await db.execute(Select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserRetentionResponse(
            user_id=user.id,
            email=user.email,
            current_retention_months=user.retention_period,
            retention_start_date=user.retention_start_date.isoformat() if user.retention_start_date else None,
            partnership_level=user.partnership_level or "UNKNOWN"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating retention for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user retention: {str(e)}")

@retention_router.get("/analytics", response_model=RetentionAnalyticsResponse)
async def get_retention_analytics(
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get retention analytics for all users
    Requires super admin access
    """
    if role not in [get_super_admin_role(), get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analytics = await RetentionService.get_retention_analytics(db)
        return RetentionAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"Error getting retention analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get retention analytics: {str(e)}")

@retention_router.get("/eligible-upgrades")
async def get_users_eligible_for_upgrades(
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get users who are eligible for partnership level upgrades based on retention
    Requires super admin access
    """
    if role not in [get_super_admin_role(), get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        eligible_users = await RetentionService.get_users_eligible_for_partnership_upgrade(db)
        
        # Format the response
        formatted_users = []
        for item in eligible_users:
            formatted_users.append({
                "user_id": item["user"].id,
                "email": item["user"].email,
                "current_retention_months": item["current_retention"],
                "partnership_level": item["level"].level,
                "required_retention_months": item["required_retention"],
                "kpi_score": item["user"].kpi_score,
                "retention_start_date": item["user"].retention_start_date.isoformat() if item["user"].retention_start_date else None
            })
        
        return {
            "eligible_users": formatted_users,
            "total_eligible": len(formatted_users),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting eligible users for upgrades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get eligible users: {str(e)}")

@retention_router.post("/scheduler/start")
async def start_retention_scheduler(
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role)
):
    """
    Start the monthly retention update scheduler
    Requires super admin access
    """
    if role != get_super_admin_role():
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        await background_task_service.start_retention_update_scheduler()
        return {"message": "Retention update scheduler started successfully"}
        
    except Exception as e:
        logger.error(f"Error starting retention scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@retention_router.post("/scheduler/stop")
async def stop_retention_scheduler(
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role)
):
    """
    Stop the monthly retention update scheduler
    Requires super admin access
    """
    if role != get_super_admin_role():
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        await background_task_service.stop_retention_update_scheduler()
        return {"message": "Retention update scheduler stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping retention scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@retention_router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role)
):
    """
    Get the status of the retention update scheduler
    Requires super admin access
    """
    if role not in [get_super_admin_role(), get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "is_running": background_task_service._is_running,
        "has_task": background_task_service._retention_update_task is not None,
        "task_done": background_task_service._retention_update_task.done() if background_task_service._retention_update_task else None,
        "timestamp": datetime.utcnow().isoformat()
    }
