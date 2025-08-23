from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobBase(BaseModel):
    title: str
    location: str
    type: str
    summary: str
    description: str
    requirements: str
    salary_range: Optional[str] = None
    application_deadline: Optional[datetime] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = None
    application_deadline: Optional[datetime] = None

class JobResponse(BaseModel):
    id: int
    title: str
    location: str
    type: str
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True

class JobFullResponse(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime
    posted_by: int

    class Config:
        from_attributes = True