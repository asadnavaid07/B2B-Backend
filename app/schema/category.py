from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Literal, Dict
from datetime import datetime, date
import enum



class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True

class ProductCategoryCreate(BaseModel):
    category_id: int

class ProductCategoryResponse(BaseModel):
    user_id: int
    category_id: int
    category: CategoryResponse

    class Config:
        from_attributes = True