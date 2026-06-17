# Backend Local Development

Guide for running the FastAPI backend locally.

## Scope

**Phase 1 / Step 3** adds auth foundation utilities only:

- bcrypt password hashing (`hash_password`, `verify_password`)
- JWT access token create/decode (`create_access_token`, `decode_access_token`)
- Auth settings: `AUTH_SECRET_KEY`, `AUTH_ALGORITHM`, `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES`
- Pydantic schemas: `Token`, `TokenPayload`

No login/register API, no `password_hash` column, no migrations. `GET /health` is unchanged.

## Folder structure

```text
apps/backend/
├── alembic/
│   └── versions/
│       ├── 0001_baseline.py
│       └── 0002_core_saas_models.py
├── app/
│   ├── models/
│   │   ├── enums.py
│   │   ├── user.py
│   │   ├── workspace.py
│   │   └── workspace_membership.py
│   └── db/
├── scripts/
│   └── check_db_connection.py
└── tests/
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

Copy repository root `.env.example` to `.env` — **never commit `.env`**.

## Start PostgreSQL

```bash
cd ~/cxgeorgia
docker compose up -d postgres
docker compose ps
```

Do **not** use `docker compose down -v` unless you intentionally want to wipe local data.

## Alembic migrations

```bash
cd apps/backend
source .venv/bin/activate
alembic current
alembic upgrade head
alembic current
```

After Step 2, `alembic current` should show `0002 (head)`.

## Inspect tables

```bash
docker exec -it cx_postgres psql -U georgian_cx_user -d georgian_cx_platform -c "\dt"
```

## Database connectivity check

```bash
python scripts/check_db_connection.py
```

## Run tests

```bash
pytest
ruff check .
```

Unit tests do not require PostgreSQL.

## Run the server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Verify manually

| URL | Purpose |
|-----|---------|
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Health check (no DB check) |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI |

## What is intentionally not implemented

- `password_hash` on `users` (Step 4+)
- Login, registration, refresh tokens, protected routes
- User/workspace/membership API routes
- RBAC enforcement, permission engine
- Universal Case, customer, ticket models
- Seed data or admin users

## Related docs

- [Backend README](../../apps/backend/README.md)
- [Local Docker workflow](local-docker.md)
- [RBAC](../security/rbac.md)
