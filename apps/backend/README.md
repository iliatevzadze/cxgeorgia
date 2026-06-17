# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 1: database foundation)

Phase 1 / Step 2 has **not started**. No authentication, user/workspace models, or business logic exists yet.

## What exists now

- FastAPI application with `GET /health` (unchanged — no database check)
- Pydantic Settings configuration (`app/core/config.py`)
- SQLAlchemy async engine, session factory, declarative `Base`
- Alembic migrations with empty baseline revision `0001`
- Database connectivity check script
- Response envelope: `{ "data", "meta", "error" }`
- pytest tests for health, OpenAPI, and database config
- Docker container runs as non-root `appuser`

## What does not exist yet

- ORM models or business tables
- Authentication, JWT, RBAC
- `/api/v1/` routes
- Universal Case, customer, or workspace logic

## Folder structure

```text
apps/backend/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_baseline.py
├── alembic.ini
├── app/
│   ├── api/
│   │   └── health.py       # GET /health
│   ├── core/
│   │   └── config.py       # Pydantic Settings + database URL
│   ├── db/
│   │   ├── base.py         # Declarative Base
│   │   └── session.py      # async engine + get_async_session
│   └── main.py             # FastAPI entrypoint
├── scripts/
│   └── check_db_connection.py
├── tests/
│   ├── test_db_config.py
│   └── test_health.py
├── pyproject.toml
└── README.md
```

## Database URL modes

| `BACKEND_DATABASE_MODE` | When to use | Resolved URL source |
|-------------------------|-------------|---------------------|
| `local` (default) | Host terminal / pytest | `BACKEND_DATABASE_URL_LOCAL` or built from `POSTGRES_*` + `localhost:POSTGRES_HOST_PORT` |
| `docker` | Backend Docker container | `BACKEND_DATABASE_URL_DOCKER` or built from `POSTGRES_*` + `postgres:5432` |

Copy repository root `.env.example` to `.env` — **never commit `.env`**.

## Local setup

From `apps/backend`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Start PostgreSQL

From repository root:

```bash
docker compose up -d postgres
```

## Run migrations

From `apps/backend` with venv active:

```bash
alembic current
alembic upgrade head
alembic current
```

## Check database connectivity

Requires PostgreSQL running and migrations applied (or at least reachable DB):

```bash
python scripts/check_db_connection.py
```

## Run tests

Normal unit tests do **not** require PostgreSQL:

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

Compose sets `BACKEND_DATABASE_MODE=docker` for the backend service.

Backend URL: [http://localhost:8000/health](http://localhost:8000/health)

Dockerfile: `apps/backend/Dockerfile` (runs as non-root `appuser`)

## Related docs

- [Backend local development](../../docs/development/backend-local.md)
- [Local Docker workflow](../../docs/development/local-docker.md)
