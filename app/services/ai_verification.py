import base64
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.document import Document, VerificationStatus

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_document_advanced(document_id: int, file_path: str, document_type: str, db: AsyncSession) -> Dict[str, Any]:
    try:
        # Read file
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        b64_file = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = "application/pdf" if file_path.endswith(".pdf") else "image/jpeg"

        # Define document-specific prompts
        prompts = {
            "business_registration": """
Verify a business registration certificate. Check for:
- Official letterhead, registration number, issuing authority.
- Clear text, no blurriness.
- Valid issue and expiry dates.
Return JSON with:
- status: "Pass", "Fail", or "AwaitingAdditional"
- kpi: 0-10 (based on clarity, authenticity, completeness)
- extracted: {registration_number, issue_date, expiry_date, business_name}
- remarks: Explanation of status
""",
            "business_license": """
Verify a business license certificate. Check for:
- License number, issuing authority, and business name.
- Clear text, no tampering.
- Valid dates.
Return JSON with:
- status: "Pass", "Fail", or "AwaitingAdditional"
- kpi: 0-10
- extracted: {license_number, issue_date, expiry_date, business_name}
- remarks: Explanation
""",
            "adhaar_card": """
Verify an Adhaar card. Check for:
- 12-digit Adhaar number, name, and address.
- No blurriness or tampering.
- QR code presence.
Return JSON with:
- status: "Pass", "Fail", or "AwaitingAdditional"
- kpi: 0-10
- extracted: {name, adhaar_number, address}
- remarks: Explanation
""",
            "artisan_id_card": """
Verify an artisan ID card. Check for:
- Artisan name, ID number, and issuing organization.
- Clear photo and text.
Return JSON with:
- status: "Pass", "Fail", or "AwaitingAdditional"
- kpi: 0-10
- extracted: {name, id_number}
- remarks: Explanation
""",
            "bank_statement": """
Verify a bank statement (last 3 months). Check for:
- Bank logo, account number, and account holder name.
- Transactions from the last 3 months.
- No tampering.
Return JSON with:
- status: "Pass", "Fail", or "AwaitingAdditional"
- kpi: 0-10
- extracted: {account_number, account_holder, date_range}
- remarks: Explanation
""",
            "product_catalog": """
Verify a product catalog. Check for:
- A4 portrait layout, 12pt font, 1-inch margins.
- Includes introduction, product descriptions, prices, certifications, business info.
- Clear images and text.
Return JSON with:
- status: "Pass", "Fail", or "AwaitingAdditional"
- kpi: 0-10
- extracted: {business_name, product_count}
- remarks: Explanation
""",
            "certifications": """
Verify certifications (GI, Fair Trade, Organic, etc.). Check for:
- Certificate number, issuing authority, and validity.
- No tampering or blurriness.
Return JSON with:
- status: "Pass", "Fail", or "AwaitingAdditional"
- kpi: 0-10
- extracted: {certificate_type, certificate_number, issue_date, expiry_date}
- remarks: Explanation
"""
        }

        prompt = prompts.get(document_type, "Invalid document type")
        if prompt == "Invalid document type":
            raise ValueError(f"Unsupported document type: {document_type}")

        response = await client.chat.completions.create(
            model="gpt-4o",  # Updated to gpt-4o
            messages=[
                {"role": "system", "content": "You are a professional document verifier for a B2B platform."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_file}"}}
                    ]
                }
            ],
            max_tokens=700,
        )

        try:
            content = response.choices[0].message.content
            result = json.loads(content)
            if not all(key in result for key in ["status", "kpi", "extracted", "remarks"]):
                raise ValueError("AI response missing required fields")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"AI Response parsing failed: {response}")
            raise ValueError(f"AI did not return valid JSON: {str(e)}")

        async with db.begin():
            db_result = await db.execute(select(Document).where(Document.id == document_id))
            document = db_result.scalar_one_or_none()
            if not document:
                raise ValueError("Document not found")

            document.ai_verification_status = VerificationStatus(result["status"])
            document.ai_kpi_score = result["kpi"]
            document.ai_remarks = result["remarks"]
            document.extracted_data = result["extracted"]
            await db.commit()

        return result
    except Exception as e:
        logger.error(f"AI Verification failed for document {document_id}: {str(e)}")
        raise

async def calculate_kpi_score(user_id: int, db: AsyncSession) -> float:
    try:
        # Get verified documents
        result = await db.execute(
            select(Document).filter(
                Document.user_id == user_id,
                Document.ai_verification_status == VerificationStatus.Pass
            )
        )
        documents = result.scalars().all()

        # Initialize KPI components based on Vendor KPI Framework
        kpi_scores = {
            "customer_experience": 0,
            "product_integrity": 0,
            "technology_integration": 0,
            "ethical_sustainability": 0,
            "ecosystem_engagement": 0,
            "market_performance": 0
        }

        # Map document types to KPI categories
        doc_contributions = {
            "business_registration": ("product_integrity", 0.2),  # Contributes to Integrity & Authenticity
            "business_license": ("product_integrity", 0.2),
            "adhaar_card": ("product_integrity", 0.1),
            "artisan_id_card": ("product_integrity", 0.1),
            "bank_statement": ("market_performance", 0.2),
            "product_catalog": ("technology_integration", 0.3),
            "certifications": ("ethical_sustainability", 0.3)
        }

        # Calculate scores based on verified documents
        total_weight = 0
        for doc in documents:
            category, weight = doc_contributions.get(doc.document_type, (None, 0))
            if category:
                kpi_scores[category] += doc.ai_kpi_score * weight
                total_weight += weight

        # Normalize to 0-10 scale (based on framework's 104 max points)
        weights = {
            "customer_experience": 0.2,  # 20%
            "product_integrity": 0.29,  # 29%
            "technology_integration": 0.15,  # 15%
            "ethical_sustainability": 0.15,  # 15%
            "ecosystem_engagement": 0.15,  # 15%
            "market_performance": 0.1  # 10%
        }

        final_score = 0
        for category, score in kpi_scores.items():
            final_score += score * weights[category]

        # Scale to 0-10
        final_score = (final_score / 104) * 10 if total_weight > 0 else 0
        return round(final_score, 2)
    except Exception as e:
        logger.error(f"Error calculating KPI score for user {user_id}: {str(e)}")
        return 0.0