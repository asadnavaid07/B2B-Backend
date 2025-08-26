from sqlalchemy import Column, Integer, String, JSON, Boolean, ForeignKey, Enum, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
import enum
from datetime import datetime


class PartnershipLevel(enum.Enum):
    DROP_SHIPPING = "DROP_SHIPPING"
    CONSIGNMENT = "CONSIGNMENT"
    IMPORT_EXPORT = "IMPORT_EXPORT"
    WHOLESALE = "WHOLESALE"
    EXHIBITION = "EXHIBITION"
    AUCTION = "AUCTION"
    WHITE_LABEL = "WHITE_LABEL"
    BRICK_MORTAR = "BRICK_MORTAR"
    DESIGN_COLLABORATION = "DESIGN_COLLABORATION"
    STORYTELLING = "STORYTELLING"
    WAREHOUSE = "WAREHOUSE"
    PACKAGING = "PACKAGING"
    LOGISTICS = "LOGISTICS"
    MUSEUM_INSTITUTIONAL = "MUSEUM_INSTITUTIONAL"
    NGO_GOVERNMENT = "NGO_GOVERNMENT"
    TECHNOLOGY_PARTNERSHIP = "TECHNOLOGY_PARTNERSHIP"


class RegistrationLevel(Base):
    __tablename__ = "registration_levels"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    level = Column(Enum(PartnershipLevel), nullable=False)
    is_lateral = Column(Boolean, default=False)
    payment_status = Column(String(50), default="pending")
    verification_status = Column(String(50), default="pending")
    retention_period_months = Column(Integer, nullable=False)
    kpi_threshold = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RegistrationInfo(Base):
    __tablename__ = "registration_info"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Business Details
    business_name = Column(String(255), nullable=False)
    business_legal_structure = Column(String(100), nullable=False)
    business_type = Column(String(100), nullable=False)
    year_established = Column(Integer)
    business_registration_number = Column(String(100), nullable=False)
    brand_affiliations = Column(String(500))
    website = Column(String(255))
    annual_turnover = Column(String(100))
    # Tax & Registration Information
    gst_number = Column(String(100), nullable=False)
    tax_identification_number = Column(String(100), nullable=False)
    import_export_code = Column(String(100))
    # Business Address
    street_address_1 = Column(String(255), nullable=False)
    street_address_2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state_region = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    # Contact Person
    contact_person_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_whatsapp = Column(String(50))
    # Contact Person Address
    contact_district = Column(String(100), nullable=False)
    contact_pin_code = Column(String(20), nullable=False)
    contact_state = Column(String(100), nullable=False)
    contact_country = Column(String(100), nullable=False)
    # Credibility Assessment
    material_standard = Column(Integer)
    quality_level = Column(Integer)
    sustainability_level = Column(Integer)
    service_level = Column(Integer)
    standards_level = Column(Integer)
    ethics_level = Column(Integer)
    certifications = Column(JSONB)
    # Banking Information
    bank_name = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(100), nullable=False)
    account_number = Column(String(100), nullable=False)
    ifsc_code = Column(String(50), nullable=False)
    swift_bis_code = Column(String(50))
    iban_code = Column(String(50))
    # Regulatory Challenges
    kyc_challenges = Column(Boolean, default=False)
    gst_compliance_issues = Column(Boolean, default=False)
    fema_payment_issues = Column(Boolean, default=False)
    digital_banking_issues = Column(Boolean, default=False)
    fraud_cybersecurity_issues = Column(Boolean, default=False)
    payment_gateway_compliance_issues = Column(Boolean, default=False)
    account_activity_issues = Column(Boolean, default=False)
    regulatory_actions = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RegistrationProduct(Base):
    __tablename__ = "registration_products"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_data = Column(JSONB, nullable=False)  # Stores categoryId, categoryName, subcategoryId, subcategoryName, specifications
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RegistrationAgreement(Base):
    __tablename__ = "registration_agreements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agreement_signed = Column(Boolean, nullable=False, default=False)
    agreement_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())