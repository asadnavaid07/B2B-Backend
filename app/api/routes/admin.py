from datetime import datetime
from select import select
from fastapi import APIRouter,Depends, HTTPException, logger
from pydantic import BaseModel
from sqlalchemy import Select, func
from app.models.document import Document
from app.models.notification import Notification, NotificationTargetType
from app.schema.document import DocumentApproveRequest, DocumentResponse, VerificationStatus
from app.schema.notification import NotificationCreate, NotificationResponse
from app.schema.user import UserDashboardResponse, UserRole,get_super_admin_role,get_sub_admin_role,UserResponse
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import RegistrationStatus, User
from app.models.registration import RegistrationInfo, RegistrationProduct
from app.services.auth.jwt import get_current_user
from app.schema.category import PersonalInfoDashboardResponse
import logging

logger = logging.getLogger(__name__)
admin_router=APIRouter(prefix="/admin", tags=["admin"])



class RegistrationApproval(BaseModel):
    status: str  # APPROVED or REJECTED
    remarks: str | None = None

@admin_router.post("/approve-registration/{user_id}")
async def approve_registration(
    user_id: int,
    approval: RegistrationApproval,
    role: UserRole = Depends(get_super_admin_role),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    try:
        result = await db.execute(
            Select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if approval.status not in ["APPROVED", "REJECTED"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be APPROVED or REJECTED")
        if approval.status == "APPROVED":
            user.retention_start_date = datetime.utcnow()
            
        if approval.status == "REJECTED":
            # Delete related data
            await db.execute("DELETE FROM registration_info WHERE user_id = %s", (user_id,))
            await db.execute("DELETE FROM registration_levels WHERE user_id = %s", (user_id,))
            await db.execute("DELETE FROM registration_products WHERE user_id = %s", (user_id,))
            await db.execute("DELETE FROM documents WHERE user_id = %s", (user_id,))
            await db.execute("DELETE FROM registration_agreements WHERE user_id = %s", (user_id,))
        
        user.is_registered = RegistrationStatus[approval.status]
        notification_message = (
            f"Your registration has been {approval.status.lower()}."
            f"{f' Remarks: {approval.remarks}' if approval.remarks else ''}"
        )
        
        notification = Notification(
            user_id=user.id,
            message=notification_message,
            created_at=datetime.utcnow(),
            is_read=False
        )
        
        db.add(user)
        db.add(notification)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Registration {approval.status.lower()} for user {user.email}: {notification_message}")
        return {
            "message": f"Registration {approval.status.lower()} successfully",
            "user_id": user.id,
            "email": user.email,
            "registration_status": user.is_registered.value,
            "remarks": approval.remarks
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing registration for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process registration: {str(e)}")



@admin_router.get("/users",response_model=list[UserDashboardResponse])
async def get_users(
    role:UserRole=Depends(get_super_admin_role),
    db:AsyncSession=Depends(get_db)
):
    if role not in [get_super_admin_role(),get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result=await db.execute(
            Select(User).filter(User.role not in [UserRole.super_admin, UserRole.sub_admin])
        )
        users=result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users:{str(e)}")
    
@admin_router.get("/document-info",response_model=list[DocumentResponse])
async def get_users(
    role:UserRole=Depends(get_super_admin_role),
    db:AsyncSession=Depends(get_db)
):
    if role not in [get_super_admin_role(),get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result=await db.execute(
            Select(Document) )
        users=result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users:{str(e)}")
    

@admin_router.get("/registrationinfo/{user_id}",response_model=PersonalInfoDashboardResponse)
async def get_user(user_id:int,role:UserRole=Depends(get_super_admin_role),db:AsyncSession=Depends(get_db)):

    if role not in [get_super_admin_role(),get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await db.execute(
            Select(RegistrationInfo).filter(RegistrationInfo.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User is not registered")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")
    
@admin_router.get("/user/{user_id}",response_model=UserDashboardResponse)
async def get_user(user_id:int,role:UserRole=Depends(get_super_admin_role),db:AsyncSession=Depends(get_db)):

    if role not in [get_super_admin_role(),get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await db.execute(
            Select().filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")
    


@admin_router.delete("/sub-admin/{user_id}",status_code=200)
async def delete_sub_admin(
    user_id:int,
    role:UserRole=Depends(get_super_admin_role),
    current_user:UserResponse=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    if role!=get_super_admin_role():
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        result=await db.execute(
            Select(User).filter(User.id==user_id,User.role==UserRole.sub_admin)
        )
        sub_admin=result.scalar_one_or_none()
        if not sub_admin:
            raise HTTPException(status_code=404, detail="Sub-admin not found")
        
        await db.delete(sub_admin)
        await db.commit()
        
        logger.info(f"Sub-admin {sub_admin.email} deleted by {current_user.email}")
        return {"message":"Sub-admin deleted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting sub-admin {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete sub-admin: {str(e)}")
    




@admin_router.post("/notifications", status_code=200, response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    current_user:UserResponse=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [get_super_admin_role(), get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        new_notification = Notification(
            admin_id=current_user.id,
            user_id=notification.user_id if notification.user_id else None,
            message=notification.message,
            target_type=notification.target_type,
            visibility=notification.visibility
        )
        db.add(new_notification)
        await db.commit()
        await db.refresh(new_notification)
        logger.info(f"Notification created by admin_id={current_user.id}: {notification.message}")
        return new_notification
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")


@admin_router.post("/documents/approve", response_model=DocumentResponse)
async def approve_document(
    request: DocumentApproveRequest,
    role: UserRole = Depends(get_super_admin_role),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:

        result = await db.execute(
            Select(Document).where(Document.id == request.document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document.ai_verification_status = VerificationStatus.PASS if request.approve else VerificationStatus.FAIL
        document.updated_at = func.now()
        
        # Notify user
        user_notification = Notification(
            admin_id=current_user.id,
            user_id=document.user_id,
            message=f"Your document {document.id} ({document.document_type}) has been {'approved' if request.approve else 'rejected'}.",
            target_type=NotificationTargetType.ALL_USERS,  
            visibility=True
        )
        db.add(user_notification)
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"Document {document.id} {'approved' if request.approve else 'rejected'} by admin_id={current_user.id}")
        return document
    except Exception as e:
        await db.rollback()
        logger.error(f"Error approving document {request.document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve document: {str(e)}")
    


@admin_router.get("/user-product_data/{user_id}", status_code=200)
async def get_user_product_data(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
     role: UserRole = Depends(get_super_admin_role),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            Select(RegistrationProduct).filter(RegistrationProduct.user_id == user_id)
        )
        data = result.scalar_one_or_none()
        if not data:
            raise HTTPException(status_code=404, detail="User Data not found")
        
        return{
            "product_data": data.product_data
        }
    except Exception as e:
        logger.error(f"Error fetching product data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch product data: {str(e)}")
    

@admin_router.post("/user-lateral/{user_id}", status_code=200)
async def mark_user_as_lateral(
    user_id: int,
    is_lateral: bool,
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role),
    db: AsyncSession = Depends(get_db)
):
    if role != get_super_admin_role():
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        result = await db.execute(
            Select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_lateral = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User {user.email} marked as {'lateral' if is_lateral else 'non-lateral'} by admin_id={current_user.id}")
        return {
            "message": f"User marked as {'lateral' if is_lateral else 'non-lateral'} successfully",
            "user_id": user.id,
            "email": user.email,
            "is_lateral": user.is_lateral
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking user {user_id} as lateral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark user as lateral: {str(e)}")
    



@admin_router.patch("/update-kpi-score", status_code=200)
async def update_kpi_score(
    user_id: int,
    kpi_score: int,
    current_user: UserResponse = Depends(get_current_user),
    role: UserRole = Depends(get_super_admin_role),
    db: AsyncSession = Depends(get_db)
):
    if role not in [get_super_admin_role(), get_sub_admin_role()]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(
            Select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user.is_registered != RegistrationStatus.APPROVED:
            raise HTTPException(status_code=404, detail="User not Registered")
        
        user.kpi_score = kpi_score
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"KPI score for document {user.id} updated to {kpi_score} by admin_id={current_user.id}")
        return {
            "message": "KPI score updated successfully"
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating KPI score for document {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update KPI score: {str(e)}")