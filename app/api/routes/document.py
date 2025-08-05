# app/routers/user.py (or wherever you're defining routes)
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import uuid4
from pathlib import Path
import os

from app.core.database import get_db
from app.models.document import Document, DocumentType, VerificationStatus
from app.schema.document import DocumentResponse
from app.schema.user import UserResponse
from app.services.auth.jwt import role_required
from app.models.plan import PlanStatus

user_router = APIRouter(tags=["documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

def validate_file(filename: str):
    if not filename or "." not in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


# Upload Document
@user_router.post("/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    document_type: DocumentType,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(role_required("vendor", "buyer")),
    db: AsyncSession = Depends(get_db)
):
    ext = validate_file(file.filename)
    filename = f"{uuid4()}.{ext}"
    user_folder = Path(UPLOAD_DIR) / str(current_user.id)
    user_folder.mkdir(parents=True, exist_ok=True)
    file_path = user_folder / filename

    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                buffer.write(chunk)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    document = Document(
        user_id=current_user.id,
        document_type=document_type,
        file_path=str(file_path),
        ai_verification_status=VerificationStatus.PENDING
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


# List Documents
@user_router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_user: UserResponse = Depends(role_required("vendor", "buyer", "super_admin", "sub_admin")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).filter(Document.user_id == current_user.id))
    return result.scalars().all()


# Update Document (re-upload file only)
@user_router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(role_required("vendor", "buyer")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document).filter(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    ext = validate_file(file.filename)
    filename = f"{uuid4()}.{ext}"
    file_path = Path(UPLOAD_DIR) / str(current_user.id) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Remove old file if exists
    old_file = Path(document.file_path)
    if old_file.exists():
        old_file.unlink()

    document.file_path = str(file_path)
    document.ai_verification_status = VerificationStatus.PENDING
    await db.commit()
    await db.refresh(document)
    return document


# Delete Document
@user_router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: UserResponse = Depends(role_required("vendor", "buyer")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document).filter(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove file from disk
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(document)
    await db.commit()
    return {"message": "Document deleted successfully"}
