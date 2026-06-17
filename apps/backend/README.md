# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 2: core SaaS database models)

Phase 1 / Step 3 has **not started**. No authentication, API routes, or business logic exists yet.

## What exists now

- FastAPI application with `GET /health` (unchanged — no database check)
- Pydantic Settings configuration (`app/core/config.py`)
- SQLAlchemy async engine, session factory, declarative `Base`
- Core SaaS ORM models: `User`, `Workspace`, `WorkspaceMembership`
- Alembic migrations: `0001` baseline, `0002` core SaaS tables
- Database connectivity check script
- pytest tests for health, database config, and model metadata
- Docker container runs as non-root `appuser`

## Core SaaS tables (Phase 1 / Step 2)

| Table | Purpose |
|-------|---------|
| `users` | Platform user (`email` unique; no password field yet) |
| `workspaces` | Tenant workspace (`slug` unique) |
| `workspace_memberships` | User ↔ workspace link with role |

**Membership roles (minimal):** `owner`, `admin`, `member`

No authentication, password hashing, JWT, API endpoints, or seed data exists yet.

## What does not exist yet

- Password fields, login, registration, JWT
- RBAC enforcement, permission checks
- `/api/v1/` routes
- Universal Case, customer, or ticket models

## Folder structure

```text
apps/backend/
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 0001_baseline.py
│       └── 0002_core_saas_models.py
├── alembic.ini
├── app/
│   ├── api/
│   │   └── health.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── enums.py
│   │   ├── user.py
│   │   ├── workspace.py
│   │   └── workspace_membership.py
│   └── main.py
├── scripts/
│   └── check_db_connection.py
├── tests/
│   ├── test_core_saas_models.py
│   ├── test_db_config.py
│   ├── test_health.py
│   └── test_models_metadata.py
├── pyproject.toml
└── README.md
```

## Run migrations

From repository root, start PostgreSQL:

```bash
docker compose up -d postgres
```

From `apps/backend` with venv active:

```bash
alembic current
alembic upgrade head
alembic current
```

## Inspect tables

```bash
docker exec -it cx_postgres psql -U georgian_cx_user -d georgian_cx_platform -c "\dt"
```

Expected after `0002`: `alembic_version`, `users`, `workspaces`, `workspace_memberships`

## Run tests

Normal unit tests do **not** require PostgreSQL:

```bash
pytest
ruff check .
```

## Related docs

- [Backend local development](../../docs/development/backend-local.md)
- [Local Docker workflow](../../docs/development/local-docker.md)
- [RBAC](../../docs/security/rbac.md)
