from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
from app.models.document import Document, VerificationStatus
from app.models.user import User
from app.models.notification import Notification
from app.services.ai_verification import analyze_document_advanced
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
verification_router = APIRouter(prefix="/verification", tags=["verification"])

def is_retention_period_over(retention_period: str, retention_start_date: datetime, current_date: datetime) -> bool:
    if retention_period == "None":
        return True
    months = 6 if retention_period == "6 months" else 12
    retention_end = retention_start_date + timedelta(days=months * 30)  # Approximate months
    return current_date >= retention_end

async def update_partnership_level(user: User, kpi_score: float, db: AsyncSession):
    partnership_levels = [
        {"level": "Drop Shipping Vendor", "min_kpi": 0, "retention": "None"},
        {"level": "Consignment Vendor", "min_kpi": 5.5, "retention": "6 months"},
        {"level": "Export Vendor", "min_kpi": 6.0, "retention": "6 months"},
        {"level": "Wholesale & Distribution Vendor", "min_kpi": 6.5, "retention": "6 months"},
        {"level": "Exhibition & Event Organizer Vendor", "min_kpi": 7.0, "retention": "12 months"},
        {"level": "Auction & Bidding Vendor", "min_kpi": 7.2, "retention": "12 months"},
        {"level": "White-Label Vendor", "min_kpi": 7.5, "retention": "12 months"},
        {"level": "Brick & Mortar Space-Sharing Vendor", "min_kpi": 7.8, "retention": "12 months"},
        {"level": "Knowledge & Design Collaboration Vendor", "min_kpi": 8.0, "retention": "12 months"},
        {"level": "Storytelling & Media Vendor", "min_kpi": 8.2, "retention": "12 months"},
        {"level": "Buyer Mentorship Program Vendor", "min_kpi": 8.5, "retention": "12 months"},
        {"level": "Craft Innovation Patron Vendor", "min_kpi": 8.8, "retention": "12 months"},
        {"level": "Strategic Investor Vendor", "min_kpi": 9.0, "retention": "12 months"},
        {"level": "Museum / Institutional Vendor", "min_kpi": 9.2, "retention": "12 months"},
        {"level": "NGO & Government Collaboration Vendor", "min_kpi": 9.4, "retention": "12 months"},
        {"level": "Impact Measurement Vendor", "min_kpi": 9.6, "retention": "12 months"}
    ]
    
    current_level_index = next((i for i, level in enumerate(partnership_levels) if level["level"] == user.partnership_level), 0)
    current_level = partnership_levels[current_level_index]
    next_level = partnership_levels[min(current_level_index + 1, len(partnership_levels) - 1)] if current_level_index < len(partnership_levels) - 1 else current_level
    
    if kpi_score >= next_level["min_kpi"]:
        user.partnership_level = next_level["level"]
        user.retention_period = next_level["retention"]
        user.retention_start_date = datetime.utcnow()
        
        # Create notification
        notification = Notification(
            user_id=user.id,
            message=f"Congratulations! Your partnership level has been upgraded to {next_level['level']}.",
            created_at=datetime.utcnow(),
            is_read=False
        )
        db.add(notification)
        return True
    return False

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
        
        partnership_levels = [
            {"level": "Drop Shipping Vendor", "min_kpi": 0, "retention": "None"},
            {"level": "Consignment Vendor", "min_kpi": 5.5, "retention": "6 months"},
            {"level": "Export Vendor", "min_kpi": 6.0, "retention": "6 months"},
            {"level": "Wholesale & Distribution Vendor", "min_kpi": 6.5, "retention": "6 months"},
            {"level": "Exhibition & Event Organizer Vendor", "min_kpi": 7.0, "retention": "12 months"},
            {"level": "Auction & Bidding Vendor", "min_kpi": 7.2, "retention": "12 months"},
            {"level": "White-Label Vendor", "min_kpi": 7.5, "retention": "12 months"},
            {"level": "Brick & Mortar Space-Sharing Vendor", "min_kpi": 7.8, "retention": "12 months"},
            {"level": "Knowledge & Design Collaboration Vendor", "min_kpi": 8.0, "retention": "12 months"},
            {"level": "Storytelling & Media Vendor", "min_kpi": 8.2, "retention": "12 months"},
            {"level": "Buyer Mentorship Program Vendor", "min_kpi": 8.5, "retention": "12 months"},
            {"level": "Craft Innovation Patron Vendor", "min_kpi": 8.8, "retention": "12 months"},
            {"level": "Strategic Investor Vendor", "min_kpi": 9.0, "retention": "12 months"},
            {"level": "Museum / Institutional Vendor", "min_kpi": 9.2, "retention": "12 months"},
            {"level": "NGO & Government Collaboration Vendor", "min_kpi": 9.4, "retention": "12 months"},
            {"level": "Impact Measurement Vendor", "min_kpi": 9.6, "retention": "12 months"}
        ]
        
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

@verification_router.post("/update-partnership")
async def update_partnership(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Checking partnership update for {current_user.email}")
    try:
        # Get user
        result = await db.execute(
            select(User).filter(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User not found: {current_user.email}")
            raise HTTPException(status_code=404, detail="User not found")
        
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
            kpi_score = round(min(kpi_score, 10), 2)
        
        # Check if retention period is over
        partnership_updated = False
        if user.retention_start_date and is_retention_period_over(user.retention_period, user.retention_start_date, datetime.utcnow()):
            partnership_updated = await update_partnership_level(user, kpi_score, db)
        
        if partnership_updated:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Partnership updated for {current_user.email}: "
                       f"new_level={user.partnership_level}, retention_period={user.retention_period}")
            return {
                "message": f"Partnership level updated to {user.partnership_level}",
                "kpi_score": kpi_score,
                "partnership_level": user.partnership_level,
                "retention_period": user.retention_period
            }
        else:
            return {
                "message": "No partnership update required or retention period not yet over",
                "kpi_score": kpi_score,
                "partnership_level": user.partnership_level,
                "retention_period": user.retention_period
            }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating partnership for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update partnership: {str(e)}")

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