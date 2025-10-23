import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from app.models.otp import OTP
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

async def send_otp_email(email: str, db: AsyncSession) -> bool:
    try:
        email = email.lower().strip()
        logger.debug(f"Starting send_otp_email for {email}, session active: {not db.is_active}")

        otp_code = str(secrets.randbelow(1000000)).zfill(6)  # 6-digit OTP
        logger.debug(f"Generated OTP {otp_code} for {email}")

        # Clear previous OTPs
        try:
            delete_result = await db.execute(delete(OTP).where(OTP.email == email))
            logger.debug(f"Deleted {delete_result.rowcount} OTPs for {email}")
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting OTPs for {email}: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error deleting OTPs: {str(e)}")


        try:
            new_otp = OTP(
                email=email,
                otp_code=otp_code
            )
            db.add(new_otp)
            await db.commit()
            logger.debug(f"Inserted OTP {otp_code} for {email}")
        except SQLAlchemyError as e:
            logger.error(f"Database error storing OTP for {email}: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error storing OTP: {str(e)}")

        # Verify OTP was stored
        try:
            result = await db.execute(select(OTP).filter(OTP.email == email, OTP.otp_code == otp_code))
            stored_otp = result.scalar_one_or_none()
            if not stored_otp:
                logger.error(f"Failed to store OTP {otp_code} for {email} in database")
                await db.rollback()
                raise HTTPException(status_code=500, detail="Failed to store OTP in database")
            logger.info(f"OTP {otp_code} stored in PostgreSQL for {email}")
        except SQLAlchemyError as e:
            logger.error(f"Database error verifying OTP storage for {email}: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error verifying OTP: {str(e)}")

        # Send email via SMTP
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        email_from = os.getenv("EMAIL_FROM")
        
        if not smtp_username or not smtp_password or not email_from:
            logger.error("Missing SMTP configuration (username, password, or sender email)")
            raise HTTPException(status_code=500, detail="Email service configuration missing")

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email
            msg['Subject'] = "Your OTP for Project Overflow"
            
            # Email body
            body = f"""
            Hello,
            
            Your OTP (One-Time Password) is: {otp_code}
            
            Please use this code to verify your account. This code will expire in 10 minutes.
            
            If you did not request this OTP, please ignore this email.
            
            Best regards,
            Project Overflow Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Enable TLS encryption
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(email_from, email, text)
            server.quit()
            
            logger.info(f"OTP email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error for {email}: {str(e)}")
            return False  # OTP is still stored in the database

    except Exception as e:
        logger.error(f"Unexpected error in send_otp_email for {email}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def verify_otp_code(email: str, otp: str, db: AsyncSession) -> bool:
    try:
        # Normalize email
        email = email.lower().strip()
        clean_otp = otp.strip('"')
        logger.debug(f"Verifying OTP for {email}, session active: {not db.is_active}, provided={clean_otp}")
        
        result = await db.execute(
            select(OTP).filter(
                OTP.email == email,
                OTP.otp_code == clean_otp
            )
        )
        stored_otp = result.scalar_one_or_none()
        
        if stored_otp:
            await db.execute(delete(OTP).where(OTP.email == email))
            await db.commit()
            logger.info(f"OTP verified for {email}: stored={stored_otp.otp_code}")
            return True
        
        logger.warning(f"Invalid OTP for {email}: provided={clean_otp}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"Database error verifying OTP for {email}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error verifying OTP for {email}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")