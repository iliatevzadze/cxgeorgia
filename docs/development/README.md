# Development

Guide for contributors working on the Georgian CX Platform.

## Prerequisites (future)

When tooling is introduced, you will need:

- Node.js (LTS) — frontend
- Python 3.12+ — backend and worker
- Docker and Docker Compose — local services
- Git

Nothing is installable yet. This phase is structure and documentation only.

## Getting started (future)

Steps to be documented when Docker Compose and app scaffolding land:

1. Clone the repository
2. Copy environment templates (`.env.example` → `.env`)
3. Start infrastructure: `docker compose up`
4. Run database migrations
5. Start backend, worker, and frontend dev servers

## Environment variables (future)

All secrets and environment-specific values will live in `.env` files that are **never committed**. Example templates (`.env.example`) will be added per app and for Docker Compose.

## Code conventions (planned)

### Frontend

- TypeScript strict mode
- App Router file conventions
- next-intl for all user-facing strings (no hardcoded UI text)
- Default locale: `ka`

### Backend

- Python type hints throughout
- Pydantic schemas for request/response validation
- Async SQLAlchemy for database access
- API routes under `/api/v1/`

### Worker

- Celery tasks as plain functions in `worker/tasks/`
- Idempotent tasks where possible
- Shared models with backend (same database)

### Git workflow (suggested)

- `main` — stable, deployable
- Feature branches: `feature/<short-description>`
- Conventional commits encouraged but not enforced yet

## Related docs

- [Monorepo layout](../architecture/monorepo.md)
- [Security principles](../security/README.md)
