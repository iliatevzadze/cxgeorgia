# Backend Local Development

Guide for running the FastAPI backend locally.

## Scope

**Phase 1 / Step 4** adds the backend auth API:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- Migration `0003` adds `users.password_hash`

No frontend auth UI, refresh tokens, email verification, or workspace creation on registration.

## Prerequisites

- Python 3.12+
- PostgreSQL via Docker Compose

## Setup

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Copy repository root `.env.example` to `.env` — **never commit `.env`**.

## Start PostgreSQL and migrate

```bash
cd ~/cxgeorgia
docker compose up -d postgres

cd apps/backend
source .venv/bin/activate
alembic upgrade head
```

Do **not** use `docker compose down -v` unless you intentionally want to wipe local data.

## Run the server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Auth API examples

Register:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"founder@example.com","password":"StrongPass123","full_name":"Founder"}'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"founder@example.com","password":"StrongPass123"}'
```

Current user:

```bash
curl http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Tests

```bash
pytest
ruff check .
```

Auth API integration tests require PostgreSQL to be running.

## What is not implemented

- Refresh tokens, logout, password reset, email verification
- Workspace creation on registration
- RBAC enforcement beyond authenticated `/me`
- Frontend auth UI

## Related docs

- [Backend README](../../apps/backend/README.md)
- [Security baseline](../security/security-baseline.md)
