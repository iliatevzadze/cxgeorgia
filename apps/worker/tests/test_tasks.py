"""Tests for debug tasks."""

from worker.celery_app import celery_app
from worker.tasks.debug import ping


def test_debug_ping_task_is_registered() -> None:
    assert "debug.ping" in celery_app.tasks


def test_debug_ping_returns_dict() -> None:
    result = ping()
    assert isinstance(result, dict)


def test_debug_ping_status() -> None:
    result = ping()
    assert result["status"] == "ok"


def test_debug_ping_service() -> None:
    result = ping()
    assert result["service"] == "worker"


def test_debug_ping_task_name() -> None:
    result = ping()
    assert result["task"] == "debug.ping"
