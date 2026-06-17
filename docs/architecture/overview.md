# Architecture Overview

## Monorepo layout

Georgian CX Platform is a single repository containing all deployable applications, shared packages, infrastructure configuration, and documentation.

```text
.
├── apps/
│   ├── frontend/       # Next.js App Router UI
│   ├── backend/        # FastAPI REST API
│   └── worker/         # Celery background jobs
├── packages/
│   └── shared/         # Shared types and API contracts
├── infra/              # Per-service local config (Docker Compose in Step 2)
├── docs/               # Product, architecture, security, ADRs
├── scripts/            # Dev and ops helper scripts
└── tests/e2e/          # Cross-app end-to-end tests
```

See also [monorepo.md](monorepo.md) for conventions and dependency direction.

## Application separation

```text
┌─────────────┬─────────────┬─────────────┬───────────────────┐
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
```

### Frontend (`apps/frontend`)

- Next.js App Router, React, TypeScript
- Communicates with backend only via HTTP (no direct database access)
- next-intl for Georgian and English UI

### Backend (`apps/backend`)

- FastAPI application serving REST endpoints
- SQLAlchemy async with asyncpg for PostgreSQL
- Alembic for schema migrations
- Authoritative source for auth, RBAC, and business rules

### Worker (`apps/worker`)

- Celery worker sharing the backend database and Redis
- Background jobs: email delivery, imports, scheduled tasks (future)
- No HTTP API surface

Apps must not import from each other directly. The frontend calls the backend over HTTP; the worker reads/writes the same database.

## Infrastructure services

| Service | Role |
|---------|------|
| **PostgreSQL** | Primary relational data store. All tenant-owned tables include `workspace_id`. |
| **Redis** | Celery broker and result backend. Caching and real-time pub/sub later. |
| **MinIO** | S3-compatible object storage for attachments and exports. |
| **Mailpit** | Local SMTP capture for development — no real email in early phases. |

Docker Compose orchestration is planned for Phase 0 / Step 2. No compose file exists yet.

## Future API boundary

- **Style:** REST, versioned at `/api/v1/`
- **IDs:** UUIDs only for public-facing resource identifiers
- **Auth:** JWT access token in `Authorization` header; refresh token in HttpOnly cookie (Phase 1)
- **Pagination:** Cursor-based pagination on all list endpoints (no unbounded queries)
- **Errors:** Structured error responses; no stack traces in production

The frontend is a client of `/api/v1/`. All authorization is enforced at the API layer, not inferred from UI visibility.

## Future data model direction

Core entities (not implemented yet):

- Workspace (tenant boundary)
- User, membership, role
- Customer (profile + timeline)
- Universal Case (trackable work unit)
- Customer Event (timeline entry)
- Message (channel content linked to cases)

## Related docs

- [Tech stack](tech-stack.md)
- [Security baseline](../security/security-baseline.md)
- [RBAC](../security/rbac.md)
