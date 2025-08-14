from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.document import Document
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
import os
import logging
import uuid

logger = logging.getLogger(__name__)
doc_router = APIRouter(prefix="/user", tags=["documents"])

ALLOWED_DOCUMENT_TYPES = [
    "business_registration",
    "business_license",
    "adhaar_card",
    "artisan_id_card",
    "bank_statement",
    "product_catalog",
    "certifications"
]

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx"}

@doc_router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Uploading document for user {current_user.email}: {document_type}")

    # Validate document type
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Allowed: {ALLOWED_DOCUMENT_TYPES}"
        )

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {ALLOWED_EXTENSIONS}"
        )

    try:
        # Save file with unique name
        upload_dir = "uploads/documents"
        os.makedirs(upload_dir, exist_ok=True)
        unique_filename = f"{current_user.id}_{document_type}_{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Save to database
        new_document = Document(
            user_id=current_user.id,
            document_type=document_type,
            file_path=file_path,
            file_name=file.filename,
            ai_verification_status="PENDING",  # Now valid after enum update
            ai_kpi_score=0,
            ai_remarks="Awaiting AI verification"
        )
        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)

        logger.info(f"Document uploaded: {document_type} for {current_user.email}")
        return {
            "message": "Document uploaded successfully",
            "file_path": file_path,
            "document_id": new_document.id
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading document for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@doc_router.get("/documents/progress")
async def get_document_progress(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching document progress for {current_user.email}")
    try:
        result = await db.execute(
            select(Document.document_type).filter(Document.user_id == current_user.id)
        )
        uploaded_types = {doc for doc in result.scalars().all()}
        total_required = len(ALLOWED_DOCUMENT_TYPES)
        uploaded_count = len(uploaded_types)
        return {
            "progress": f"{uploaded_count}/{total_required}",
            "uploaded_documents": list(uploaded_types),
            "missing_documents": list(set(ALLOWED_DOCUMENT_TYPES) - uploaded_types)
        }
    except Exception as e:
        logger.error(f"Error fetching document progress for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch document progress: {str(e)}")