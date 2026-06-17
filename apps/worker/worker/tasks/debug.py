"""Safe debug tasks for local worker verification."""

from worker.celery_app import celery_app


@celery_app.task(name="debug.ping")
def ping() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "worker",
        "task": "debug.ping",
    }
