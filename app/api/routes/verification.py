from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.registration import PartnershipLevel
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
from app.models.document import Document, VerificationStatus
from app.models.user import User
from app.models.notification import Notification, NotificationTargetType
from app.services.ai_verification import analyze_document_advanced
import logging
from datetime import datetime, timedelta
from app.utils.partnership_levels import get_available_partnerships, get_retention_expiration, is_retention_period_over, partnership_level,partnership_dic, update_partnership_level
logger = logging.getLogger(__name__)
verification_router = APIRouter(prefix="/verification", tags=["verification"])



@verification_router.get("/status")
async def get_verification_status(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching verification status for {current_user.email}")
    try:
        result = await db.execute(
            select(Document).filter(Document.user_id == current_user.id)
        )
        documents = result.scalars().all()
        
        # Verify pending documents
        for doc in documents:
            if doc.ai_verification_status == VerificationStatus.PENDING:
                await analyze_document_advanced(doc.id, doc.file_path, doc.document_type, db)
        
        # Refresh documents
        result = await db.execute(
            select(Document).filter(Document.user_id == current_user.id)
        )
        documents = result.scalars().all()
        
        return {
            "documents": [
                {
                    "document_id": doc.id,
                    "document_type": doc.document_type,
                    "file_name": doc.file_name,
                    "status": doc.ai_verification_status.value,
                    "kpi_score": doc.ai_kpi_score,
                    "remarks": doc.ai_remarks,
                    "extracted_data": doc.extracted_data
                } for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching verification status for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch verification status: {str(e)}")

@verification_router.get("/kpiscore")
async def get_kpi_score(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Calculating KPI score for {current_user.email}")
    try:
        # Get verified documents
        result = await db.execute(
            select(Document).filter(
                Document.user_id == current_user.id,
                Document.ai_verification_status == VerificationStatus.PASS
            )
        )
        documents = result.scalars().all()
        
        # Calculate KPI score
        kpi_score = 0
        doc_count = len(documents)
        if doc_count > 0:
            kpi_score = sum(doc.ai_kpi_score for doc in documents) / doc_count
            kpi_score = round(min(kpi_score, 10), 2)  # Cap at 10
        
        # Get user
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User not found: {current_user.email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update KPI score
        user.kpi_score = kpi_score
        partnership_updated = False
        if user.retention_start_date and is_retention_period_over(user.retention_period, user.retention_start_date, datetime.utcnow()):
            partnership_updated = await update_partnership_level(user, kpi_score, db)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        partnership_levels = partnership_dic
        
        current_level = next((level for level in partnership_levels if level["level"] == user.partnership_level), partnership_levels[0])
        
        logger.info(f"KPI score for {current_user.email}: kpi_score={kpi_score}, "
                   f"partnership_level={user.partnership_level}, "
                   f"retention_period={user.retention_period}, "
                   f"partnership_updated={partnership_updated}")
        
        return {
            "kpi_score": kpi_score,
            "partnership_level": user.partnership_level,
            "retention_period": user.retention_period,
            "verified_documents": len(documents),
            "partnership_updated": partnership_updated
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error calculating KPI score for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPI score: {str(e)}")



@verification_router.get("/notifications")
async def get_notifications(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching notifications for {current_user.email}")
    try:
        result = await db.execute(
            select(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
        )
        notifications = result.scalars().all()
        return [
            {
                "id": notif.id,
                "message": notif.message,
                "created_at": notif.created_at.isoformat(),
                "is_read": notif.is_read
            } for notif in notifications
        ]
    except Exception as e:
        logger.error(f"Error fetching notifications for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")
    









@verification_router.get("/current-partnership", response_model=dict)
async def get_current_partnership(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching current partnership for {current_user.email}")
    try:
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User not found: {current_user.email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate retention expiration
        retention_expiration = get_retention_expiration(user.retention_period, user.retention_start_date)
        is_retention_expired = retention_expiration and datetime.utcnow() >= retention_expiration if retention_expiration else False
        
        return {
            "partnership_level": user.partnership_level if user.partnership_level else None,
            "kpi_score": user.kpi_score,
            "retention_period": user.retention_period,
            "retention_expiration": retention_expiration.isoformat() if retention_expiration else None,
            "is_retention_expired": is_retention_expired
        }
    except Exception as e:
        logger.error(f"Error fetching current partnership for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch current partnership: {str(e)}")






@verification_router.get("/available-partnerships", response_model=dict)
async def get_available_partnerships_api(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching available partnerships for {current_user.email}")
    try:
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User not found: {current_user.email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get available partnerships
        available_partnerships = get_available_partnerships(user.kpi_score, user.partnership_level, user.retention_period)
        
        return {
            "available_partnerships": available_partnerships,
            "kpi_score": user.kpi_score,
            "current_partnership_level": user.partnership_level,
            "retention_period": user.retention_period,
            "retention_expiration": get_retention_expiration(user.retention_period, user.retention_start_date).isoformat() if user.retention_start_date else None
        }
    except Exception as e:
        logger.error(f"Error fetching available partnerships for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch available partnerships: {str(e)}")

@verification_router.get("/kpiscore", response_model=dict)
async def get_kpi_score(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Calculating KPI score for {current_user.email}")
    try:
        # Get verified documents
        result = await db.execute(
            select(Document).filter(
                Document.user_id == current_user.id,
                Document.ai_verification_status == VerificationStatus.PASS
            )
        )
        documents = result.scalars().all()
        
        # Calculate KPI score
        kpi_score = 0.0
        doc_count = len(documents)
        if doc_count > 0:
            kpi_score = sum(doc.ai_kpi_score for doc in documents) / doc_count
            kpi_score = round(min(kpi_score, 10), 2)  # Cap at 10
        
        # Get user
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User not found: {current_user.email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update KPI score
        user.kpi_score = kpi_score
        partnership_updated = False
        if user.retention_start_date:
            partnership_updated = await update_partnership_level(user, kpi_score, db)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Calculate retention expiration
        retention_expiration = get_retention_expiration(user.retention_period, user.retention_start_date)
        is_retention_expired = retention_expiration and datetime.utcnow() >= retention_expiration if retention_expiration else False
        
        # Get available partnerships
        available_partnerships = get_available_partnerships(kpi_score, user.partnership_level, user.retention_period, user.retention_start_date)
        
        logger.info(f"KPI score for {current_user.email}: kpi_score={kpi_score}, "
                   f"partnership_level={user.partnership_level}, "
                   f"retention_period={user.retention_period}, "
                   f"retention_expiration={retention_expiration}, "
                   f"partnership_updated={partnership_updated}, "
                   f"available_partnerships={[p.value for p in available_partnerships]}")
        
        return {
            "kpi_score": kpi_score,
            "partnership_level": user.partnership_level.value,
            "retention_period": user.retention_period,
            "retention_expiration": retention_expiration.isoformat() if retention_expiration else None,
            "is_retention_expired": is_retention_expired,
            "available_partnerships": [p.value for p in available_partnerships],
            "verified_documents": len(documents),
            "partnership_updated": partnership_updated
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error calculating KPI score for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPI score: {str(e)}")

@verification_router.post("/update-partnership", status_code=200)
async def update_partnership(
    partnership_level: PartnershipLevel,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(select(User).filter(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.partnership_level = partnership_level.value
    db.add(user)            
    await db.commit()      
    await db.refresh(user)  

    return {
        "message": "Partnership level updated successfully",
        "partnership_level": user.partnership_level
    }


    


@verification_router.get("/notifications", response_model=List[dict])
async def get_notifications(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching notifications for {current_user.email}")
    try:
        result = await db.execute(
            select(Notification).filter(Notification.admin_id == current_user.id).order_by(Notification.created_at.desc())
        )
        notifications = result.scalars().all()
        return [
            {
                "id": notif.id,
                "message": notif.message,
                "created_at": notif.created_at.isoformat(),
                "is_read": notif.is_read
            } for notif in notifications
        ]
    except Exception as e:
        logger.error(f"Error fetching notifications for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")