from fastapi import HTTPException, status,Depends
from app.models.user import User
from app.schema.user import UserResponse
from  app.services.auth.jwt import get_current_user

def role_required(required_roles: list[str]):
    def dependency(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return dependency
