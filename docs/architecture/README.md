# Architecture

## Overview

Georgian CX Platform is a **monorepo** with three application services and shared infrastructure for local development.

```text
┌─────────────────────────────────────────────────────────────┐
│                        Monorepo                             │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│  frontend   │   backend   │   worker    │  packages/shared  │
│  (Next.js)  │  (FastAPI)  │  (Celery)   │  (contracts)      │
└──────┬──────┴──────┬──────┴──────┬──────┴───────────────────┘
       │             │             │
       │    REST     │             │ async tasks
       │  /api/v1/   │             │
       └────────────►│◄────────────┘
                     │
       ┌─────────────┼─────────────┬─────────────┐
       ▼             ▼             ▼             ▼
  PostgreSQL      Redis         MinIO        Mailpit
  (primary DB)  (cache/queue)  (files)     (dev email)
```

## Applications

### Frontend (`apps/frontend`)

- Next.js App Router with React and TypeScript
- next-intl for i18n (default locale: `ka`)
- Communicates with backend via REST at `/api/v1/`

### Backend (`apps/backend`)

- FastAPI application
- SQLAlchemy async ORM with asyncpg driver
- Alembic for schema migrations
- Serves versioned REST API

### Worker (`apps/worker`)

- Celery worker for background processing
- Shares database and Redis with backend
- Handles async jobs: email, webhooks, scheduled tasks (future)

### Shared (`packages/shared`)

- Cross-app types and API contracts (future)
- May host OpenAPI-generated client types

## Infrastructure (`infra/`)

Local service configuration placeholders. Docker Compose orchestration is planned for a later phase.

| Service | Role |
|---------|------|
| PostgreSQL | Persistent relational data |
| Redis | Celery broker, cache |
| MinIO | S3-compatible object storage |
| Mailpit | Local email simulation |

## API design (planned)

- REST, versioned at `/api/v1/`
- Resource identifiers: UUIDs only
- Authentication: JWT access + HttpOnly refresh cookie (not implemented)

## Data model (planned)

Core entities will center on:

- **Workspace** (tenant)
- **Customer** (profile + timeline)
- **Universal Case** (trackable work unit)
- **Customer Event** (timeline entry)
- **Message** (channel-specific content linked to cases/events)

No database models exist yet.

## Related docs

- [Monorepo layout](monorepo.md)
- [Security principles](../security/README.md)
- [ADR index](../decisions/README.md)
