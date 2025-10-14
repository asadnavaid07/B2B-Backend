import base64
import os
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from jose import jwt
from app.models.otp import OTP
load_dotenv()
from jose import JWTError
from pydantic import BaseModel
from app.core.security import get_password_hash, verify_password
from app.services.auth.jwt import create_access_token, create_refresh_token, role_required
from app.utils.email import send_otp_email, verify_otp_code
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schema.user import SubAdminResponse, UserSignup, UserLogin, Token, UserResponse, SubAdminCreate, SubAdminUpdate
from app.services.auth.auth_service import register_user, register_vendor, register_super_admin, register_sub_admin, update_sub_admin, login_user, google_login, start_google_oauth
from datetime import timedelta
import logging
from google.oauth2 import id_token  # Added import
from google.auth.transport import requests
from app.schema.user import GoogleLoginRequest, RefreshTokenRequest, ResendOTPRequest, get_buyer_role, get_vendor_role, get_super_admin_role, get_sub_admin_role


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix=("/auth"),tags=["auth"])


@auth_router.post("/signup", response_model=UserResponse)
async def signup(
    user: UserSignup,
    role: UserRole = Depends(get_buyer_role),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Signup payload: {user.dict()}, role: {role}")
    return await register_user(db, user, role)

@auth_router.post("/register-supplier", response_model=UserResponse)
async def register_supplier_endpoint(
    user: UserSignup,
    role: UserRole = Depends(get_vendor_role),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Register-supplier payload: {user.dict()}, role: {role}")
    return await register_vendor(db, user, role)

# @auth_router.post("/register-super-admin", response_model=UserResponse)
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


@auth_router.post("/register-sub-admin", response_model=SubAdminResponse)
async def register_sub_admin_endpoint(
    user: SubAdminCreate,
    role: UserRole = Depends(get_sub_admin_role),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin"))
):
    logger.debug(f"Register-sub-admin payload: {user.dict()}, role: {role}")
    return await register_sub_admin(db, user, role)

@auth_router.put("/update-sub-admin/{user_id}", response_model=UserResponse)
async def update_sub_admin_endpoint(
    user_id: int,
    user_update: SubAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(role_required("super_admin"))
):
    logger.debug(f"Update-sub-admin payload: {user_update.dict()}, user_id: {user_id}")
    return await update_sub_admin(db, user_id, user_update)


@auth_router.post("/verify/otp", response_model=Token)
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
        username=user.username,
        email=user.email,
        user_id=user.id,
        role=user.role.value,
        visibility_level=user.visibility_level,
        ownership=user.ownership,
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        username=user.username,
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

@auth_router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Login payload: {user.dict()}")
    return await login_user(db, user)

@auth_router.post("/forgot/password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Forgot password for email: {email}")
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not await send_otp_email(email, db):  # Pass db session
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    return {"message": "Password reset OTP sent to email"}

@auth_router.post("/reset-password")
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

@auth_router.post("/change-password")
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

@auth_router.post("/logout")
async def logout(current_user: UserResponse = Depends(role_required("vendor", "buyer", "super_admin", "sub_admin"))):
    logger.debug(f"Logout for user_id: {current_user.id}")
    return {"message": "Logged out successfully"}


@auth_router.post("/google-login")
async def google_login_endpoint(request: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    if not request.id_token:
        logger.error("No id_token provided in request")
        raise HTTPException(status_code=400, detail="Missing id_token")
    logger.debug(f"Processing Google login with ID token for role: {request.role}")
    return await google_login(db, request.id_token, request.role)

from fastapi.responses import RedirectResponse
import json

@auth_router.get("/google-auth")
async def google_auth_endpoint(role: str):
    logger.debug(f"Starting Google OAuth flow with role: {role}")
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        logger.debug(f"Starting OAuth with client_id: {client_id[:10]}...")
        logger.debug(f"Client secret present: {bool(client_secret)}")
        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Missing Google client credentials")

        # Validate role
        try:
            requested_role = UserRole(role.lower())
            if requested_role not in [UserRole.buyer, UserRole.vendor]:
                raise ValueError("Invalid role")
        except ValueError:
            logger.error(f"Invalid role provided: {role}")
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'buyer' or 'vendor'")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["https://api.b2b.dekoshurcrafts.com/auth/google-callback"]
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
        )
        flow.redirect_uri = "https://api.b2b.dekoshurcrafts.com/auth/google-callback"
        # Encode role in the state parameter
        state = json.dumps({"role": role})
        auth_url, state = flow.authorization_url(
            prompt="consent",
            include_granted_scopes="true",
            access_type="offline",
            state=state
        )
        logger.info(f"Redirecting to Google auth URL: {auth_url}")
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error starting Google OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start Google OAuth: {str(e)}")
    


@auth_router.get("/google-callback")
async def google_callback_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code:
        logger.error("Missing authorization code in Google callback")
        raise HTTPException(status_code=400, detail="Missing authorization code")
    if not state:
        logger.error("Missing state parameter in Google callback")
        raise HTTPException(status_code=400, detail="Missing state parameter")

    try:
        # Decode the state to extract the role
        state_data = json.loads(state)
        role = state_data.get("role")
        if not role:
            logger.error("No role found in state parameter")
            raise HTTPException(status_code=400, detail="Missing role in state")
        
        # Validate role
        try:
            requested_role = UserRole(role.lower())
            if requested_role not in [UserRole.buyer, UserRole.vendor]:
                raise ValueError("Invalid role")
        except ValueError:
            logger.error(f"Invalid role in state: {role}")
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'buyer' or 'vendor'")

        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Missing Google client credentials")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["https://api.b2b.dekoshurcrafts.com/auth/google-callback"]
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
        )
        flow.redirect_uri = "https://api.b2b.dekoshurcrafts.com/auth/google-callback"
        logger.debug(f"Fetching token with code: {code[:10]}...")
        flow.fetch_token(code=code)
        credentials = flow.credentials
        logger.debug(f"Credentials received: id_token={bool(credentials.id_token)}")

        # Get the auth data from google_login
        auth_data: Dict[str, Any] = await google_login(db, credentials.id_token, role)
        

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000") 
        
        redirect_target = f"{frontend_url}/auth/callback?{auth_data}"  
        
        logger.info(f"Redirecting to frontend with auth data: {redirect_target}")
        return RedirectResponse(redirect_target, status_code=302)  
        
    except json.JSONDecodeError:
        logger.error("Invalid state parameter format")
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")    
    


@auth_router.post("/refresh-token", response_model=Token)
async def refresh_token_endpoint(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    logger.debug("Processing refresh token request")
    try:
        payload = jwt.decode(request.refresh_token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        visibility_level: Optional[int] = payload.get("visibility_level")
        ownership: Optional[dict] = payload.get("ownership")
        
        if not email or not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        result = await db.execute(select(User).filter(User.id == user_id, User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account not activated")
        
        access_token = create_access_token(
            username=user.username,
            email=user.email,
            user_id=user.id,
            role=user.role.value,
            visibility_level=user.visibility_level,
            ownership=user.ownership,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            username=user.username,
            email=user.email,
            user_id=user.id,
            role=user.role.value,
            visibility_level=user.visibility_level,
            ownership=user.ownership,
            expires_delta=timedelta(days=7)
        )
        logger.info(f"Token refreshed for user {email}")
        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user_role=user.role.value,
            user_id=user.id,
            visibility_level=user.visibility_level,
            ownership=user.ownership
        )
    except JWTError as e:
        logger.error(f"Invalid refresh token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")
    

@auth_router.post("/resend-otp")
async def resend_otp(request: ResendOTPRequest, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Resend OTP for email: {request.email}")
    result = await db.execute(select(User).filter(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_active:
        raise HTTPException(status_code=400, detail="Account already activated")
    
    if not await send_otp_email(request.email, db):
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    return {"message": "OTP resent successfully"}


