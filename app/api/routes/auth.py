import os
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel
from app.core.security import get_password_hash, verify_password
from app.services.auth.jwt import create_access_token, create_refresh_token, role_required
from app.utils.email import send_otp_email, verify_otp_code
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schema.user import UserSignup, UserLogin, Token, UserResponse, SubAdminCreate, SubAdminUpdate
from app.services.auth.auth_service import register_user, register_vendor, register_super_admin, register_sub_admin, update_sub_admin, login_user, google_login, start_google_oauth
from datetime import timedelta
import logging

from google.oauth2 import id_token  # Added import
from google.auth.transport import requests


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class GoogleLoginRequest(BaseModel):
    id_token: str
    
def get_buyer_role() -> UserRole:
    return UserRole.buyer

def get_vendor_role() -> UserRole:
    return UserRole.vendor

def get_super_admin_role() -> UserRole:
    return UserRole.super_admin

def get_sub_admin_role() -> UserRole:
    return UserRole.sub_admin

@router.post("/signup", response_model=UserResponse)
async def signup(
    user: UserSignup,
    role: UserRole = Depends(get_buyer_role),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Signup payload: {user.dict()}, role: {role}")
    return await register_user(db, user, role)

@router.post("/register-supplier", response_model=UserResponse)
async def register_supplier_endpoint(
    user: UserSignup,
    role: UserRole = Depends(get_vendor_role),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Register-supplier payload: {user.dict()}, role: {role}")
    return await register_vendor(db, user, role)

# @router.post("/register-super-admin", response_model=UserResponse)
# async def register_super_admin_endpoint(
#     user: UserSignup,
#     role: UserRole = Depends(get_super_admin_role),
#     db: AsyncSession = Depends(get_db)
# ):
#     # Check if any super admin exists
#     result = await db.execute(select(User).filter(User.role == UserRole.super_admin))
#     existing_super_admin = result.scalar_one_or_none()
#     if existing_super_admin:
#         # If a super admin exists, require authentication (optional: add role_required("super_admin"))
#         from app.core.security import role_required
#         current_user = Depends(get_super_admin_role)
#         logger.debug(f"Existing super admin found: {existing_super_admin.email}. Authentication required.")
#     else:
#         logger.debug("No super admin exists. Allowing unauthenticated super admin creation.")
    
#     logger.debug(f"Register-super-admin payload: {user.dict()}, role: {role}")
#     return await register_super_admin(db, user, role)


@router.post("/register-sub-admin", response_model=UserResponse)
async def register_sub_admin_endpoint(
    user: SubAdminCreate,
    role: UserRole = Depends(get_sub_admin_role),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin"))
):
    logger.debug(f"Register-sub-admin payload: {user.dict()}, role: {role}")
    return await register_sub_admin(db, user, role)

@router.put("/update-sub-admin/{user_id}", response_model=UserResponse)
async def update_sub_admin_endpoint(
    user_id: int,
    user_update: SubAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin"))
):
    logger.debug(f"Update-sub-admin payload: {user_update.dict()}, user_id: {user_id}")
    return await update_sub_admin(db, user_id, user_update)


@router.post("/verify/otp", response_model=Token)
async def verify_otp(email: str, otp: str, db: AsyncSession = Depends(get_db)):
    # Strip quotes from OTP
    clean_otp = otp.strip('"')
    logger.debug(f"Verify OTP for email: {email}, otp: {clean_otp}")
    if not await verify_otp_code(email, clean_otp, db):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_active:
        raise HTTPException(status_code=400, detail="Account already activated")
    
    user.is_active = True
    db.add(user)
    await db.commit()
    
    access_token = create_access_token(
        email=user.email,
        user_id=user.id,
        role=user.role.value,
        visibility_level=user.visibility_level,
        ownership=user.ownership,
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        email=user.email,
        user_id=user.id,
        role=user.role.value,
        visibility_level=user.visibility_level,
        ownership=user.ownership,
        expires_delta=timedelta(days=7)
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        user_role=user.role.value,
        user_id=user.id,
        visibility_level=user.visibility_level,
        ownership=user.ownership
    )

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Login payload: {user.dict()}")
    return await login_user(db, user)

@router.post("/forgot/password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Forgot password for email: {email}")
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not await send_otp_email(email, db):  # Pass db session
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    return {"message": "Password reset OTP sent to email"}

@router.post("/reset-password")
async def reset_password(email: str, otp: str, new_password: str, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Reset password for email: {email}, otp: {otp}")
    if not await verify_otp_code(email, otp,db):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    await db.commit()
    return {"message": "Password reset successfully"}

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: UserResponse = Depends(role_required("vendor", "buyer", "super_admin", "sub_admin")),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Change password for user_id: {current_user.id}")
    result = await db.execute(select(User).filter(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user or not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid current password")
    
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    await db.commit()
    return {"message": "Password changed successfully"}

@router.post("/logout")
async def logout(current_user: UserResponse = Depends(role_required("vendor", "buyer", "super_admin", "sub_admin"))):
    logger.debug(f"Logout for user_id: {current_user.id}")
    return {"message": "Logged out successfully"}


@router.post("/google-login")
async def google_login_endpoint(request: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    if not request.id_token:
        logger.error("No id_token provided in request")
        raise HTTPException(status_code=400, detail="Missing id_token")
    logger.debug(f"Processing Google login with ID token")
    return await google_login(db, request.id_token)

@router.get("/google-auth")
async def google_auth_endpoint():
    logger.debug("Starting Google OAuth flow")
    return await start_google_oauth()

@router.get("/google-callback")
async def google_callback_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Processing Google OAuth callback: {request.query_params}")
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        logger.debug(f"Using client_id: {client_id[:10]}... for OAuth flow")
        logger.debug(f"Client secret present: {bool(client_secret)}")
        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Missing Google client credentials")
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8000/auth/google-callback"]
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
        )
        flow.redirect_uri = "http://localhost:8000/auth/google-callback"
        logger.debug(f"Fetching token with code: {code[:10]}...")
        flow.fetch_token(code=code)
        credentials = flow.credentials
        logger.debug(f"Credentials received: id_token={bool(credentials.id_token)}")
        return await google_login(db, credentials.id_token)
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")