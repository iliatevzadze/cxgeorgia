# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 0 — Project Foundation** (Step 3: backend skeleton)

Phase 1 has **not started**. No database, authentication, or business logic exists yet.

## What exists now

- FastAPI application with `GET /health`
- Pydantic Settings configuration (`app/core/config.py`)
- Response envelope: `{ "data", "meta", "error" }`
- pytest tests for health and OpenAPI metadata
- Runnable locally without Docker
- Docker container runs as non-root `appuser`

## What does not exist yet

- PostgreSQL / SQLAlchemy / Alembic
- Redis, MinIO, Mailpit integration
- Authentication, JWT, RBAC
- `/api/v1/` routes
- Universal Case, customer, or workspace logic

## Folder structure

```text
apps/backend/
├── app/
│   ├── api/
│   │   └── health.py       # GET /health
│   ├── core/
│   │   └── config.py       # Pydantic Settings
│   └── main.py             # FastAPI entrypoint
├── tests/
│   └── test_health.py
├── pyproject.toml
└── README.md
```

## Local setup

From `apps/backend`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Optional: copy the repository root `.env.example` to `apps/backend/.env` or use defaults built into `config.py`.

## Run tests

```bash
pytest
```

## Lint

```bash
ruff check .
```

## Run the backend

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health (no database check) |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | OpenAPI schema |

**Health URL:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## Docker (local development)

From repository root:

```bash
docker compose up -d --build backend
```

Backend URL: [http://localhost:8000/health](http://localhost:8000/health)

Dockerfile: `apps/backend/Dockerfile` (runs as non-root `appuser`)

Example response:

```json
{
  "data": {
    "status": "ok",
    "service": "backend",
    "app_name": "Georgian CX Platform",
    "environment": "local"
  },
  "meta": {},
  "error": null
}
```

## Planned stack (future phases)

- SQLAlchemy async + asyncpg + PostgreSQL
- Alembic migrations
- REST API under `/api/v1/`
- JWT access + HttpOnly refresh token
- UUID public IDs only

## Related docs

- [Backend local development](../../docs/development/backend-local.md)
