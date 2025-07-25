from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from app.schema.user import UserResponse
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(email: str, user_id: int, role: str, visibility_level: Optional[int] = None, ownership: Optional[Dict[str, List[str]]] = None, expires_delta: timedelta = None):
    to_encode = {"sub": email, "user_id": user_id, "role": role}
    if visibility_level is not None:
        to_encode["visibility_level"] = visibility_level
    if ownership is not None:
        to_encode["ownership"] = ownership
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(email: str, user_id: int, role: str, visibility_level: Optional[int] = None, ownership: Optional[Dict[str, List[str]]] = None, expires_delta: timedelta = None):
    to_encode = {"sub": email, "user_id": user_id, "role": role}
    if visibility_level is not None:
        to_encode["visibility_level"] = visibility_level
    if ownership is not None:
        to_encode["ownership"] = ownership
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def role_required(*allowed_roles: str):
    async def verify_token(token: str = Depends(oauth2_scheme)) -> UserResponse:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
                # Example: Restrict sub_admin access based on visibility_level
                if visibility_level < 3 and any(r in ["super_admin"] for r in allowed_roles):
                    raise HTTPException(status_code=403, detail="Insufficient visibility level")
            
            return UserResponse(
                id=user_id,
                username=email,  # Adjust based on actual username retrieval
                email=email,
                role=role,
                is_active=True,
                visibility_level=visibility_level,
                ownership=ownership
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    return verify_token