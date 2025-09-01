from click import DateTime
from sqlalchemy import Column, Integer, Enum, JSON
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.registration import PartnershipLevel
from datetime import datetime

class PartnershipLevelModel(Base):
    __tablename__ = "partnership_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    partnership_name = Column(Enum(PartnershipLevel), unique=True, nullable=False)
    prices = Column(JSON, nullable=False)  # Stores {"1st": float, "2nd": float, "3rd": float}
