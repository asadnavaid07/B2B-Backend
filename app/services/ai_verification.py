from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import Document, VerificationStatus
from app.models.user import User
from app.models.registration import RegistrationInfo
import logging

logger = logging.getLogger(__name__)

VENDOR_DOCUMENT_PROMPTS = {
    "business_registration": """
Verify that the document is a valid Business Registration Certificate. Check for:
- Official company name, registration number, and date of registration.
- Issuing authority (e.g., government or chamber of commerce).
- No signs of tampering or forgery (e.g., inconsistent fonts, missing seals).
- Valid date (not expired).
- Matches business_name and business_registration_number from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "business_license": """
Verify that the document is a valid Business License. Check for:
- License number, company name, and business address.
- Issuing authority and validity period.
- No signs of tampering or forgery.
- Valid date (not expired).
- Matches business_name and street_address_1 from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "adhaar_card": """
Verify that the document is a valid Aadhaar Card. Check for:
- 12-digit Aadhaar number, name, and address.
- QR code or other authenticity markers.
- No signs of tampering or forgery.
- Matches contact_person_name and contact_district from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "artisan_id_card": """
Verify that the document is a valid Artisan/Trade License. Check for:
- Artisan name, trade details, and license number.
- Issuing authority (e.g., trade board or guild).
- No signs of tampering or forgery.
- Valid date (not expired).
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "bank_statement": """
Verify that the document is a valid Bank Statement. Check for:
- Bank name, account holder name, and account number.
- Recent transactions (within last 6 months).
- Official bank logo and formatting.
- No signs of tampering or forgery.
- Matches bank_name, account_name, and account_number from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "product_catalog": """
Verify that the document is a valid Product Catalog. Check for:
- Clear list of products with descriptions and images.
- For certifications: verify GI, Fair Trade, or Organic certifications with valid certificate numbers and issuing authorities.
- No signs of tampering or forgery.
- Matches certifications from registration_info.
For vendors, extract data relevant to KPI calculations (e.g., product quality, certifications).
Return: JSON with { 
    "status": "PASS" or "FAIL", 
    "remarks": "string", 
    "kpi_details": {
        "product_integrity": {
            "quality": float,  // 0-8 based on product descriptions
            "certification": float  // 0-4 based on valid certifications
        }
    }
}.
""",
    "certifications": """
Verify that the document contains valid Certifications (GI, Fair Trade, Organic). Check for:
- Certificate number, issuing authority, and validity period.
- Matches certifications from registration_info.
- No signs of tampering or forgery.
Extract data for KPI calculations (e.g., certification compliance).
Return: JSON with { 
    "status": "PASS" or "FAIL", 
    "remarks": "string", 
    "kpi_details": {
        "product_integrity": {
            "certification": float  // 0-4 based on valid certifications
        }
    }
}.
"""
}

BUYER_DOCUMENT_PROMPTS = {
    "business_registration": """
Verify that the document is a valid Articles of Incorporation. Check for:
- Official company name, incorporation date, and registration number.
- Issuing authority (e.g., state or national registry).
- No signs of tampering or forgery.
- Valid date (not expired).
- Matches business_name and business_registration_number from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "business_license": """
Verify that the document is a valid Business License. Check for:
- License number, company name, and business address.
- Issuing authority and validity period.
- No signs of tampering or forgery.
- Valid date (not expired).
- Matches business_name and street_address_1 from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "adhaar_card": """
Verify that the document is a valid Photo ID (e.g., passport, driver’s license). Check for:
- Name, photo, and ID number.
- Issuing authority and validity period.
- No signs of tampering or forgery.
- Matches contact_person_name and contact_district from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "artisan_id_card": """
Verify that the document is a valid Trade License. Check for:
- Business name, trade details, and license number.
- Issuing authority (e.g., trade board or government).
- No signs of tampering or forgery.
- Valid date (not expired).
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "bank_statement": """
Verify that the document is a valid Bank Statement. Check for:
- Bank name, account holder name, and account number.
- Recent transactions (within last 6 months).
- Official bank logo and formatting.
- No signs of tampering or forgery.
- Matches bank_name, account_name, and account_number from registration_info.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "product_catalog": """
Verify that the document is a valid Product Catalog. Check for:
- Clear list of products with descriptions and images.
- No signs of tampering or forgery.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
""",
    "certifications": """
Verify that the document contains valid Certifications (e.g., industry-specific certifications). Check for:
- Certificate number, issuing authority, and validity period.
- Matches certifications from registration_info.
- No signs of tampering or forgery.
Return: JSON with { "status": "PASS" or "FAIL", "remarks": "string" }.
"""
}

async def analyze_document_advanced(doc_id: int, file_path: str, document_type: str, db: AsyncSession):
    try:
        # Fetch document and user
        result = await db.execute(
            select(Document).filter(Document.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise Exception(f"Document {doc_id} not found")
        
        result = await db.execute(
            select(User).filter(User.id == doc.user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise Exception(f"User {doc.user_id} not found")
        
        # Fetch registration info for cross-verification
        result = await db.execute(
            select(RegistrationInfo).filter(RegistrationInfo.user_id == user.id)
        )
        reg_info = result.scalar_one_or_none()
        
        # Select prompts based on role
        prompts = VENDOR_DOCUMENT_PROMPTS if user.role == "vendor" else BUYER_DOCUMENT_PROMPTS
        prompt = prompts.get(document_type)
        if not prompt:
            raise Exception(f"Invalid document type: {document_type}")
        
        # Mock AI verification (replace with actual AI call)
        mock_ai_response = {
            "status": "PASS",
            "remarks": f"Valid {document_type} document",
            "extracted_data": {
                "company_name": reg_info.business_name if reg_info else "",
                "registration_number": reg_info.business_registration_number if reg_info else "",
                "address": reg_info.street_address_1 if reg_info else "",
                "name": reg_info.contact_person_name if reg_info else "",
                "bank_name": reg_info.bank_name if reg_info else "",
                "account_name": reg_info.account_name if reg_info else "",
                "account_number": reg_info.account_number if reg_info else "",
                "certifications": reg_info.certifications if reg_info else []
            }
        }
        
        # Cross-verify with registration_info
        if reg_info:
            if document_type == "business_registration" and (
                reg_info.business_name not in mock_ai_response["extracted_data"].get("company_name", "") or
                reg_info.business_registration_number not in mock_ai_response["extracted_data"].get("registration_number", "")
            ):
                mock_ai_response = {"status": "FAIL", "remarks": "Business name or registration number mismatch"}
            elif document_type == "business_license" and (
                reg_info.business_name not in mock_ai_response["extracted_data"].get("company_name", "") or
                reg_info.street_address_1 not in mock_ai_response["extracted_data"].get("address", "")
            ):
                mock_ai_response = {"status": "FAIL", "remarks": "Business name or address mismatch"}
            elif document_type == "adhaar_card" and (
                reg_info.contact_person_name not in mock_ai_response["extracted_data"].get("name", "") or
                reg_info.contact_district not in mock_ai_response["extracted_data"].get("address", "")
            ):
                mock_ai_response = {"status": "FAIL", "remarks": "Contact person name or district mismatch"}
            elif document_type == "bank_statement" and (
                reg_info.bank_name not in mock_ai_response["extracted_data"].get("bank_name", "") or
                reg_info.account_name not in mock_ai_response["extracted_data"].get("account_name", "") or
                reg_info.account_number not in mock_ai_response["extracted_data"].get("account_number", "")
            ):
                mock_ai_response = {"status": "FAIL", "remarks": "Bank details mismatch"}
            elif document_type in ["product_catalog", "certifications"] and reg_info.certifications:
                extracted_certs = mock_ai_response["extracted_data"].get("certifications", [])
                if not all(cert in extracted_certs for cert in reg_info.certifications):
                    mock_ai_response = {"status": "FAIL", "remarks": "Certifications mismatch"}
        
        # For vendors, include KPI calculations for product_catalog and certifications
        if user.role == "vendor" and document_type in ["product_catalog", "certifications"]:
            mock_kpi_data = {
                "product_catalog": {
                    "product_integrity": {
                        "quality": 7.0,  # Based on product descriptions
                        "certification": 3.0  # Based on certifications
                    }
                },
                "certifications": {
                    "product_integrity": {
                        "certification": 4.0  # Based on valid certifications
                    }
                }
            }.get(document_type, {})
            mock_ai_response["kpi_details"] = mock_kpi_data
        else:
            mock_ai_response["kpi_details"] = {}
        
        # Update document
        doc.ai_verification_status = VerificationStatus[mock_ai_response["status"]]
        doc.ai_remarks = mock_ai_response["remarks"]
        doc.kpi_details = mock_ai_response["kpi_details"]
        doc.extracted_data = mock_ai_response["extracted_data"]
        doc.ai_kpi_score = sum(sum(category.values()) for category in doc.kpi_details.values()) if doc.kpi_details else 0.0
        
        db.add(doc)
        await db.commit()
        
        # Update user's kpi_score by aggregating all verified documents
        if user.role == "vendor":
            result = await db.execute(
                select(Document).filter(
                    Document.user_id == user.id,
                    Document.ai_verification_status == VerificationStatus.PASS
                )
            )
            verified_docs = result.scalars().all()
            total_kpi_score = sum(doc.ai_kpi_score for doc in verified_docs)
            user.kpi_score = total_kpi_score
            db.add(user)
            await db.commit()
        
        logger.info(f"Document {doc_id} verified: status={doc.ai_verification_status}, remarks={doc.ai_remarks}, kpi_details={doc.kpi_details}")
        return {
            "status": doc.ai_verification_status.value,
            "remarks": doc.ai_remarks,
            "kpi_details": doc.kpi_details
        }
    except Exception as e:
        logger.error(f"Error verifying document {doc_id}: {str(e)}")
        raise