from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User, UserRole
from app.schema.user import UserSignup, UserLogin, Token, SubAdminCreate, SubAdminUpdate, UserResponse
from app.core.security import get_password_hash, verify_password
from app.services.auth.jwt import create_access_token, create_refresh_token
from app.utils.email import send_otp_email
from datetime import timedelta
import logging
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
import logging
import os
import secrets
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

async def login_user(db: AsyncSession, user_login: UserLogin) -> Token:
    user = await authenticate_user(db, user_login.email, user_login.password)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not activated. Please verify OTP.")
    expires_delta_access = timedelta(hours=1)
    expires_delta_refresh = timedelta(days=7)
    access_token = create_access_token(
        email=user.email,
        user_id=user.id,
        role=user.role.value,
        visibility_level=user.visibility_level,
        ownership=user.ownership,
        expires_delta=expires_delta_access
    )
    refresh_token = create_refresh_token(
        email=user.email,
        user_id=user.id,
        role=user.role.value,
        visibility_level=user.visibility_level,
        ownership=user.ownership,
        expires_delta=expires_delta_refresh
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

async def register_user(db: AsyncSession, user: UserSignup, role: UserRole) -> UserResponse:
    try:
        # Check for existing users
        result = await db.execute(select(User).filter((User.email == user.email) | (User.username == user.username)))
        existing_users = result.scalars().all()  # Get all matching users
        if existing_users:
            for existing_user in existing_users:
                if existing_user.is_active:
                    logger.error(f"Active user found with email {user.email} or username {user.username}")
                    raise HTTPException(status_code=400, detail="Email or username already registered")
                else:
                    logger.info(f"Deleting unverified user {existing_user.email} (ID: {existing_user.id}) for retry")
                    await db.delete(existing_user)
            await db.commit()

        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            password_hash=hashed_password,
            role=role,
            is_active=False,
            visibility_level=1 if role == UserRole.sub_admin else None,
            ownership=None
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        # Send OTP
        try:
            if not await send_otp_email(user.email, db):
                await db.delete(db_user)
                await db.commit()
                logger.error(f"Failed to send OTP to {user.email}")
                raise HTTPException(status_code=500, detail="Failed to send OTP email")
            logger.info(f"User {user.email} registered, OTP sent")
        except HTTPException as e:
            await db.delete(db_user)
            await db.commit()
            logger.error(f"Error during OTP sending for {user.email}: {str(e)}")
            raise e
        
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            role=db_user.role,
            is_active=db_user.is_active,
            visibility_level=db_user.visibility_level,
            ownership=db_user.ownership
        )
    except Exception as e:
        logger.error(f"Error registering user {user.email}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

async def register_vendor(db: AsyncSession, user_data: UserSignup, role: UserRole = UserRole.vendor) -> UserResponse:
    result = await db.execute(select(User).filter((User.email == user_data.email) | (User.username == user_data.username)))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(status_code=400, detail="Email or username already registered")
        else:
            logger.info(f"Deleting unverified user {user_data.email} for retry")
            await db.delete(existing_user)
            await db.commit()

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        role=role,
        is_active=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    try:
        if not await send_otp_email(user_data.email, db):  # Pass db session
            await db.delete(new_user)
            await db.commit()
            logger.error(f"Failed to send OTP to {user_data.email}")
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
        logger.info(f"Vendor {user_data.email} registered, OTP sent")
    except HTTPException as e:
        await db.delete(new_user)
        await db.commit()
        logger.error(f"Error during OTP sending for {user_data.email}: {str(e)}")
        raise e
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
        visibility_level=new_user.visibility_level,
        ownership=new_user.ownership
    )

async def register_super_admin(db: AsyncSession, user_data: UserSignup, role: UserRole = UserRole.super_admin) -> UserResponse:
    result = await db.execute(select(User).filter((User.email == user_data.email) | (User.username == user_data.username)))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(status_code=400, detail="Email or username already registered")
        else:
            logger.info(f"Deleting unverified user {user_data.email} for retry")
            await db.delete(existing_user)
            await db.commit()

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        role=role,
        is_active=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    try:
        if not await send_otp_email(user_data.email, db):  # Pass db session
            await db.delete(new_user)
            await db.commit()
            logger.error(f"Failed to send OTP to {user_data.email}")
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
        logger.info(f"Super admin {user_data.email} registered, OTP sent")
    except HTTPException as e:
        await db.delete(new_user)
        await db.commit()
        logger.error(f"Error during OTP sending for {user_data.email}: {str(e)}")
        raise e
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
        visibility_level=new_user.visibility_level,
        ownership=new_user.ownership
    )

async def register_sub_admin(db: AsyncSession, user_data: SubAdminCreate, role: UserRole = UserRole.sub_admin) -> UserResponse:
    result = await db.execute(select(User).filter((User.email == user_data.email) | (User.username == user_data.username)))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(status_code=400, detail="Email or username already registered")
        else:
            logger.info(f"Deleting unverified user {user_data.email} for retry")
            await db.delete(existing_user)
            await db.commit()

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        role=role,
        visibility_level=user_data.visibility_level,
        ownership=user_data.ownership,
        is_active=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    try:
        if not await send_otp_email(user_data.email, db):  # Pass db session
            await db.delete(new_user)
            await db.commit()
            logger.error(f"Failed to send OTP to {user_data.email}")
            raise HTTPException(status_code=500, detail="Failed to send OTP email")
        logger.info(f"Sub-admin {user_data.email} registered, OTP sent")
    except HTTPException as e:
        await db.delete(new_user)
        await db.commit()
        logger.error(f"Error during OTP sending for {user_data.email}: {str(e)}")
        raise e
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
        visibility_level=new_user.visibility_level,
        ownership=new_user.ownership
    )

async def update_sub_admin(db: AsyncSession, user_id: int, user_update: SubAdminUpdate):
    try:
        result = await db.execute(select(User).filter(User.id == user_id, User.role == UserRole.sub_admin))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Sub-admin not found")
        if user_update.visibility_level is not None:
            user.visibility_level = user_update.visibility_level
        if user_update.ownership is not None:
            user.ownership = user_update.ownership
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

async def google_login(db: AsyncSession, token: str):
    email = None
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        logger.debug(f"Verifying ID token with client_id: {client_id[:10]}...")
        if not client_id:
            raise HTTPException(status_code=500, detail="Missing Google client ID")
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
        
        google_id = idinfo['sub']
        email = idinfo['email']
        username = idinfo.get('name', email.split('@')[0])
        
        result = await db.execute(select(User).filter((User.google_id == google_id) | (User.email == email)))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if not existing_user.is_active:
                logger.warning(f"Unverified user found for Google ID {google_id} or email {email}")
                raise HTTPException(status_code=400, detail="Account not verified. Please complete OTP verification.")
            logger.info(f"Existing user {email} logged in via Google")
            access_token = create_access_token(
                data={"sub": existing_user.email, "user_id": existing_user.id, "role": existing_user.role.value, 
                      "visibility_level": existing_user.visibility_level, "ownership": existing_user.ownership}
            )
            refresh_token = create_refresh_token(data={"sub": existing_user.email})
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "refresh_token": refresh_token,
                "user_role": existing_user.role.value,
                "user_id": existing_user.id,
                "visibility_level": existing_user.visibility_level,
                "ownership": existing_user.ownership
            }
        
        result = await db.execute(select(User).filter(User.username == username))
        existing_username = result.scalar_one_or_none()
        if existing_username and existing_username.is_active:
            username = f"{username}_{secrets.randbelow(1000)}"
        
        new_user = User(
            email=email,
            username=username,
            google_id=google_id,
            role=UserRole.buyer,
            is_active=True
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"New user {email} created via Google Sign-In")
        access_token = create_access_token(
            data={"sub": new_user.email, "user_id": new_user.id, "role": new_user.role.value, 
                  "visibility_level": new_user.visibility_level, "ownership": new_user.ownership}
        )
        refresh_token = create_refresh_token(data={"sub": new_user.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "user_role": new_user.role.value,
            "user_id": new_user.id,
            "visibility_level": new_user.visibility_level,
            "ownership": new_user.ownership
        }
    except ValueError as e:
        logger.error(f"Invalid Google ID token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        email_str = email if email else "unknown"
        logger.error(f"Error processing Google login for {email_str}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")

async def start_google_oauth():
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        logger.debug(f"Starting OAuth with client_id: {client_id[:10]}...")
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
        auth_url, state = flow.authorization_url(
            prompt="consent",
            include_granted_scopes="true"
        )
        logger.info(f"Redirecting to Google auth URL: {auth_url}")
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error starting Google OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start Google OAuth: {str(e)}")