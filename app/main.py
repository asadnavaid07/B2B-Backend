from fastapi import FastAPI
from contextlib import asynccontextmanager

from fastapi.staticfiles import StaticFiles
from app.core.database import init_db
from dotenv import load_dotenv
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from app.api.version1.route_init import router
from app.services.background_tasks import background_task_service

load_dotenv()



@asynccontextmanager
async def lifespan(app:FastAPI):
    await init_db()
    # Start all background schedulers
    await background_task_service.start_all_schedulers()
    yield
    # Stop all schedulers when app shuts down
    await background_task_service.stop_all_schedulers()

def create_app() -> FastAPI:
    app = FastAPI(
        title="B2B APIS",
        version="1.0.0",
        description="De Koshur Crafts, our mission transcends the typical e-commerce experience.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }

        for path in openapi_schema["paths"].values():
            for method in path.values():
                method.setdefault("security", []).append({"BearerAuth": []})

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "default-secret-key"),
        session_cookie="session_cookie"
    )

    app.include_router(router)

    return app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )