from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.registration import RegistrationLevel, RegistrationInfo, RegistrationProduct, RegistrationAgreement, PartnershipLevel
from app.models.categories import ProductCategory, Category
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union
import logging
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
from app.utils.categories import PRODUCT_CATEGORIES
from app.schema.category import LevelSelection, PersonalInfo, ProductCatalog, AgreementConfirmation
load_dotenv()
logger = logging.getLogger(__name__)


registration_router = APIRouter(prefix="/registration", tags=["registration"])



async def verify_khrcf(email: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://khrcf.org/api/verify",
                json={"email": email},
                timeout=10
            )
            if response.status_code == 200 and response.json().get("verified"):
                logger.info(f"khrcf.org verification successful for {email}")
                return True
            logger.warning(f"khrcf.org verification failed for {email}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error verifying with khrcf.org for {email}: {str(e)}")
        return False

async def process_payment(email: str, amount: float) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://mock-payment-gateway.com/process",
                json={"email": email, "amount": amount, "currency": "USD"},
                timeout=10
            )
            if response.status_code == 200 and response.json().get("status") == "success":
                logger.info(f"Payment successful for {email}: ${amount}")
                return True
            logger.warning(f"Payment failed for {email}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Payment error for {email}: {str(e)}")
        return False

# Partnership Level Requirements
LEVEL_REQUIREMENTS = {
    PartnershipLevel.DROP_SHIPPING: {"retention_months": 0, "kpi_threshold": 7.0},
    PartnershipLevel.CONSIGNMENT: {"retention_months": 18, "kpi_threshold": 7.0},
    PartnershipLevel.IMPORT_EXPORT: {"retention_months": 6, "kpi_threshold": 8.0},
    PartnershipLevel.WHOLESALE: {"retention_months": 3, "kpi_threshold": 7.0},
    PartnershipLevel.EXHIBITION: {"retention_months": 6, "kpi_threshold": 8.0},
    PartnershipLevel.AUCTION: {"retention_months": 6, "kpi_threshold": 8.0},
    PartnershipLevel.WHITE_LABEL: {"retention_months": 12, "kpi_threshold": 9.0},
    PartnershipLevel.BRICK_MORTAR: {"retention_months": 12, "kpi_threshold": 9.0},
    PartnershipLevel.DESIGN_COLLABORATION: {"retention_months": 6, "kpi_threshold": 8.0},
    PartnershipLevel.STORYTELLING: {"retention_months": 6, "kpi_threshold": 7.0},
    PartnershipLevel.TRAINER: {"retention_months": 12, "kpi_threshold": 9.0},
    PartnershipLevel.CRAFT_RD: {"retention_months": 12, "kpi_threshold": 9.0},
    PartnershipLevel.INVESTOR: {"retention_months": 12, "kpi_threshold": 9.0},
    PartnershipLevel.NGO_POLICY: {"retention_months": 12, "kpi_threshold": 8.0},
    PartnershipLevel.SUBSIDIARY: {"retention_months": 24, "kpi_threshold": 9.0},
    PartnershipLevel.KPI_LEADER: {"retention_months": 24, "kpi_threshold": 9.5},
}

# Routes
@registration_router.post("/level")
async def select_level(
    level_selection: LevelSelection,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    email = current_user.email.lower().strip()
    logger.debug(f"Level selection for {email}: {level_selection.levels}, is_lateral: {level_selection.is_lateral}")

    result=await db.execute(Select(RegistrationLevel).filter(RegistrationLevel.user_id==current_user.id))
    exisiting_user=result.scalars().first()
    if exisiting_user:
        raise HTTPException(status_code=400, detail="User already has registration levels")

    for level in level_selection.levels:
        if level not in LEVEL_REQUIREMENTS:
            raise HTTPException(status_code=400, detail=f"Invalid level: {level}")

    if level_selection.is_lateral:
        payment_amount = 100.0 * len(level_selection.levels)
        if not await process_payment(email, payment_amount):
            raise HTTPException(status_code=400, detail="Payment failed for lateral entry")
        if not await verify_khrcf(email):
            raise HTTPException(status_code=400, detail="khrcf.org verification failed")

    try:
        for level in level_selection.levels:
            requirements = LEVEL_REQUIREMENTS[level]
            new_level = RegistrationLevel(
                user_id=current_user.id,
                level=level,
                is_lateral=level_selection.is_lateral,
                payment_status="completed" if level_selection.is_lateral else "not_required",
                verification_status="verified" if level_selection.is_lateral else "not_required",
                retention_period_months=requirements["retention_months"],
                kpi_threshold=requirements["kpi_threshold"]
            )
            db.add(new_level)
        result = await db.execute(
        Select(User).filter(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.registration_step=1
            
        await db.commit()

        logger.info(f"Levels registered for {email}: {level_selection.levels}")
        return {"message": "Levels selected successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing levels for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store levels: {str(e)}")

@registration_router.post("/info")
async def submit_personal_info(
    info: PersonalInfo,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    email = current_user.email.lower().strip()
    logger.debug(f"Personal info for {email}: {info.dict()}")
    result=await db.execute(Select(RegistrationInfo).filter(RegistrationInfo.user_id==current_user.id))
    exisiting_user=result.scalars().first()
    if exisiting_user:
        raise HTTPException(status_code=400, detail="User already has registration levels")

    try:
        new_info = RegistrationInfo(
            user_id=current_user.id,
            business_name=info.business_name,
            business_legal_structure=info.business_legal_structure,
            business_type=info.business_type,
            year_established=info.year_established,
            business_registration_number=info.business_registration_number,
            brand_affiliations=info.brand_affiliations,
            website=info.website,
            annual_turnover=info.annual_turnover,
            gst_number=info.gst_number,
            tax_identification_number=info.tax_identification_number,
            import_export_code=info.import_export_code,
            street_address_1=info.street_address_1,
            street_address_2=info.street_address_2,
            city=info.city,
            state_region=info.state_region,
            postal_code=info.postal_code,
            country=info.country,
            contact_person_name=info.contact_person_name,
            contact_email=info.contact_email,
            contact_phone=info.contact_phone,
            contact_whatsapp=info.contact_whatsapp,
            contact_district=info.contact_district,
            contact_pin_code=info.contact_pin_code,
            contact_state=info.contact_state,
            contact_country=info.contact_country,
            material_standard=info.material_standard,
            quality_level=info.quality_level,
            sustainability_level=info.sustainability_level,
            service_level=info.service_level,
            standards_level=info.standards_level,
            ethics_level=info.ethics_level,
            certifications=info.certifications,
            bank_name=info.bank_name,
            account_name=info.account_name,
            account_type=info.account_type,
            account_number=info.account_number,
            ifsc_code=info.ifsc_code,
            swift_bis_code=info.swift_bis_code,
            iban_code=info.iban_code,
            kyc_challenges=info.kyc_challenges,
            gst_compliance_issues=info.gst_compliance_issues,
            fema_payment_issues=info.fema_payment_issues,
            digital_banking_issues=info.digital_banking_issues,
            fraud_cybersecurity_issues=info.fraud_cybersecurity_issues,
            payment_gateway_compliance_issues=info.payment_gateway_compliance_issues,
            account_activity_issues=info.account_activity_issues,
            regulatory_actions=info.regulatory_actions
        )
        db.add(new_info)
        result = await db.execute(
        Select(User).filter(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.registration_step=2
        await db.commit()
        logger.info(f"Personal info stored for {email}")
        return {"message": "Personal info submitted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing personal info for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store personal info: {str(e)}")
    

class SubcategoryData(BaseModel):
    subcategoryId: str = Field(..., alias="subcategoryId")
    subcategoryName: str = Field(..., alias="subcategoryName")
    specifications: Dict[str, Union[str, List[str]]] = Field(...)

    @validator("specifications")
    def validate_specifications(cls, v, values):
        if "subcategoryId" not in values:
            raise ValueError("Subcategory ID must be specified before specifications")
        for key, value in v.items():
            if not isinstance(value, (str, list)):
                raise ValueError(f"Specification {key} must be a string or list of strings")
            if isinstance(value, list) and not all(isinstance(val, str) for val in value):
                raise ValueError(f"Specification {key} list must contain only strings")
        return v

class CategoryData(BaseModel):
    categoryId: str = Field(..., alias="categoryId")
    categoryName: str = Field(..., alias="categoryName")
    subcategories: List[SubcategoryData] = Field(...)

class ProductCatalog(BaseModel):
    selectedData: List[CategoryData] = Field(...)



@registration_router.post("/products")
async def submit_product_catalog(
    catalog: ProductCatalog,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    email = current_user.email.lower().strip()
    logger.debug(f"Product catalog for {email}: {len(catalog.selectedData)} categories")

    # Check if user has already registered products
    result = await db.execute(
        select(RegistrationProduct).filter(RegistrationProduct.user_id == current_user.id)
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already has registered products")

    try:
        for category_data in catalog.selectedData:
            for subcategory in category_data.subcategories:
                # Store product directly without category validation
                new_product = RegistrationProduct(
                    user_id=current_user.id,
                    product_data={
                        "categoryId": category_data.categoryId,
                        "categoryName": category_data.categoryName,
                        "subcategoryId": subcategory.subcategoryId,
                        "subcategoryName": subcategory.subcategoryName,
                        "specifications": subcategory.specifications
                    }
                )
                db.add(new_product)
                result = await db.execute(
                Select(User).filter(User.id == current_user.id))
                user = result.scalar_one_or_none()
                if not user:
                   raise HTTPException(status_code=404, detail="User not found")
                user.registration_step=3
        await db.commit()
        logger.info(f"Product catalog stored for {email}")
        return {"message": "Product catalog submitted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing product catalog for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store product catalog: {str(e)}")


@registration_router.post("/agreement")
async def confirm_agreement(
    agreement: AgreementConfirmation,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    email = current_user.email.lower().strip()
    logger.debug(f"Agreement confirmation for {email}")
    result=await db.execute(Select(RegistrationAgreement).filter(RegistrationAgreement.user_id==current_user.id))
    exisiting_user=result.scalars().first()
    if exisiting_user:
        raise HTTPException(status_code=400, detail="User already has registration levels")

    if not agreement.agreement_signed:
        raise HTTPException(status_code=400, detail="Agreement must be signed")

    try:
        # Check mandatory documents
        result = await db.execute(
            select(Document.document_type).filter(Document.user_id == current_user.id)
        )
        uploaded_types = {doc.document_type for doc in result.scalars().all()}
        mandatory_docs = {"business_registration", "adhaar_card"}
        missing_docs = mandatory_docs - uploaded_types
        if missing_docs:
            raise HTTPException(
                status_code=400,
                detail=f"Missing mandatory documents: {missing_docs}"
            )

        new_agreement = RegistrationAgreement(
            user_id=current_user.id,
            agreement_signed=agreement.agreement_signed,
            agreement_url=agreement.agreement_url
        )
        db.add(new_agreement)
        result = await db.execute(
        Select(User).filter(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.registration_step=5
        await db.commit()
        logger.info(f"Agreement confirmed for {email}")

        # Check if all steps are complete
        level_result = await db.execute(select(RegistrationLevel).filter(RegistrationLevel.user_id == current_user.id))
        info_result = await db.execute(select(RegistrationInfo).filter(RegistrationInfo.user_id == current_user.id))
        product_result = await db.execute(select(RegistrationProduct).filter(RegistrationProduct.user_id == current_user.id))
        category_result = await db.execute(select(ProductCategory).filter(ProductCategory.user_id == current_user.id))
        document_result = await db.execute(select(Document).filter(Document.user_id == current_user.id))
        
        if all([
            level_result.scalars().first(),
            info_result.scalars().first(),
            product_result.scalars().first(),
            category_result.scalars().first(),
            document_result.scalars().first()
        ]):
            user_result = await db.execute(select(User).filter(User.id == current_user.id))
            user = user_result.scalar_one_or_none()
            user.is_active = True
            db.add(user)
            await db.commit()
            logger.info(f"Registration completed for {email}")
            return {"message": "Registration completed successfully"}
        
        return {"message": "Agreement confirmed successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing agreement for {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store agreement: {str(e)}")
    


@registration_router.get("/registration_info",response_model=PersonalInfo)
async def get_registration_info(
        current_user:UserResponse=Depends(get_current_user),
        db:AsyncSession=Depends(get_db)):
    try:
        result=await db.execute(Select(RegistrationInfo).filter(RegistrationInfo.user_id==current_user.id))
        registration_info = result.scalars().first()
        if not registration_info:
            raise HTTPException(status_code=404, detail="Registration info not found")  
        
        return registration_info
    except Exception as e:
        logger.error(f"Error fetching registration info for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch registration info: {str(e)}")
    
    