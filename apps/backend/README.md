# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 33: Universal Case activity timeline frontend UI)

Activity timeline is visible on the case detail page in the frontend. Activity records remain **read-only** in the UI.

Comments can be created, listed and deleted through case-scoped backend endpoints. **Comment edit is not implemented yet.**

SLA, attachments, tags, and customer module are **not implemented**.

Phase 1 / Step 34 has **not started**.

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

## Universal Case API (Phase 1 / Steps 11–32)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/cases` | Create case (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/cases` | List cases in workspace, newest first |
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Case detail (workspace-scoped) |
| PATCH | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Update title, description, status, priority, source, customer metadata and assignment |
| DELETE | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Delete case (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments` | Create comment on case (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments` | List case comments, oldest first |
| DELETE | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments/{comment_id}` | Delete comment (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/activities` | List case activity timeline, newest first (active members only) |

All case, comment and activity endpoints require `Authorization: Bearer <token>` and active workspace membership.

Database tables: `universal_cases`, `case_comments`, `case_activities`. Models: `UniversalCase`, `CaseComment`, `CaseActivity`. Enums: `case_status`, `case_priority`, `case_source`, `case_activity_type`. All case and activity rows include `workspace_id` for tenant isolation.

Case create, update, assignment changes, and comment create/delete automatically record `case_activities` rows. There is no public API to create or mutate activity records directly.

## Migrations

```bash
alembic upgrade head   # applies through 0006
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
