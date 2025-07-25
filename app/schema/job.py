from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Literal, Dict
from datetime import datetime, date
import enum




class JobCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True