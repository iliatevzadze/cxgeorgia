# Docker Compose

Instructions for running the full Phase 0 local stack via the root [`docker-compose.yml`](../../docker-compose.yml).

## Prerequisites

- Docker Engine and Docker Compose v2 installed on your machine
- Repository cloned locally

## First-time setup

1. Copy environment template (creates your local `.env` — never commit it):

```bash
cp .env.example .env
```

2. Validate the Compose file:

```bash
docker compose config
```

## Start full stack

Build and start infrastructure + app containers:

```bash
docker compose up -d --build
```

Expected containers:

| Container | Service | Host access |
|-----------|---------|-------------|
| `cx_postgres` | postgres | `localhost:15432` → container `5432` |
| `cx_redis` | redis | `localhost:16379` → container `6379` |
| `cx_minio` | minio | `localhost:9000`, console `9001` |
| `cx_mailpit` | mailpit | SMTP `1025`, web UI `8025` |
| `cx_backend` | backend | `localhost:8000` |
| `cx_frontend` | frontend | `localhost:3001` → container `3000` |
| `cx_worker` | worker | no host port (uses `redis:6379` internally) |

App containers (`cx_backend`, `cx_frontend`, `cx_worker`) run as non-root users. The Celery worker no longer logs the root-user `SecurityWarning`. Next.js telemetry is disabled in the Docker frontend container (`NEXT_TELEMETRY_DISABLED=1`).

## Browser and API checks

| URL | Purpose |
|-----|---------|
| [http://localhost:8000/health](http://localhost:8000/health) | Backend health |
| [http://localhost:8000/docs](http://localhost:8000/docs) | Backend Swagger UI |
| [http://localhost:3001/ka](http://localhost:3001/ka) | Frontend (Georgian) |
| [http://localhost:3001/en](http://localhost:3001/en) | Frontend (English) |
| [http://localhost:9001](http://localhost:9001) | MinIO console |
| [http://localhost:8025](http://localhost:8025) | Mailpit web UI |

## Check service status

```bash
docker compose ps
```

## View logs

```bash
docker compose logs backend
docker compose logs frontend
docker compose logs worker
docker compose logs postgres
docker compose logs redis
```

Follow logs in real time:

```bash
docker compose logs -f <service-name>
```

## Rebuild app containers

After code changes to backend, frontend, or worker:

```bash
docker compose build backend frontend worker
docker compose up -d backend frontend worker
```

Or rebuild everything:

```bash
docker compose up -d --build
```

## Stop services safely

**Stop containers (preserves volumes):**

```bash
docker compose stop
```

**Remove containers and network (preserves named volumes by default):**

```bash
docker compose down
```

## Warning: wiping local data

```bash
# DO NOT run unless you intentionally want to delete all local data
docker compose down -v
```

The `-v` flag deletes named volumes (`postgres_data`, `redis_data`, `minio_data`).

## Troubleshooting

| Problem | Command |
|---------|---------|
| Check running containers | `docker compose ps` |
| Inspect service logs | `docker compose logs <service-name>` |
| Rebuild one app | `docker compose build <service>` |
| Validate config | `docker compose config` |
| Port already in use | Adjust `POSTGRES_HOST_PORT`, `REDIS_HOST_PORT`, `FRONTEND_PORT`, or `BACKEND_PORT` in `.env` |

## What is not included yet

- PostgreSQL schemas or migrations
- Auth, RBAC, Universal Case APIs
- Frontend–backend API integration
- MinIO bucket creation
- Celery Beat / scheduled jobs
- Production deployment or TLS

## Related docs

- [Infrastructure overview](../README.md)
- [Local Docker workflow](../../docs/development/local-docker.md)
