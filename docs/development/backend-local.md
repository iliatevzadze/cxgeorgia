# Backend Local Development

Guide for running the FastAPI backend skeleton locally (Phase 0 / Step 3).

## Scope

This backend is a **minimal skeleton**:

- Configuration via Pydantic Settings
- `GET /health` endpoint
- pytest tests
- No database, Redis, MinIO, Mailpit, auth, or business logic

The backend runs **without Docker**. Infrastructure services (PostgreSQL, etc.) are not required for this step.

## Folder structure

```text
apps/backend/
├── app/
│   ├── __init__.py
│   ├── main.py             # create_app() + app instance
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py       # GET /health
│   └── core/
│       ├── __init__.py
│       └── config.py       # Settings (APP_ENV, APP_NAME, ...)
├── tests/
│   ├── __init__.py
│   └── test_health.py
├── pyproject.toml
└── README.md
```

## Prerequisites

- Python 3.12+
- No Docker required for the backend skeleton

## Setup

```bash
cd apps/backend

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Environment variables

Settings load from environment variables or an optional `apps/backend/.env` file. Defaults match the repository root [`.env.example`](../../.env.example):

| Variable | Default |
|----------|---------|
| `APP_ENV` | `local` |
| `APP_NAME` | `Georgian CX Platform` |
| `BACKEND_PORT` | `8000` |
| `DEFAULT_LOCALE` | `ka` |
| `SUPPORTED_LOCALES` | `ka,en` |

Database, Redis, MinIO, and JWT variables are **not loaded** in this step.

## Run tests

```bash
pytest
```

## Lint

```bash
ruff check .
```

## Run the server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Verify manually

| URL | Purpose |
|-----|---------|
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Health check JSON |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | OpenAPI schema |

### Health response envelope

All future API responses will use:

```json
{
  "data": { ... },
  "meta": { ... },
  "error": null
}
```

Current health response:

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

The health endpoint does **not** check PostgreSQL, Redis, MinIO, or Mailpit connectivity.

## What is intentionally not implemented

- SQLAlchemy, Alembic, database models, migrations
- PostgreSQL / Redis / MinIO / Mailpit connections
- Authentication, JWT, refresh tokens, RBAC
- `/api/v1/` versioned routes
- Universal Case, customer, workspace APIs
- Backend Docker container
- CORS configuration

## Related docs

- [Backend README](../../apps/backend/README.md)
- [Development rules](development-rules.md)
- [Local Docker workflow](local-docker.md)
