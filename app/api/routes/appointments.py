from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.appointment import Appointment, VerificationStatus
from app.schema.appointment import AppointmentResponse, AvailableTimeResponse
from app.services.auth.jwt import get_current_user
from app.schema.user import UserResponse
from datetime import date, datetime, timedelta, time
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
import pytz
import uuid

logger = logging.getLogger(__name__)
appointment_router = APIRouter(prefix="/appointments", tags=["appointments"])

ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx"]

TIME_SLOTS_CONFIG = {
    "buyer": {
        "virtual": {
            "weekday_times": [
                time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                time(13, 0), time(13, 30), time(14, 0), time(14, 30)
            ],
            "friday_times": [
                time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                time(14, 0), time(14, 30)
            ],
            "time_zone": "EST"
        },
        "offline": {
            "USA Office – HQ": {
                "weekday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                    time(14, 0), time(14, 30), time(15, 0), time(15, 30)
                ],
                "friday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(12, 0), time(12, 30), time(14, 0), time(14, 30),
                    time(15, 0), time(15, 30)
                ],
                "time_zone": "EST"
            },
            "Kashmir India": {
                "weekday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                    time(14, 0), time(14, 30), time(15, 0), time(15, 30)
                ],
                "friday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(15, 0), time(15, 30)
                ],
                "saturday_times": [
                    time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                    time(13, 0), time(13, 30), time(14, 0), time(14, 30)
                ],
                "time_zone": "IST"
            }
        }
    },
    "vendor": {
        "virtual": {
            "weekday_times": [
                time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                time(13, 0), time(13, 30), time(14, 0), time(14, 30)
            ],
            "friday_times": [
                time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                time(14, 0), time(14, 30)
            ],
            "time_zone": "EST"
        },
        "offline": {
            "USA Office – HQ": {
                "weekday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                    time(14, 0), time(14, 30), time(15, 0), time(15, 30)
                ],
                "friday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(12, 0), time(12, 30), time(14, 0), time(14, 30),
                    time(15, 0), time(15, 30)
                ],
                "time_zone": "EST"
            },
            "Kashmir India": {
                "weekday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                    time(14, 0), time(14, 30), time(15, 0), time(15, 30)
                ],
                "friday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(15, 0), time(15, 30)
                ],
                "saturday_times": [
                    time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                    time(13, 0), time(13, 30), time(14, 0), time(14, 30)
                ],
                "time_zone": "IST"
            }
        }
    },
    "guest": {
        "USA": {
            "virtual": {
                "weekday_times": [
                    time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                    time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                    time(13, 0), time(13, 30), time(14, 0), time(14, 30)
                ],
                "friday_times": [
                    time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                    time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                    time(14, 0), time(14, 30)
                ],
                "time_zone": "EST"
            },
            "offline": {
                "USA Office – HQ": {
                    "weekday_times": [
                        time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                        time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                        time(14, 0), time(14, 30), time(15, 0), time(15, 30)
                    ],
                    "friday_times": [
                        time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                        time(12, 0), time(12, 30), time(14, 0), time(14, 30),
                        time(15, 0), time(15, 30)
                    ],
                    "time_zone": "EST"
                }
            }
        },
        "India": {
            "virtual": {
                "weekday_times": [
                    time(13, 0), time(13, 30), time(14, 0), time(14, 30)
                ],
                "friday_times": [],
                "saturday_times": [
                    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                    time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                    time(14, 0), time(14, 30), time(15, 0), time(15, 30)
                ],
                "time_zone": "IST"
            },
            "offline": {
                "Kashmir India": {
                    "weekday_times": [
                        time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                        time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                        time(14, 0), time(14, 30), time(15, 0), time(15, 30)
                    ],
                    "friday_times": [
                        time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                        time(15, 0), time(15, 30)
                    ],
                    "saturday_times": [
                        time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                        time(13, 0), time(13, 30), time(14, 0), time(14, 30)
                    ],
                    "time_zone": "IST"
                }
            }
        }
    }
}

def get_available_dates(start_date: date) -> List[date]:
    from datetime import date, timedelta
    dates = []
    current_date = start_date
    for _ in range(30):  # Generate 30 days, excluding Sundays
        if current_date.weekday() != 6:  # Skip Sundays
            dates.append(current_date)
        current_date += timedelta(days=1)
    return dates[:26]  # Limit to 26 dates


@appointment_router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    db: AsyncSession = Depends(get_db)
):

    try:
        result = await db.execute(
            select(Appointment).filter(
            ).order_by(Appointment.appointment_date, Appointment.appointment_time)
        )
        appointments = result.scalars().all()
        if not appointments:
            return []
        return [AppointmentResponse.from_orm(appointment) for appointment in appointments]
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch appointments: {str(e)}")









@appointment_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    user_type: str = Form(...),
    appointment_type: str = Form(...),
    virtual_platform: Optional[str] = Form(None),
    office_location: Optional[str] = Form(None),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    time_zone: str = Form(...),
    purpose: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    business_name: str = Form(...),
    website: Optional[str] = Form(None),
    email: str = Form(...),
    phone_number: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):


    # Parse and validate date
    try:
        parsed_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Parse and validate time
    try:
        parsed_time = datetime.strptime(appointment_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    # Validate date in available range
    available_dates = get_available_dates(date(2025, 8, 14))
    if parsed_date not in available_dates:
        raise HTTPException(status_code=400, detail=f"Invalid date. Available dates: {available_dates}")

    # Validate time slot
    if user_type == "guest":
        config = TIME_SLOTS_CONFIG[user_type][email.split('@')[1].split('.')[0]][appointment_type]
    else:
        config = TIME_SLOTS_CONFIG[user_type][appointment_type]
        if appointment_type == "offline":
            config = config[office_location or "USA Office – HQ"]
    is_friday = parsed_date.weekday() == 4
    is_saturday = parsed_date.weekday() == 5
    if is_saturday and "saturday_times" in config:
        valid_slots = [t.strftime("%H:%M") for t in config["saturday_times"]]
    elif is_friday:
        valid_slots = [t.strftime("%H:%M") for t in config["friday_times"]]
    else:
        valid_slots = [t.strftime("%H:%M") for t in config["weekday_times"]]
    if appointment_time not in valid_slots:
        raise HTTPException(status_code=400, detail=f"Invalid appointment time. Available times: {valid_slots}")

    # Store time in local time zone
    time_zone_obj = pytz.timezone("America/New_York" if time_zone == "EST" else "Asia/Kolkata")
    local_dt = datetime.combine(parsed_date, parsed_time)
    local_dt = time_zone_obj.localize(local_dt)

    # Check for existing appointment
    result = await db.execute(
        select(Appointment).filter(
            Appointment.appointment_date == parsed_date,
            Appointment.appointment_time == parsed_time,
            Appointment.time_zone == time_zone
        )
    )
    if result.scalar_one_or_none():
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
            unique_filename = f"appointment_{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_name = file.filename
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    try:
        new_appointment = Appointment(
            user_type=user_type.upper(),
            appointment_type=appointment_type.upper(),
            virtual_platform=virtual_platform.upper() if virtual_platform else None,
            office_location=office_location,
            appointment_date=parsed_date,
            appointment_time=parsed_time,
            time_zone=time_zone,
            purpose=purpose,
            first_name=first_name,
            last_name=last_name,
            business_name=business_name,
            website=website,
            email=email,
            phone_number=phone_number,
            file_path=file_path,
            file_name=file_name,
            verification_status=VerificationStatus.PENDING
        )
        db.add(new_appointment)
        await db.commit()
        await db.refresh(new_appointment)
        logger.info(f"Appointment created {new_appointment.id}")
        return {"message": "Appointment created successfully", "appointment_id": new_appointment.id}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating appointment :{str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")