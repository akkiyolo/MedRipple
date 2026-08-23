from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.patients import router as patients_router
from app.api.v1.doctors import router as doctors_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.ai import router as ai_router
from app.api.v1.medications import router as medications_router
from app.api.v1.followups import router as followups_router
from app.api.v1.care_plans import router as care_plans_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.admin import router as admin_router
from app.api.v1.health import router as health_router
from app.api.v1.compat_router import router as compat_router

api_v1_router = APIRouter(prefix="/api/v1")
api_legacy_router = APIRouter(prefix="/api")

sub_routers = [
    auth_router, profile_router, patients_router, doctors_router,
    appointments_router, ai_router, medications_router, followups_router,
    care_plans_router, calendar_router, notifications_router, admin_router, health_router
]

for r in sub_routers:
    api_v1_router.include_router(r)
    api_legacy_router.include_router(r)

# Root level compatibility routes for frontend endpoints
root_compat_router = APIRouter()
root_compat_router.include_router(compat_router)
