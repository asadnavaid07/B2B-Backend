from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.appointment import Appointment, UserType, AppointmentType, VirtualPlatform, OfficeLocation
from app.models.user import User
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import date, time, datetime, timedelta
import pytz
import os
import uuid
import logging
import calendar
from app.utils.appointment import TIME_SLOTS_CONFIG, get_available_dates
from app.schema.appointment import AppointmentCreate, AppointmentResponse, AvailableTimeResponse



logger = logging.getLogger(__name__)
appointment_router = APIRouter(prefix="/appointments", tags=["appointments"])


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg"}


@appointment_router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching appointments for user {current_user.email}")
    try:
        query = select(Appointment)
        if current_user.role != "admin":
            query = query.filter(Appointment.user_id == current_user.id)
        result = await db.execute(query)
        appointments = result.scalars().all()
        return [
            AppointmentResponse(
                **appt.__dict__,
                appointment_time=appt.appointment_time.strftime("%H:%M")
            ) for appt in appointments
        ]
    except Exception as e:
        logger.error(f"Error fetching appointments for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch appointments: {str(e)}")

@appointment_router.get("/times", response_model=List[AvailableTimeResponse])
async def get_available_times(
    date: date,
    user_type: str = Query(..., regex="^(buyer|vendor|guest)$"),
    appointment_type: str = Query(..., regex="^(virtual|offline)$"),
    office_location: Optional[str] = Query(None, regex="^(USA Office – HQ|Kashmir India)?$"),
    country: Optional[str] = Query(None, regex="^(USA|India)?$"),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Fetching available times for {user_type} on {date}")
    available_dates = get_available_dates(date(2025, 8, 14))
    if date not in available_dates:
        raise HTTPException(status_code=400, detail=f"Invalid date. Available dates: {available_dates}")

    if appointment_type == "offline" and not office_location:
        raise HTTPException(status_code=400, detail="Office location required for offline appointments")
    if appointment_type == "virtual" and office_location:
        raise HTTPException(status_code=400, detail="Office location not applicable for virtual appointments")
    if user_type == "guest" and not country:
        raise HTTPException(status_code=400, detail="Country required for guest users")
    if user_type != "guest" and country:
        raise HTTPException(status_code=400, detail="Country only applicable for guest users")

    if user_type == "guest":
        config = TIME_SLOTS_CONFIG[user_type][country or "USA"][appointment_type]
    else:
        config = TIME_SLOTS_CONFIG[user_type][appointment_type]
        if appointment_type == "offline":
            config = config[office_location]

    time_slots = config["times"]
    time_zone = config["time_zone"]

    # Convert local times to UTC for checking booked slots
    time_zone_obj = pytz.timezone("America/New_York" if time_zone == "EST" else "Asia/Kolkata")
    booked_times = set()
    for slot in time_slots:
        local_dt = datetime.combine(date, slot)
        local_dt = time_zone_obj.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.UTC)
        result = await db.execute(
            select(Appointment.appointment_time).filter(
                Appointment.appointment_date == utc_dt.date(),
                Appointment.appointment_time == utc_dt.time(),
                Appointment.time_zone == time_zone
            )
        )
        if result.scalar_one_or_none():
            booked_times.add(slot)

    available_times = [t.strftime("%H:%M") for t in time_slots if t not in booked_times]
    return [AvailableTimeResponse(date=date, time_slots=available_times, time_zone=time_zone)]

@appointment_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment: AppointmentCreate = Depends(),
    file: Optional[UploadFile] = File(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Creating appointment for user {current_user.email}: {appointment.user_type}")

    # Validate user type matches role (except for guests)
    if appointment.user_type != "guest" and appointment.user_type != current_user.role:
        raise HTTPException(
            status_code=400,
            detail=f"User role {current_user.role} does not match provided user_type {appointment.user_type}"
        )

    # Convert time to UTC for storage
    time_zone = pytz.timezone("America/New_York" if appointment.time_zone == "EST" else "Asia/Kolkata")
    local_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)
    local_dt = time_zone.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.UTC)
    utc_date = utc_dt.date()
    utc_time = utc_dt.time()

    # Check for existing appointment on the same date and time
    result = await db.execute(
        select(Appointment).filter(
            Appointment.user_id == current_user.id,
            Appointment.appointment_date == utc_date,
            Appointment.appointment_time == utc_time
        )
    )
    existing_appointment = result.scalar_one_or_none()
    if existing_appointment:
        raise HTTPException(
            status_code=400,
            detail="User already has an appointment at this date and time"
        )

    # Handle file upload
    file_path = None
    file_name = None
    if file:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed: {ALLOWED_EXTENSIONS}"
            )
        try:
            upload_dir = "uploads/documents"
            os.makedirs(upload_dir, exist_ok=True)
            unique_filename = f"{current_user.id}_appointment_{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_name = file.filename
        except Exception as e:
            logger.error(f"Error uploading file for {current_user.email}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    try:
        user_id = None if appointment.user_type == "guest" else current_user.id
        new_appointment = Appointment(
            user_id=user_id,
            user_type=appointment.user_type,
            appointment_type=appointment.appointment_type,
            virtual_platform=appointment.virtual_platform,
            office_location=appointment.office_location,
            appointment_date=utc_date,
            appointment_time=utc_time,
            time_zone=appointment.time_zone,
            purpose=appointment.purpose,
            file_path=file_path,
            file_name=file_name
        )
        db.add(new_appointment)
        await db.commit()
        await db.refresh(new_appointment)
        logger.info(f"Appointment created for {current_user.email}: {appointment.user_type} on {appointment.appointment_date}")
        return {"message": "Appointment created successfully", "appointment_id": new_appointment.id}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating appointment for {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")