from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "booked_table",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "expire_holds_every_minute": {
        "task": "app.workers.tasks.expire_holds",
        "schedule": 60.0,
    }
}
