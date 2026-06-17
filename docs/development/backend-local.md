# Backend Local Development

Guide for running the FastAPI backend locally.

## Scope

**Phase 1 / Step 5** adds workspace bootstrap API:

- `POST /api/v1/workspaces` — create workspace (owner membership auto-created)
- `GET /api/v1/workspaces` — list your active workspaces
- `GET /api/v1/workspaces/{id}` — detail (members only, 404 otherwise)
- `GET /api/v1/workspaces/{id}/memberships` — active memberships

No frontend UI, invitations, or advanced RBAC yet.

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

## Start PostgreSQL

```bash
cd ~/cxgeorgia
docker compose up -d postgres
cd apps/backend && alembic upgrade head
```

Do **not** use `docker compose down -v` unless you intentionally want to wipe local data.

## Workspace API examples

```bash
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"founder@example.com","password":"StrongPass123"}')

TOKEN=$(python -c 'import json,sys; print(json.load(sys.stdin)["data"]["access_token"])' <<< "$LOGIN_RESPONSE")

curl -X POST http://127.0.0.1:8000/api/v1/workspaces \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Acme Support"}'

curl http://127.0.0.1:8000/api/v1/workspaces \
  -H "Authorization: Bearer $TOKEN"
```

## Tests

```bash
pytest
ruff check .
```

## Related docs

- [Backend README](../../apps/backend/README.md)
