import os
import secrets
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.models.otp import OTP
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def send_otp_email(email: str, db: AsyncSession = Depends(get_db)) -> bool:
    try:
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        email_from = os.getenv("EMAIL_FROM")
        if not sendgrid_api_key or not email_from:
            logger.error("Missing SendGrid API key or sender email")
            raise HTTPException(status_code=500, detail="Email service configuration missing")
        
        otp = str(secrets.randbelow(1000000)).zfill(6)
        logger.debug(f"Generated OTP for {email}: {otp}")
        
        message = Mail(
            from_email=email_from,
            to_emails=email,
            subject="Your OTP for Project Overflow",
            plain_text_content=f"Your OTP is: {otp}"
        )
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        logger.debug(f"SendGrid response for {email}: status={response.status_code}")
        
        if response.status_code < 200 or response.status_code >= 300:
            logger.error(f"SendGrid failed for {email}: status={response.status_code}")
            raise HTTPException(status_code=500, detail=f"Failed to send OTP email: Status {response.status_code}")
        
        try:
            await db.execute(delete(OTP).where(OTP.email == email))
            expires_at = datetime.utcnow() + timedelta(seconds=300)
            new_otp = OTP(
                email=email,
                otp_code=otp,  # Store as plain string
                expires_at=expires_at
            )
            db.add(new_otp)
            await db.commit()
            logger.info(f"OTP {otp} stored in PostgreSQL for {email}, expires at {expires_at}")
            return True
        except Exception as e:
            logger.error(f"Failed to store OTP in PostgreSQL for {email}: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to store OTP: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending OTP to {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send OTP email: {str(e)}")

async def verify_otp_code(email: str, otp: str, db: AsyncSession = Depends(get_db)) -> bool:
    try:
        # Strip quotes from OTP if present
        clean_otp = otp.strip('"')
        logger.debug(f"Verifying OTP for {email}: provided={clean_otp}")
        
        result = await db.execute(
            select(OTP).filter(
                OTP.email == email,
                OTP.otp_code == clean_otp,
                OTP.expires_at > datetime.utcnow()
            )
        )
        stored_otp = result.scalar_one_or_none()
        
        if stored_otp:
            await db.execute(delete(OTP).where(OTP.email == email))
            await db.commit()
            logger.info(f"OTP verified for {email}")
            return True
        
        logger.warning(f"Invalid or expired OTP for {email}: provided={clean_otp}")
        return False
    except Exception as e:
        logger.error(f"Error verifying OTP for {email}: {str(e)}")
        await db.rollback()
        return False