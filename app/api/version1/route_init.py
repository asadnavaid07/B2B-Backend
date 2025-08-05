from fastapi import APIRouter
from app.api.routes.auth import auth_router as auth_router
from app.api.routes.document import user_router as doc_router
from app.api.routes.categories import category_router 

router = APIRouter()
router.include_router(auth_router, tags=["Auth"])
router.include_router(doc_router, tags=["documents"])
router.include_router(category_router, tags=["categories"])






