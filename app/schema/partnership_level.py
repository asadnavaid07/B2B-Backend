from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from app.models import PartnershipLevel

class PartnershipLevelCreate(BaseModel):
    partnership_name: PartnershipLevel
    prices: Dict[str, str] 
class PartnershipLevelUpdate(BaseModel):
    partnership_name: Optional[PartnershipLevel] = None
    prices: Optional[Dict[str, str]] = None 

class PartnershipLevelResponse(BaseModel):
    id: int
    partnership_name: str
    prices: Dict[str, str]

    class Config:
        from_attributes = True