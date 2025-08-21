from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from app.models.registration import PartnershipLevel

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

# Pydantic Schemas
class LevelSelection(BaseModel):
    levels: List[PartnershipLevel]
    is_lateral: bool = False

class PersonalInfo(BaseModel):
    # Business Details
    business_name: str = Field(..., min_length=2, max_length=255)
    business_legal_structure: str = Field(..., max_length=100)
    business_type: str = Field(..., max_length=100)
    year_established: Optional[int] = Field(None, ge=1800, le=2025)
    business_registration_number: str = Field(..., max_length=100)
    brand_affiliations: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=255)
    annual_turnover: Optional[str] = Field(None, max_length=100)
    # Tax & Registration Information
    gst_number: str = Field(..., max_length=100)
    tax_identification_number: str = Field(..., max_length=100)
    import_export_code: Optional[str] = Field(None, max_length=100)
    # Business Address
    street_address_1: str = Field(..., max_length=255)
    street_address_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state_region: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(..., max_length=100)
    # Contact Person
    contact_person_name: str = Field(..., min_length=2, max_length=255)
    contact_email: str = Field(..., max_length=255)
    contact_phone: str = Field(..., max_length=50)
    contact_whatsapp: Optional[str] = Field(None, max_length=50)
    # Contact Person Address
    contact_district: str = Field(..., max_length=100)
    contact_pin_code: str = Field(..., max_length=20)
    contact_state: str = Field(..., max_length=100)
    contact_country: str = Field(..., max_length=100)
    # Credibility Assessment
    material_standard: Optional[int] = Field(None, ge=1, le=5)
    quality_level: Optional[int] = Field(None, ge=1, le=5)
    sustainability_level: Optional[int] = Field(None, ge=1, le=5)
    service_level: Optional[int] = Field(None, ge=1, le=5)
    standards_level: Optional[int] = Field(None, ge=1, le=5)
    ethics_level: Optional[int] = Field(None, ge=1, le=5)
    certifications: Optional[List[str]] = Field(None)
    # Banking Information
    bank_name: str = Field(..., max_length=255)
    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=100)
    ifsc_code: str = Field(..., max_length=50)
    swift_bis_code: Optional[str] = Field(None, max_length=50)
    iban_code: Optional[str] = Field(None, max_length=50)
    # Regulatory Challenges
    kyc_challenges: bool = False
    gst_compliance_issues: bool = False
    fema_payment_issues: bool = False
    digital_banking_issues: bool = False
    fraud_cybersecurity_issues: bool = False
    payment_gateway_compliance_issues: bool = False
    account_activity_issues: bool = False
    regulatory_actions: bool = False

    @validator("certifications")
    def validate_certifications(cls, v):
        allowed_certs = [
            "GI Certification", "Handloom Mark", "Craft Mark", "India Handmade",
            "Quality Council", "Export Council", "Blockchain"
        ]
        if v:
            for cert in v:
                if cert not in allowed_certs:
                    raise ValueError(f"Invalid certification: {cert}. Must be one of {allowed_certs}")
        return v

class ProductData(BaseModel):
    name: str = Field(..., max_length=255)
    category_id: int = Field(...)  # References Category.id
    attributes: Dict = Field(...)  # Category-specific attributes

    @validator("attributes")
    def validate_attributes(cls, v, values):
        if "category_id" not in values:
            raise ValueError("Category ID must be specified before attributes")
        return v

class ProductCatalog(BaseModel):
    products: List[ProductData]

class AgreementConfirmation(BaseModel):
    agreement_signed: bool = True
    agreement_url: Optional[str] = None


class PersonalInfoDashboardResponse(BaseModel):
    # Business Summary
    business_name: str
    business_type: str
    year_established: Optional[int]
    website: Optional[str]
    annual_turnover: Optional[str]

    # Location
    city: str
    state_region: str
    country: str

    # Contact Person (basic info only)
    contact_person_name: str
    contact_email: str
    contact_phone: str

    # Credibility Snapshot
    certifications: Optional[List[str]]
    material_standard: Optional[int]
    quality_level: Optional[int]
    sustainability_level: Optional[int]
    service_level: Optional[int]
    standards_level: Optional[int]
    ethics_level: Optional[int]

    # Compliance / Risk Indicators (flags only)
    kyc_challenges: bool
    gst_compliance_issues: bool
    fema_payment_issues: bool
    fraud_cybersecurity_issues: bool
    regulatory_actions: bool