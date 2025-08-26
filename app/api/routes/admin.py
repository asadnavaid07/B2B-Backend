from datetime import datetime
from fastapi import APIRouter,Depends, HTTPException, logger
from pydantic import BaseModel
from sqlalchemy import Select
from app.models.document import Document
from app.models.notification import Notification
from app.schema.document import DocumentResponse
from app.schema.user import UserDashboardResponse, UserRole,get_super_admin_role,get_sub_admin_role,UserResponse
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import RegistrationStatus, User
from app.models.registration import RegistrationInfo
from app.services.auth.jwt import get_current_user
from app.schema.category import PersonalInfoDashboardResponse
import logging

logger = logging.getLogger(__name__)
admin_router=APIRouter(prefix="/admin", tags=["admin"])

# class KPIDetails(BaseModel):
#     quality: float
#     integrity: float
#     child_labour: float
#     artisan: float
#     certification: float
#     media: float
#     packaging: float
#     sourcing: float
#     carbon: float
#     hcrf: float
#     artstay: float

class RegistrationApproval(BaseModel):
    status: str  # APPROVED or REJECTED
    remarks: str | None = None

# @admin_router.post("/assign-kpi/{document_id}")
# async def assign_kpi_scores(
#     document_id: int,
#     kpi_details: KPIDetails,
#     current_user: UserResponse = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Admin access required")
    
#     try:
#         result = await db.execute(
#             select(Document).filter(Document.id == document_id)
#         )
#         doc = result.scalar_one_or_none()
#         if not doc:
#             raise HTTPException(status_code=404, detail="Document not found")
        
#         if doc.kpi_details is None:
#             doc.kpi_details = {}
        
#         doc.kpi_details.update({
#             "product_integrity": {
#                 "quality": kpi_details.quality,
#                 "integrity": kpi_details.integrity,
#                 "child_labour": kpi_details.child_labour,
#                 "artisan": kpi_details.artisan,
#                 "certification": kpi_details.certification,
#                 "availability": doc.kpi_details.get("product_integrity", {}).get("availability", 0)
#             },
#             "technology_integration": {
#                 "inventory": doc.kpi_details.get("technology_integration", {}).get("inventory", 0),
#                 "blockchain": doc.kpi_details.get("technology_integration", {}).get("blockchain", 0),
#                 "media": kpi_details.media
#             },
#             "ethical_sustainability": {
#                 "packaging": kpi_details.packaging,
#                 "sourcing": kpi_details.sourcing,
#                 "carbon": kpi_details.carbon
#             },
#             "ecosystem_engagement": {
#                 "craftlore": doc.kpi_details.get("ecosystem_engagement", {}).get("craftlore", 0),
#                 "hcrf": kpi_details.hcrf,
#                 "artstay": kpi_details.artstay
#             }
#         })
        
#         doc.ai_kpi_score = sum(sum(category.values()) for category in doc.kpi_details.values())
#         doc.ai_verification_status = VerificationStatus.PASS
#         doc.ai_remarks = "Admin-assigned KPI scores"
        
#         db.add(doc)
#         await db.commit()
        
#         logger.info(f"Admin assigned KPI scores for document {document_id}: {doc.kpi_details}")
#         return {"message": "KPI scores assigned successfully", "kpi_details": doc.kpi_details}
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Error assigning KPI scores for document {document_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to assign KPI scores: {str(e)}")

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

    

