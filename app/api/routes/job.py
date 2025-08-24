from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.services.auth.jwt import get_current_user
from app.schema.job import JobCreate, JobUpdate, JobResponse, JobFullResponse
from app.schema.user import UserResponse
from app.schema.user import UserRole
import logging

logger = logging.getLogger(__name__)
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])
admin_jobs_router = APIRouter(prefix="/admin/jobs", tags=["admin_jobs"])

@jobs_router.get("/", response_model=list[JobResponse])
async def get_jobs(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        logger.info(f"Fetched {len(jobs)} job postings")
        return jobs
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")

@admin_jobs_router.get("/{id}", response_model=JobFullResponse)
async def get_job_details(id: int, current_user: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in [UserRole.sub_admin, UserRole.super_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(select(Job).filter(Job.id == id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        logger.info(f"Fetched job details for job_id={id}")
        return job
    except Exception as e:
        logger.error(f"Error fetching job {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job details: {str(e)}")

@jobs_router.post("/", status_code=201, response_model=JobFullResponse)
async def create_job(
    job_data: JobCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Strip tzinfo from datetime to match TIMESTAMP WITHOUT TIME ZONE
        job_dict = job_data.dict()
        if "application_deadline" in job_dict and job_dict["application_deadline"]:
            deadline = job_dict["application_deadline"]
            if deadline.tzinfo is not None:
                job_dict["application_deadline"] = deadline.replace(tzinfo=None)

        new_job = Job(
            **job_dict,
            posted_by=current_user.id
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        logger.info(f"Job created: {new_job.title} (job_id={new_job.id}) by user {current_user.email}")
        return new_job
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@jobs_router.post("/update", status_code=200, response_model=JobFullResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.sub_admin, UserRole.super_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        update_fields = job_data.dict(exclude_unset=True)
        # Strip tzinfo from application_deadline
        if "application_deadline" in update_fields and update_fields["application_deadline"]:
            deadline = update_fields["application_deadline"]
            if deadline.tzinfo is not None:
                update_fields["application_deadline"] = deadline.replace(tzinfo=None)
        
        for field, value in update_fields.items():
            setattr(job, field, value)
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"Job updated: {job.title} (job_id={job_id}) by user {current_user.email}")
        return job
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")


@jobs_router.delete("/{id}", status_code=200)
async def delete_job(
    id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.super_admin, UserRole.sub_admin]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.execute(select(Job).filter(Job.id == id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        await db.delete(job)
        await db.commit()
        logger.info(f"Job deleted: job_id={id} by user {current_user.email}")
        return {"message": "Job deleted successfully", "job_id": id}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting job {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")