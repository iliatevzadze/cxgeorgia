# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 19: Universal Case customer/source PATCH API)

Alembic head: `0004`. Create, list, detail, and PATCH endpoints exist for `universal_cases`. PATCH updates title, description, status, priority, source and customer metadata. **Frontend customer/source edit controls are not implemented yet.**

Assignment, delete, comments, timeline, SLA, attachments, tags, and customer module are **not implemented**.

Phase 1 / Step 20 has **not started**.

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

## Universal Case API (Phase 1 / Steps 11–19)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/cases` | Create case (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/cases` | List cases in workspace, newest first |
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Case detail (workspace-scoped) |
| PATCH | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Update title, description, status, priority, source and customer metadata |

All case endpoints require `Authorization: Bearer <token>` and active workspace membership.

Database table: `universal_cases`. Enums: `case_status`, `case_priority`, `case_source`. All rows include `workspace_id` for tenant isolation.

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

Workspace and Universal Case API tests require PostgreSQL (Docker Compose).

## Related docs

- [Backend local development](../../docs/development/backend-local.md)
- [RBAC](../../docs/security/rbac.md)
