from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.models.notification import NotificationTargetType

class NotificationCreate(BaseModel):
    message: str
    target_type: NotificationTargetType
    visibility: bool = True

class NotificationResponse(BaseModel):
    id: int
    admin_id: int
    message: str
    target_type: str
    visibility: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True