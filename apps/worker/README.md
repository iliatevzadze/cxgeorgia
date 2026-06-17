# Worker

Celery worker for asynchronous background jobs in the Georgian CX Platform.

## Current phase

**Phase 0 — Project Foundation** (Step 5: worker skeleton)

Phase 1 has **not started**. No real jobs, scheduler, database access, or email sending exist yet.

## What exists now

- Celery application `georgian_cx_worker`
- Redis broker and result backend configuration (local: `localhost:16379`)
- Pydantic Settings (`worker/core/config.py`)
- Safe debug task: `debug.ping`
- pytest tests (no Redis required)
- Runnable locally from `apps/worker`
- Docker container runs as non-root `appuser` (no Celery root-user warning)

## What does not exist yet

- Celery Beat / scheduled tasks
- Real background jobs (email, imports, SLA, notifications)
- PostgreSQL, MinIO, Mailpit integration
- Auth, RBAC, workspace, Universal Case logic

## Folder structure

```text
apps/worker/
├── worker/
│   ├── celery_app.py       # Celery entrypoint
│   ├── core/
│   │   └── config.py       # Settings + Redis URLs
│   └── tasks/
│       └── debug.py        # debug.ping task
├── tests/
│   ├── test_config.py
│   └── test_tasks.py
├── pyproject.toml
└── README.md
```

## Redis connection notes

| `WORKER_REDIS_MODE` | Redis URL |
|---------------------|-----------|
| `local` (default) | `redis://localhost:16379/0` |
| `docker` (Compose) | `redis://redis:6379/0` |

Ensure Redis is running before starting a live Celery worker on the host:

```bash
docker compose ps   # from repository root
```

## Docker (local development)

From repository root:

```bash
docker compose up -d --build worker
docker compose logs worker
```

Compose sets `WORKER_REDIS_MODE=docker`. No host port is exposed.

Dockerfile: `apps/worker/Dockerfile` (runs as non-root `appuser`)

## Local setup

```bash
cd apps/worker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

## Lint

```bash
ruff check .
```

## Start Celery worker manually

Requires Redis at `localhost:16379`:

```bash
celery -A worker.celery_app:celery_app worker --loglevel=INFO
```

### Optional: dispatch debug task (requires running worker + Redis)

In a separate terminal with the same virtualenv:

```bash
celery -A worker.celery_app:celery_app call debug.ping
```

## Debug task response

```json
{
  "status": "ok",
  "service": "worker",
  "task": "debug.ping"
}
```

## Related docs

- [Worker local development](../../docs/development/worker-local.md)
