# Infrastructure

Local development infrastructure for the Georgian CX Platform. **Local development only** — not for production.

## Docker Compose

The root [`docker-compose.yml`](../docker-compose.yml) defines seven local services: four infrastructure services and three Phase 0 app containers.

## Services

### Infrastructure

| Service | Container | Image | Purpose |
|---------|-----------|-------|---------|
| `postgres` | `cx_postgres` | `postgres:16-alpine` | Future primary database |
| `redis` | `cx_redis` | `redis:7-alpine` | Celery broker, cache, pub/sub |
| `minio` | `cx_minio` | `minio/minio:latest` | S3-compatible object storage |
| `mailpit` | `cx_mailpit` | `axllent/mailpit:latest` | Local email capture |

### Application (Phase 0)

| Service | Container | Build context | Purpose |
|---------|-----------|---------------|---------|
| `backend` | `cx_backend` | `apps/backend` | FastAPI health check |
| `frontend` | `cx_frontend` | `apps/frontend` | Next.js dev server |
| `worker` | `cx_worker` | `apps/worker` | Celery worker (`debug.ping` only) |

## Local ports

| Service | Host port | Purpose |
|---------|-----------|---------|
| PostgreSQL | `15432` on host (configurable via `POSTGRES_HOST_PORT`) → `5432` inside container | Database connections from host machine |
| Redis | `16379` on host (configurable via `REDIS_HOST_PORT`) → `6379` inside container | Cache / queue from host machine |
| MinIO API | `9000` | S3-compatible API |
| MinIO Console | `9001` | Web admin UI — [http://localhost:9001](http://localhost:9001) |
| Mailpit SMTP | `1025` (configurable via `MAILPIT_SMTP_PORT`) | SMTP capture |
| Mailpit Web UI | `8025` (configurable via `MAILPIT_WEB_PORT`) | Inbox UI — [http://localhost:8025](http://localhost:8025) |
| Backend API | `8000` (`BACKEND_PORT`) | [http://localhost:8000/health](http://localhost:8000/health) |
| Frontend | `3001` on host → `3000` in container (`FRONTEND_PORT`) | [http://localhost:3001/ka](http://localhost:3001/ka) |
| Worker | none | Celery only — uses `redis:6379` on Docker network |

## Docker network

All services share a single bridge network:

```text
cx_platform_network
```

Future application containers connect to this network and reach services by Docker service name (`postgres`, `redis`, `minio`, `mailpit`, `backend`) — matching the hostnames in [`.env.example`](../.env.example).

Worker in Docker uses `WORKER_REDIS_MODE=docker` → `redis://redis:6379/0`. Worker on the host uses `WORKER_REDIS_MODE=local` → `redis://localhost:16379/0`.

**PostgreSQL port note:** Inside Docker, connect to `postgres:5432`. From the Ubuntu host (psql, GUI clients), connect to `localhost:15432`. `POSTGRES_PORT=5432` is the internal container port; `POSTGRES_HOST_PORT=15432` is the exposed host port.

**Redis port note:** Inside Docker, connect to `redis:6379`. From the Ubuntu host (redis-cli, GUI clients), connect to `localhost:16379`. `REDIS_PORT=6379` is the internal container port; `REDIS_HOST_PORT=16379` is the exposed host port.

## Named volumes

Persistent data survives container restarts and `docker compose down` (without `-v`):

| Volume | Mounted in | Purpose |
|--------|------------|---------|
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL data files |
| `redis_data` | `/data` | Redis AOF persistence |
| `minio_data` | `/data` | MinIO object storage |

## Environment variables

Copy [`.env.example`](../.env.example) to `.env` before starting services:

```bash
cp .env.example .env
```

**Never commit `.env`.** Values in `.env.example` are local-development placeholders only (`change_me_local_only`).

## Manual commands

From the repository root:

```bash
# Validate compose file (after copying .env)
cp .env.example .env
docker compose config

# Start full Phase 0 stack
docker compose up -d --build

# Infrastructure only (if needed)
# docker compose up -d postgres redis minio mailpit

# Check status
docker compose ps

# View logs
docker compose logs postgres
docker compose logs redis
docker compose logs minio
docker compose logs mailpit

# Stop containers (keeps volumes)
docker compose stop

# Remove containers and network (keeps volumes by default)
docker compose down
```

## Safety notes

- **Do not use `docker compose down -v`** unless you intentionally want to wipe all local database, Redis, and MinIO data.
- Default passwords in `.env.example` are for local development only — never use them in production.
- No TLS, no public networking, no cloud credentials — local port mappings only.
- This step does **not** create database schemas, MinIO buckets, Redis keys, or send test emails.

## Per-service directories

| Directory | Contents |
|-----------|----------|
| `docker/` | Docker Compose documentation |
| `postgres/` | Future init scripts (not created yet) |
| `redis/` | Future Redis config (not created yet) |
| `minio/` | Future bucket setup scripts (not created yet) |
| `mailpit/` | Future Mailpit config (not created yet) |

## Related docs

- [Docker Compose guide](docker/README.md)
- [Local Docker workflow](../docs/development/local-docker.md)
