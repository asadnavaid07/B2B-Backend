from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
from app.models.document import Document, VerificationStatus
from app.services.ai_verification import analyze_document_advanced
import logging

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
        
        # Calculate KPI score based on verified documents
        kpi_score = 0
        doc_count = len(documents)
        if doc_count > 0:
            kpi_score = sum(doc.ai_kpi_score for doc in documents) / doc_count
            kpi_score = round(min(kpi_score, 10), 2)  # Cap at 10
        
        # Determine partnership level and retention period
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
        
        current_level = partnership_levels[0]
        for level in partnership_levels:
            if kpi_score >= level["min_kpi"]:
                current_level = level
            else:
                break
        
        return {
            "kpi_score": kpi_score,
            "partnership_level": current_level["level"],
            "retention_period": current_level["retention"],
            "verified_documents": len(documents)
        }
    except Exception as e:
        logger.error(f"Error calculating KPI score for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPI score: {str(e)}")