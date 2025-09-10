from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.params import Form
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.document import Document, VerificationStatus
from app.models.notification import Notification, NotificationTargetType
from app.models.user import User
from app.schema.document import DocumentResponse, DocumentReuploadRequest
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
import os
import logging
import uuid
from datetime import datetime

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

VENDOR_REQUIRED_TYPES = [
    "business_registration",
    "business_license",
    "adhaar_card",
    "artisan_id_card",
    "bank_statement",
    "product_catalog",
    "certifications"
]

BUYER_REQUIRED_TYPES = [
    "business_registration",
    "business_license",
    "adhaar_card",
    "artisan_id_card",
    "bank_statement",
    "product_catalog",
    "certifications"
]

async def save_file(file: UploadFile, user_id: int, document_type: str) -> str:
    try:
        upload_dir = f"uploads/documents/{user_id}"
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{document_type}_{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving file for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@doc_router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str,
    file_url: str = Form(None),
    files: list[UploadFile] = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Uploading documents for user {current_user.email}: {document_type}")

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Allowed: {ALLOWED_DOCUMENT_TYPES}"
        )
    
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format for {file.filename}. Allowed: {ALLOWED_EXTENSIONS}"
            )

    if document_type not in ["product_catalog", "certifications"] and len(files) > 1:
        raise HTTPException(
            status_code=400,
            detail=f"Only one file allowed for {document_type}"
        )

    try:
        document_ids = []
        for file in files:
            file_path = await save_file(file, current_user.id, document_type)
            
            new_document = Document(
                user_id=current_user.id,
                document_type=document_type,
                file_path=file_path,
                file_url=file_url,
                file_name=file.filename,
                ai_verification_status=VerificationStatus.PENDING,
            )

            db.add(new_document)
            await db.flush()  # Ensure ID is generated
            document_ids.append(new_document.id)

            admin_notification = Notification(
                admin_id=current_user.id,
                message=f"Document {new_document.id} ({new_document.document_type}) uploaded by user_id={current_user.id} awaiting approval.",
                target_type=NotificationTargetType.ALL_ADMINS,
                visibility=True
            )
            db.add(admin_notification)

        await db.commit()  
        logger.debug(f"Committed documents for user {current_user.email}: {document_ids}")

        result = await db.execute(
            select(Document).filter(Document.id.in_(document_ids))
        )
        saved_documents = result.scalars().all()
        if len(saved_documents) != len(document_ids):
            raise HTTPException(
                status_code=500,
                detail=f"Only {len(saved_documents)} out of {len(document_ids)} documents saved in database"
            )

        await db.refresh(new_document)  # Refresh the last document

        result = await db.execute(
            select(Document).filter(Document.user_id == current_user.id)
        )
        documents = result.scalars().all()
        required_types = VENDOR_REQUIRED_TYPES if current_user.role == "vendor" else BUYER_REQUIRED_TYPES
        verified_types = {doc.document_type for doc in documents if doc.ai_verification_status == VerificationStatus.PASS}
        
        if all(t in verified_types for t in required_types):
            result = await db.execute(
                select(User).filter(User.id == current_user.id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if user.registration_step < 4:
                user.registration_step = 4
                db.add(user)
                await db.commit()

        logger.info(f"Documents uploaded successfully for user {current_user.email}: {document_ids}")
        return {
            "message": "Documents uploaded successfully",
            "documents": document_ids
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading documents for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload documents: {str(e)}")

@doc_router.get("/documents/progress")
async def get_document_progress(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching document progress for {current_user.email}")
    try:
        result = await db.execute(
            select(Document).filter(Document.user_id == current_user.id)
        )
        documents = result.scalars().all()
        uploaded_types = {doc.document_type for doc in documents}
        required_types = VENDOR_REQUIRED_TYPES if current_user.role == "vendor" else BUYER_REQUIRED_TYPES
        total_required = len(required_types)
        uploaded_count = len(uploaded_types)
        
        # For product_catalog and certifications, check if at least one document exists
        missing_types = [t for t in required_types if t not in uploaded_types]
        
        # Include uploaded documents with id and status
        uploaded_documents = [
            {"document_type": doc.document_type, "id": doc.id, "status": doc.ai_verification_status.value}
            for doc in documents
        ]
        
        return {
            "progress": f"{uploaded_count}/{total_required}",
            "uploaded_documents": uploaded_documents,
            "missing_documents": missing_types
        }
    except Exception as e:
        logger.error(f"Error fetching document progress for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch document progress: {str(e)}")

@doc_router.post("/reupload", status_code=status.HTTP_200_OK, response_model=DocumentResponse)
async def reupload_document(
    document_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    file_url: str = Form(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Re-uploading document {document_id} for user {current_user.email}: {document_type}")

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
            detail=f"Invalid file format for {file.filename}. Allowed: {ALLOWED_EXTENSIONS}"
        )

    try:
        result = await db.execute(
            select(Document).filter(
                Document.id == document_id,
                Document.user_id == current_user.id
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found or not owned by user")
        
        if document.document_type != document_type:
            raise HTTPException(
                status_code=400,
                detail=f"Document type mismatch. Expected {document.document_type}, got {document_type}"
            )

        file_path = await save_file(file, current_user.id, document_type)
        
        document.file_path = file_path
        document.file_url = file_url
        document.ai_verification_status = VerificationStatus.PENDING
        document.updated_at = func.now()
        
        # Create notification for admins
        admin_notification = Notification(
            admin_id=current_user.id,
            message=f"Document {document.id} ({document.document_type}) re-uploaded by user_id={current_user.id} awaiting approval.",
            target_type=NotificationTargetType.ALL_ADMINS,
            visibility=True
        )
        db.add(admin_notification)
        
        db.add(document)
        await db.commit()
        await db.refresh(document)

        
        logger.info(f"Document {document.id} re-uploaded by user_id={current_user.id}")
        return document
    except Exception as e:
        await db.rollback()
        logger.error(f"Error re-uploading document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to re-upload document: {str(e)}")