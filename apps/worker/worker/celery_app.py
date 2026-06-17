"""Celery application instance."""

from celery import Celery

from worker.core.config import get_settings

settings = get_settings()

celery_app = Celery("georgian_cx_worker")

celery_app.conf.update(
    broker_url=settings.redis_broker_url,
    result_backend=settings.redis_broker_url,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Tbilisi",
    enable_utc=True,
    task_track_started=True,
)

celery_app.autodiscover_tasks(["worker.tasks"])

# Ensure task modules are registered when the app is imported.
from worker.tasks import debug as _debug_tasks  # noqa: F401, E402
