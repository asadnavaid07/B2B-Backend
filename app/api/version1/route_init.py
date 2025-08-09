from fastapi import APIRouter
from app.api.routes.auth import auth_router 
from app.api.routes.document import doc_router
# from app.api.routes.categories import category_router 
from app.api.routes.registration import registration_router

router = APIRouter()
router.include_router(auth_router, tags=["auth"])
router.include_router(doc_router, tags=["documents"])
# router.include_router(category_router, tags=["categories"])
router.include_router(registration_router, tags=["registration"])






