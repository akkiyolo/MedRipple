from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "medripple_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.email_tasks",
        "app.workers.reminder_tasks",
        "app.workers.ai_tasks",
        "app.workers.calendar_tasks",
        "app.workers.cleanup_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)
