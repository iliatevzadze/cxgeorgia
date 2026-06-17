# Backend Local Development

Guide for running the FastAPI backend locally.

## Scope

**Phase 1 / Step 1** adds the database foundation only:

- SQLAlchemy async engine + session factory
- Alembic migrations (empty baseline)
- Database connectivity check script
- `GET /health` unchanged — no database dependency at startup

No authentication, ORM models, business tables, or `/api/v1/` routes yet.

## Folder structure

```text
apps/backend/
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_baseline.py
├── alembic.ini
├── app/
│   ├── main.py
│   ├── api/
│   │   └── health.py
│   ├── core/
│   │   └── config.py
│   └── db/
│       ├── base.py
│       └── session.py
├── scripts/
│   └── check_db_connection.py
├── tests/
│   ├── test_health.py
│   └── test_db_config.py
├── pyproject.toml
└── README.md
```

## Prerequisites

- Python 3.12+
- PostgreSQL via Docker Compose (for migrations and connectivity checks)

## Setup

```bash
cd apps/backend

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Environment variables

Copy the repository root `.env.example` to `.env` at the repo root (or `apps/backend/.env`). **Never commit `.env`.**

| Variable | Default | Notes |
|----------|---------|-------|
| `BACKEND_DATABASE_MODE` | `local` | Use `docker` inside Compose backend container |
| `BACKEND_DATABASE_URL_LOCAL` | (see `.env.example`) | Host PostgreSQL URL |
| `BACKEND_DATABASE_URL_DOCKER` | (see `.env.example`) | In-network PostgreSQL URL |
| `POSTGRES_HOST_PORT` | `15432` | Host port for local mode |
| `POSTGRES_*` | (see `.env.example`) | Used when explicit URLs are not set |

## Start PostgreSQL

```bash
cd ~/cxgeorgia
docker compose up -d postgres
docker compose ps
```

Do **not** use `docker compose down -v` unless you intentionally want to wipe local data.

## Alembic migrations

From `apps/backend` with venv active:

```bash
alembic current
alembic upgrade head
alembic current
```

The baseline migration (`0001_baseline`) creates no application tables. Alembic may create its own `alembic_version` tracking table.

## Database connectivity check

```bash
python scripts/check_db_connection.py
```

Expected output: `Database connection successful.`

This runs `SELECT 1` only — no data mutation.

## Run tests

```bash
pytest
```

Unit tests do not require PostgreSQL.

## Lint

```bash
ruff check .
```

## Run the server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The server starts even if PostgreSQL is temporarily unavailable.

## Verify manually

| URL | Purpose |
|-----|---------|
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Health check JSON |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI |

The health endpoint does **not** check PostgreSQL connectivity.

## What is intentionally not implemented

- ORM models, business tables, seed data
- Authentication, JWT, refresh tokens, RBAC
- `/api/v1/` versioned routes
- Universal Case, customer, workspace APIs
- Worker database access
- CORS configuration

## Related docs

- [Backend README](../../apps/backend/README.md)
- [Development rules](development-rules.md)
- [Local Docker workflow](local-docker.md)
