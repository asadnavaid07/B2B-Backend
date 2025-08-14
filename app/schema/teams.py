from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TeamMemberBase(BaseModel):
    name: str
    role: str
    bio: Optional[str] = None

class TeamMemberCreate(TeamMemberBase):
    image: Optional[str] = None  # Will be handled by file upload

class TeamMemberUpdate(TeamMemberBase):
    name: Optional[str] = None
    role: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None

class TeamMemberResponse(TeamMemberBase):
    id: int
    team_id: int
    image: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(TeamBase):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberResponse] = []
    sub_teams: List['TeamResponse'] = []

    class Config:
        orm_mode = True