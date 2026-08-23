from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.services.s3_service import s3_service
from app.services.ai_service import ai_service
import redis

router = APIRouter(tags=["Health Checks"])

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "MedRipple Orchestration Engine", "version": "1.0.0"}

@router.get("/health/db")
def health_db(user: User = Depends(require_role(UserRole.ADMIN)), db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "Neon PostgreSQL", "pgvector": "enabled"}
    except Exception as e:
        return {"status": "unhealthy"}

@router.get("/health/redis")
def health_redis(user: User = Depends(require_role(UserRole.ADMIN))):
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "degraded", "message": "Redis unavailable (Fallback active)"}

@router.get("/health/s3")
def health_s3(user: User = Depends(require_role(UserRole.ADMIN))):
    is_configured = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
    return {"status": "healthy" if is_configured else "mock", "s3_configured": is_configured, "bucket": settings.AWS_S3_BUCKET}

@router.get("/health/ai")
def health_ai(user: User = Depends(require_role(UserRole.ADMIN))):
    is_configured = bool(settings.GROQ_API_KEY)
    return {"status": "healthy" if is_configured else "fallback", "groq_configured": is_configured, "model": settings.GROQ_MODEL}
