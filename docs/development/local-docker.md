# Local Docker Workflow

How to run the full Phase 0 Georgian CX Platform stack via Docker Compose.

## Overview

Seven services run via Docker Compose at the repository root:

```text
docker-compose.yml
├── postgres   → cx_postgres   (primary database — backend Alembic/SQLAlchemy)
├── redis      → cx_redis      (Celery broker)
├── minio      → cx_minio      (object storage — not used yet)
├── mailpit    → cx_mailpit    (local email testing)
├── backend    → cx_backend    (FastAPI /health)
├── frontend   → cx_frontend   (Next.js /ka, /en)
└── worker     → cx_worker     (Celery debug.ping)
```

All services share the `cx_platform_network` Docker network.

App containers run as non-root users: backend and worker use `appuser`; frontend uses the `node` user from `node:22-alpine`. Next.js telemetry is disabled in the Docker frontend container.

## Environment setup

```bash
cp .env.example .env
```

Key defaults:

| Variable | Default | Notes |
|----------|---------|-------|
| `FRONTEND_PORT` | `3001` | Host port → container `3000` |
| `BACKEND_PORT` | `8000` | Host port → container `8000` |
| `POSTGRES_HOST_PORT` | `15432` | Host → container `5432` |
| `REDIS_HOST_PORT` | `16379` | Host → container `6379` |
| `WORKER_REDIS_MODE` | `local` | Override to `docker` in Compose worker service |
| `BACKEND_DATABASE_MODE` | `local` | Override to `docker` in Compose backend service |

## Backend database (Phase 1)

Backend uses SQLAlchemy async + Alembic. Core SaaS tables (`users`, `workspaces`, `workspace_memberships`) are created by migration `0002`.

```bash
docker compose up -d postgres

cd apps/backend
source .venv/bin/activate
alembic upgrade head
python scripts/check_db_connection.py
```

Inspect tables:

```bash
docker exec -it cx_postgres psql -U georgian_cx_user -d georgian_cx_platform -c "\dt"
```

Compose sets `BACKEND_DATABASE_MODE=docker` for `cx_backend`. Host development uses `local` mode with `localhost:15432`.

Do **not** use `docker compose down -v` unless you intentionally want to wipe local data.

## Validate and start

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

Expected containers: `cx_postgres`, `cx_redis`, `cx_minio`, `cx_mailpit`, `cx_backend`, `cx_frontend`, `cx_worker`.

## URLs

| URL | Service |
|-----|---------|
| [http://localhost:8000/health](http://localhost:8000/health) | Backend health |
| [http://localhost:8000/docs](http://localhost:8000/docs) | Backend Swagger |
| [http://localhost:3001/ka](http://localhost:3001/ka) | Frontend (Georgian) |
| [http://localhost:3001/en](http://localhost:3001/en) | Frontend (English) |
| [http://localhost:9001](http://localhost:9001) | MinIO console |
| [http://localhost:8025](http://localhost:8025) | Mailpit |

## App container details

### Backend (`backend`)

- **Dockerfile:** `apps/backend/Dockerfile`
- **Runs as:** non-root `appuser`
- **Internal port:** `8000`
- **Health check:** `GET /health` (no database check)
- `BACKEND_DATABASE_MODE=docker` for PostgreSQL at `postgres:5432`
- Does not require Redis to start

### Frontend (`frontend`)

- **Dockerfile:** `apps/frontend/Dockerfile`
- **Runs as:** non-root `node`
- **Telemetry:** disabled (`NEXT_TELEMETRY_DISABLED=1`)
- **Internal port:** `3000`, **host port:** `3001`
- Runs Next.js dev server on `0.0.0.0:3000`
- Does not call backend API yet

### Worker (`worker`)

- **Dockerfile:** `apps/worker/Dockerfile`
- **Runs as:** non-root `appuser` (fixes Celery root-user `SecurityWarning`)
- **No host port**
- `WORKER_REDIS_MODE=docker` → `redis://redis:6379/0`
- Depends on healthy Redis service

## Logs

```bash
docker compose logs backend
docker compose logs frontend
docker compose logs worker
```

## Rebuild app images

```bash
docker compose build backend frontend worker
docker compose up -d backend frontend worker
```

## Stop safely

```bash
docker compose stop
docker compose down
```

Do **not** use `docker compose down -v` unless you want to wipe PostgreSQL, Redis, and MinIO data.

## Manual (non-Docker) development

You can still run apps directly on the host:

- Backend: [backend-local.md](backend-local.md)
- Frontend: [frontend-local.md](frontend-local.md)
- Worker: [worker-local.md](worker-local.md)

## What is not implemented

- ORM models, business tables, auth
- Frontend–backend API integration
- Real Celery jobs, Celery Beat
- MinIO buckets, email sending
- Production deployment

## Related docs

- [Docker Compose guide](../../infra/docker/README.md)
- [Infrastructure overview](../../infra/README.md)
