# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 10: Universal Case database foundation)

Alembic head: `0004`. ORM model `UniversalCase` (`universal_cases` table) exists. **No Universal Case API, schemas, or service layer yet.**

Phase 1 / Step 11 has **not started**.

## Auth API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Bearer access token |
| GET | `/api/v1/auth/me` | Current user |

## Workspace API (Phase 1 / Step 5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workspaces` | Create workspace + owner membership |
| GET | `/api/v1/workspaces` | List current user's active workspaces |
| GET | `/api/v1/workspaces/{workspace_id}` | Workspace detail (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/memberships` | Active memberships (members only) |

All workspace endpoints require `Authorization: Bearer <token>`.

## Universal Case (Phase 1 / Step 10)

Database only — no HTTP API yet.

| Table | Purpose |
|-------|---------|
| `universal_cases` | Workspace-scoped customer issues/work items |

Enums: `case_status`, `case_priority`, `case_source`. All rows include `workspace_id` for tenant isolation.

## Migrations

```bash
alembic upgrade head   # applies through 0004
alembic current
```

## Tests

```bash
pytest
ruff check .
```

Workspace API tests require PostgreSQL (Docker Compose).

## Related docs

- [Backend local development](../../docs/development/backend-local.md)
- [RBAC](../../docs/security/rbac.md)
