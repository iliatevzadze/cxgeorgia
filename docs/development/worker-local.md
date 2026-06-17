# Worker Local Development

Guide for running the Celery worker skeleton locally (Phase 0 / Step 5).

## Scope

This worker is a **minimal skeleton**:

- Celery application with Redis broker/result backend
- Pydantic Settings for configuration
- One safe debug task (`debug.ping`)
- pytest tests that do not require Redis

No database, email, scheduling, or business logic exists yet.

## Folder structure

```text
apps/worker/
├── worker/
│   ├── celery_app.py       # georgian_cx_worker Celery app
│   ├── core/
│   │   └── config.py       # APP_ENV, Redis URLs
│   └── tasks/
│       └── debug.py        # debug.ping
├── tests/
│   ├── test_config.py
│   └── test_tasks.py
├── pyproject.toml
└── README.md
```

## Prerequisites

- Python 3.12+
- Redis running locally (Docker Compose service on `localhost:16379`) — **only for live worker verification**, not for unit tests

## Setup

```bash
cd apps/worker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No `.env` file is required; defaults match the repository root [`.env.example`](../../.env.example).

## Run tests

```bash
pytest
```

Tests call the `ping` task function directly and do **not** enqueue jobs to Redis.

## Lint

```bash
ruff check .
```

## Redis configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `REDIS_HOST` | `redis` | Docker service name (future) |
| `REDIS_PORT` | `6379` | Internal container port |
| `WORKER_REDIS_MODE` | `local` | `local` = host Redis; `docker` = Compose Redis |

| URL property | Value | When |
|--------------|-------|------|
| `redis_broker_url_local` | `redis://localhost:16379/0` | Worker on host machine |
| `redis_broker_url_docker` | `redis://redis:6379/0` | Future Docker worker |

Compose sets `WORKER_REDIS_MODE=docker` on the worker service.

## Docker (local development)

From repository root:

```bash
docker compose up -d --build worker
docker compose logs worker
```

No host port. Requires Redis service healthy in Compose.

## Start Celery worker manually

From `apps/worker` with virtualenv active and Redis running:

```bash
celery -A worker.celery_app:celery_app worker --loglevel=INFO
```

### Optional: call debug task via Celery (requires Redis + running worker)

```bash
celery -A worker.celery_app:celery_app call debug.ping
```

Expected result:

```json
{
  "status": "ok",
  "service": "worker",
  "task": "debug.ping"
}
```

## What is intentionally not implemented

- Celery Beat / cron-style scheduling
- Real background jobs (email, imports, SLA, notifications)
- PostgreSQL, SQLAlchemy, Alembic
- MinIO and Mailpit integration
- Auth, RBAC, workspace, Universal Case tasks
- Worker Docker container in Compose

## Related docs

- [Worker README](../../apps/worker/README.md)
- [Local Docker workflow](local-docker.md)
- [Development rules](development-rules.md)
