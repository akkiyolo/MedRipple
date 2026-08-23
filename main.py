import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import MedRippleException
from app.core.database import init_db
from app.api.v1.router import api_v1_router, api_legacy_router, root_compat_router
from app.views.auth_views import router as auth_views_router
from app.views.patient_views import router as patient_views_router
from app.views.doctor_views import router as doctor_views_router
from app.views.admin_views import router as admin_views_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MedRipple Orchestration Platform...")
    init_db()
    yield
    logger.info("Shutting down MedRipple Orchestration Platform...")

app = FastAPI(
    title="MedRipple Healthcare Platform",
    description="AI-Powered Longitudinal Healthcare Orchestration Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Audit Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

# Custom Exception Handler
@app.exception_handler(MedRippleException)
async def medripple_exception_handler(request: Request, exc: MedRippleException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

# Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(root_compat_router)
app.include_router(api_v1_router)
app.include_router(api_legacy_router)
app.include_router(auth_views_router)
app.include_router(patient_views_router)
app.include_router(doctor_views_router)
app.include_router(admin_views_router)

@app.get("/")
def root():
    return RedirectResponse(url="/login")
