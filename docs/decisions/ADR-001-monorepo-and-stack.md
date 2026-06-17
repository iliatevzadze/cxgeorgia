# ADR-001: Monorepo layout and confirmed stack

## Status

Accepted

## Context

Georgian CX Platform is a zero-budget, local-first SaaS project starting from scratch. We need a repository structure and technology choices that:

- Support a small team working on frontend, backend, and background jobs
- Run entirely on local infrastructure during early development
- Scale to production without a rewrite
- Prioritize Georgian language support from day one

## Decision

### Repository layout

Use a **monorepo** with:

- `apps/frontend` — Next.js App Router UI
- `apps/backend` — FastAPI REST API
- `apps/worker` — Celery background worker
- `packages/shared` — shared types and contracts
- `infra/` — local service configuration
- `docs/` — product, architecture, security, and ADR documentation

### Confirmed stack

| Concern | Choice |
|---------|--------|
| Frontend | Next.js App Router, React, TypeScript |
| i18n | next-intl (default `ka`, secondary `en`) |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy async + asyncpg |
| Migrations | Alembic |
| Worker | Celery + Redis |
| Cache / queue | Redis |
| File storage | MinIO |
| Dev email | Mailpit |
| Orchestration | Docker Compose (later phase) |
| API style | REST at `/api/v1/` |
| Auth | JWT access + HttpOnly refresh (later phase) |
| Public IDs | UUIDs only |

### Phase 0 scope

Phase 0 creates only the folder structure and documentation skeleton. No business logic, dependencies, or Docker Compose.

## Consequences

### Positive

- Clear separation of concerns from the start
- One repository for all services simplifies local development
- Documented stack reduces decision fatigue for future contributors
- Georgian-first i18n is a first-class requirement, not an afterthought

### Negative

- Monorepo tooling (shared linting, CI matrix) adds setup overhead in later phases
- Celery adds operational complexity compared to a simpler task queue
- No running application yet — developers must wait for Phase 1 scaffolding

## Related

- [Architecture overview](../architecture/README.md)
- [Monorepo layout](../architecture/monorepo.md)
