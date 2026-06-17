# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 4: backend auth API)

Phase 1 / Step 5 has **not started**. No refresh tokens, email verification, password reset, or frontend auth UI.

## What exists now

- FastAPI application with `GET /health` (unchanged — no database check)
- Auth API under `/api/v1/auth`: register, login, current user
- `password_hash` on `users` (migration `0003`)
- bcrypt password hashing and JWT access tokens
- Core SaaS models: `User`, `Workspace`, `WorkspaceMembership`
- Alembic migrations through `0003`

## Auth API (Phase 1 / Step 4)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account (returns `UserRead`) |
| POST | `/api/v1/auth/login` | Returns bearer `access_token` |
| GET | `/api/v1/auth/me` | Current user (`Authorization: Bearer`) |

Responses use the standard envelope: `{ "data", "meta", "error" }`.

No refresh tokens, logout, email verification, password reset, or workspace creation on registration.

## Manual curl examples

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"founder@example.com","password":"StrongPass123","full_name":"Founder"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"founder@example.com","password":"StrongPass123"}'

TOKEN="paste_access_token_here"
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Migrations

```bash
docker compose up -d postgres
cd apps/backend && source .venv/bin/activate
alembic upgrade head
```

## Tests

Auth API tests require PostgreSQL (Docker Compose). Unit tests for models/utilities do not.

```bash
pytest
ruff check .
```

## Related docs

- [Backend local development](../../docs/development/backend-local.md)
- [Security baseline](../../docs/security/security-baseline.md)
