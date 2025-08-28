from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.notification import Notification, NotificationTargetType
from app.schema.notification import NotificationResponse
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse, UserRole
import logging

logger = logging.getLogger(__name__)
notification_router = APIRouter(prefix="/notifications", tags=["notifications"])

@notification_router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Define role-to-target mapping
        role_to_targets = {
            UserRole.super_admin: [NotificationTargetType.ALL_USERS, NotificationTargetType.SUB_ADMINS],
            UserRole.sub_admin: [NotificationTargetType.ALL_USERS, NotificationTargetType.SUB_ADMINS],
            UserRole.buyer: [NotificationTargetType.ALL_USERS, NotificationTargetType.BUYERS],
            UserRole.vendor: [NotificationTargetType.ALL_USERS, NotificationTargetType.VENDORS]
        }
        
        target_types = role_to_targets.get(current_user.role, [NotificationTargetType.ALL_USERS])
        
        result = await db.execute(
            select(Notification)
            .filter(
                Notification.target_type.in_(target_types),
                Notification.visibility == True
            )
            .order_by(Notification.created_at.desc())
        )
        notifications = result.scalars().all()
        logger.info(f"Fetched {len(notifications)} notifications for user_id={current_user.id}, role={current_user.role}")
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications for user_id={current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")