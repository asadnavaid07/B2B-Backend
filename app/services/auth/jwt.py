from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from app.models.user import RegistrationStatus
from app.schema.user import UserResponse
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(
    username: str,
    email: str,
    user_id: int,
    role: str,
    visibility_level: Optional[int] = None,
    ownership: Optional[Dict[str, List[str]]] = None,
    expires_delta: timedelta = None,
    is_registered: RegistrationStatus = RegistrationStatus.PENDING,
    registration_step: int = 0,
    first_register: bool = False,
):
    # 🔹 Default: 15 minutes for access tokens
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))

    to_encode = {
        "username": username,
        "sub": email,
        "user_id": user_id,
        "role": role,
        "exp": expire,
    }

    if visibility_level is not None:
        to_encode["visibility_level"] = visibility_level
    if ownership is not None:
        to_encode["ownership"] = ownership

    if role in ["buyer", "vendor"]:
        to_encode["is_registered"] = is_registered.value
        to_encode["registration_step"] = registration_step
        to_encode["first_register"] = first_register

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    username: str,
    email: str,
    user_id: int,
    role: str,
    visibility_level: Optional[int] = None,
    ownership: Optional[Dict[str, List[str]]] = None,
    expires_delta: timedelta = None,
    is_registered: RegistrationStatus = RegistrationStatus.PENDING,
    registration_step: int = 0,
    first_register: bool = False,
):
    # 🔹 Default: 7 days for refresh tokens
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))

    to_encode = {
        "username": username,
        "sub": email,
        "user_id": user_id,
        "role": role,
        "exp": expire,
    }

    if visibility_level is not None:
        to_encode["visibility_level"] = visibility_level
    if ownership is not None:
        to_encode["ownership"] = ownership

    if role in ["buyer", "vendor"]:
        to_encode["is_registered"] = is_registered.value
        to_encode["registration_step"] = registration_step
        to_encode["first_register"] = first_register

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def role_required(*allowed_roles: str):
    async def verify_token(token: str = Depends(oauth2_scheme)) -> UserResponse:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username:str = payload.get("username")
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            role: str = payload.get("role")
            visibility_level: Optional[int] = payload.get("visibility_level")
            ownership: Optional[Dict[str, List[str]]] = payload.get("ownership")

            
            if email is None or user_id is None or role is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            if role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Insufficient role permissions")
            
            if role == "sub_admin":
                if visibility_level is None:
                    raise HTTPException(status_code=403, detail="Sub-admin requires visibility level")
                if visibility_level < 3 and any(r in ["super_admin"] for r in allowed_roles):
                    raise HTTPException(status_code=403, detail="Insufficient visibility level")
            
            return UserResponse(
                id=user_id,
                username=username,  
                email=email,
                role=role,
                is_active=True,
                visibility_level=visibility_level,
                ownership=ownership)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    return verify_token


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username:str = payload.get("username")
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        visibility_level: Optional[int] = payload.get("visibility_level")
        ownership: Optional[Dict[str, List[str]]] = payload.get("ownership")
        is_registered: Optional[str] = payload.get("is_registered")
        registration_step: Optional[int] = payload.get("registration_step")
        first_register: Optional[bool] = payload.get("first_register", False)
        
        if email is None or user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return UserResponse(
            id=user_id,
            username=username,  
            email=email,
            role=role,
            is_active=True,
            visibility_level=visibility_level,
            ownership=ownership,
            is_registered=is_registered,
            registration_step=registration_step,
            first_register=first_register
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")