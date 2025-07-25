# from pydantic import BaseModel, EmailStr, Field, validator
# from typing import Optional, List, Literal, Dict
# from datetime import datetime, date
# import enum




# # Job Schemas
# class JobCreate(BaseModel):
#     title: str = Field(..., min_length=1)
#     description: str = Field(..., min_length=1)

# class JobResponse(BaseModel):
#     id: int
#     title: str
#     description: str
#     created_by: int
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True

# # admin Schemas
# class adminCreate(BaseModel):
#     user_id: int
#     role: adminRole

# class adminResponse(BaseModel):
#     user_id: int
#     role: adminRole
#     created_at: datetime
#     user: UserResponse

#     class Config:
#         from_attributes = True

# # Dashboard Schema
# class DashboardStatusResponse(BaseModel):
#     registration_status: PlanStatus
#     plan_level: int
#     kpi_score: Optional[float]
#     retention_progress: Optional[float]

#     class Config:
#         from_attributes = True

# # Verification Schema
# class VerificationStatusResponse(BaseModel):
#     status: VerificationStatus
#     kpi_score: Optional[float]
#     remarks: Optional[str]

#     class Config:
#         from_attributes = True