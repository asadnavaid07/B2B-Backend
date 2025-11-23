from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from app.models.partnership_fees import PartnershipLevelGroup

class PartnershipFeesCreate(BaseModel):
    level_group: PartnershipLevelGroup
    registration_fee: float
    lateral_fees: Dict[str, float] = Field(..., description="Lateral fees for each tier: {'1st': float, '2nd': float, '3rd': float}")

class PartnershipFeesUpdate(BaseModel):
    registration_fee: Optional[float] = None
    lateral_fees: Optional[Dict[str, float]] = Field(None, description="Lateral fees for each tier: {'1st': float, '2nd': float, '3rd': float}")

class PartnershipFeesResponse(BaseModel):
    id: int
    level_group: str
    registration_fee: float
    lateral_fees: Dict[str, float]  # {"1st": float, "2nd": float, "3rd": float}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

