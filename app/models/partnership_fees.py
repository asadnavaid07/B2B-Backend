from sqlalchemy import Column, Integer, Float, DateTime, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum
from app.core.database import Base
from enum import Enum as PyEnum

class PartnershipLevelGroup(PyEnum):
    """Four level groups as per document"""
    LEVEL_1 = "LEVEL_1"  # Core Trade: DROP_SHIPPING, CONSIGNMENT, WHOLESALE, IMPORT_EXPORT
    LEVEL_2 = "LEVEL_2"  # Brand Expansion: EXHIBITION, AUCTION, WHITE_LABEL, BRICK_MORTRAR
    LEVEL_3 = "LEVEL_3"  # Collaborative: DESIGN_COLLABORATION, STORYTELLING, WAREHOUSE, PACKAGING
    LEVEL_4 = "LEVEL_4"  # Technology: LOGISTICS, MUSEUM_INSTITUTIONAL, NGO_GOVERNMENT, TECHNOLOGY_PARTNERSHIP

class PartnershipFees(Base):
    __tablename__ = "partnership_fees"
    
    id = Column(Integer, primary_key=True, index=True)
    level_group = Column(SQLEnum(PartnershipLevelGroup), unique=True, nullable=False)
    registration_fee = Column(Float, nullable=False, default=0.0)  # Fee for moving to this level from lower level
    # DB column was created as `lateral_fee`; map explicitly to keep python attribute plural
    lateral_fees = Column(
        "lateral_fee",
        JSON,
        nullable=False,
        default={"1st": 0.0, "2nd": 0.0, "3rd": 0.0},
    )  # Fees for lateral tiers: {"1st": float, "2nd": float, "3rd": float}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

