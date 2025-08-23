from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TeamMemberBase(BaseModel):
    name: str
    role: str

class TeamMemberCreate(TeamMemberBase):
    name: Optional[str] = None
    role: Optional[str] = None

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None

class TeamMemberResponse(BaseModel):
    id: int
    name: str
    role: str
    image_path: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: str
    description: str

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TeamResponse(BaseModel):
    id: int
    name: str
    description: str
    members: List[TeamMemberBase]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TeamFullResponse(TeamBase):
    id: int
    members: List[TeamMemberResponse]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True