# Tech Stack

Confirmed technology choices for the Georgian CX Platform. All items below are **planned or accepted** — most are not installed or configured yet.

## Frontend

| Technology | Role |
|------------|------|
| **Next.js App Router** | React framework, routing, SSR/SSG |
| **React** | UI component library |
| **TypeScript** | Static typing |
| **next-intl** | Internationalization (default `ka`, secondary `en`) |

## Backend

| Technology | Role |
|------------|------|
| **FastAPI** | REST API framework |
| **Python 3.12+** | Backend and worker language |
| **SQLAlchemy async** | ORM with async session support |
| **asyncpg** | PostgreSQL async driver |
| **Alembic** | Database schema migrations |
| **Pydantic** | Request/response validation |

## Worker

| Technology | Role |
|------------|------|
| **Celery** | Distributed task queue |
| **Redis** | Celery broker and result backend |

## Data and storage

| Technology | Role |
|------------|------|
| **PostgreSQL** | Primary relational database |
| **Redis** | Cache, queue, pub/sub (later) |
| **MinIO** | S3-compatible object storage |

## Local development

| Technology | Role |
|------------|------|
| **Docker Compose** | Local service orchestration (Phase 0 / Step 2) |
| **Mailpit** | Local email capture and inspection |

## Testing (by phase)

| Technology | Role | When |
|------------|------|------|
| **pytest** | Backend unit and integration tests | Phase 1+ |
| **httpx** | Async HTTP client for API tests | Phase 1+ |
| **Playwright** | End-to-end browser tests | Phase 3+ |

## API conventions

- REST endpoints under `/api/v1/`
- Public resource IDs: UUIDs only
- Cursor-based pagination on list endpoints
- JWT access + HttpOnly refresh (Phase 1)

## Database conventions (future)

- All tenant-owned tables include `workspace_id`
- Alembic manages all schema changes — no manual DDL in production
- Migrations are reviewed and tested before merge

## What is not in the stack (yet)

- No AI/LLM services
- No billing provider (Stripe, etc.)
- No production CDN or Kubernetes
- No real SMTP in local development (Mailpit only)

## Related docs

- [Architecture overview](overview.md)
- [Decision: local-first stack](../decisions/0001-local-first-stack.md)
