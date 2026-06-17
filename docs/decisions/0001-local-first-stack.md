# ADR-0001: Local-first stack

## Status

Accepted

## Context

Georgian CX Platform is a zero-budget, local-first SaaS project for Georgian businesses. The team needs technology choices that:

- Run entirely on a developer laptop during early phases
- Support frontend, backend, and background jobs in one repository
- Scale to production without a full rewrite
- Prioritize Georgian language from day one
- Avoid vendor lock-in and recurring cloud costs during foundation work

## Decision

Adopt a **monorepo** with a **local-first infrastructure stack** orchestrated by Docker Compose (starting Phase 0 / Step 2).

### Repository layout

```text
apps/frontend, apps/backend, apps/worker
packages/shared
infra/{docker,postgres,redis,minio,mailpit}
docs/, scripts/, tests/e2e/
```

### Stack choices

| Layer | Choice |
|-------|--------|
| Frontend | Next.js App Router, React, TypeScript, next-intl |
| Backend | FastAPI, Python |
| ORM | SQLAlchemy async + asyncpg |
| Migrations | Alembic |
| Database | PostgreSQL |
| Worker | Celery + Redis |
| Cache / queue | Redis |
| File storage | MinIO |
| Dev email | Mailpit |
| Orchestration | Docker Compose |
| API | REST at `/api/v1/` |
| Auth (later) | JWT access + HttpOnly refresh |
| Public IDs | UUIDs only |
| Testing | pytest, httpx (Phase 1+), Playwright (Phase 3+) |

## Reasons

1. **Local-first** — PostgreSQL, Redis, MinIO, and Mailpit run locally via Docker with no cloud dependency.
2. **Proven stack** — FastAPI + SQLAlchemy async and Next.js are well-documented with strong typing.
3. **Georgian-first** — next-intl with `ka` as default locale is a first-class requirement.
4. **Monorepo** — One clone, one compose file, shared docs and types.
5. **Phased delivery** — Stack supports auth (Phase 1), cases (Phase 2), UI (Phase 3) without rework.

## Consequences

### Positive

- Developers can run the full stack locally at zero cost
- Clear separation: frontend (HTTP client), backend (API + auth), worker (async jobs)
- UUID public IDs and `workspace_id` tenant scoping are architectural defaults
- Cursor-based pagination and API-layer RBAC are documented before implementation

### Negative

- Celery adds operational complexity vs. simpler in-process tasks
- Monorepo requires coordinated CI when introduced
- Docker Compose must be maintained alongside application code
- No running application until Phase 0 / Step 2 and Phase 1 scaffolding

## What this decision does not include yet

- Docker Compose file (Phase 0 / Step 2)
- Installed dependencies (Phase 1)
- Database schema or migrations
- Authentication or RBAC code
- Universal Case business logic
- Production deployment configuration
- CI/CD pipelines
- Real third-party integrations

## Related

- [Architecture overview](../architecture/overview.md)
- [Tech stack](../architecture/tech-stack.md)
- [Product roadmap](../product/roadmap.md)
