"""Tests for the health endpoint and OpenAPI metadata."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_envelope() -> None:
    response = client.get("/health")
    body = response.json()

    assert set(body.keys()) == {"data", "meta", "error"}
    assert body["error"] is None
    assert isinstance(body["meta"], dict)


def test_health_data_fields() -> None:
    response = client.get("/health")
    data = response.json()["data"]

    assert data["status"] == "ok"
    assert data["service"] == "backend"
    assert data["app_name"] == "Georgian CX Platform"
    assert data["environment"] == "local"


def test_openapi_json_returns_200() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200


def test_openapi_title() -> None:
    response = client.get("/openapi.json")
    assert response.json()["info"]["title"] == "Georgian CX Platform API"
