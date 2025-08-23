from fastapi import APIRouter
from app.api.routes.auth import auth_router 
from app.api.routes.document import doc_router
from app.api.routes.teams import teams_router
from app.api.routes.registration import registration_router
from app.api.routes.verification import verification_router
from app.api.routes.appointments import appointment_router
from app.api.routes.admin import admin_router
from app.api.routes.user import user_router
from app.api.routes.job import jobs_router, admin_jobs_router

router = APIRouter()
router.include_router(auth_router, tags=["auth"])
router.include_router(doc_router, tags=["documents"])
router.include_router(admin_router, tags=["admin"])
router.include_router(registration_router, tags=["registration"])
router.include_router(teams_router, tags=["teams"])
router.include_router(verification_router, tags=["verification"])
router.include_router(appointment_router, tags=["appointments"])
router.include_router(user_router, tags=["user"])
router.include_router(jobs_router, tags=["jobs"])
router.include_router(admin_jobs_router, tags=["admin_jobs"])






