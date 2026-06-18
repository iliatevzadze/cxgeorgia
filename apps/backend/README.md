# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 35: Universal Case comment edit frontend UI)

Comment body and `is_internal` can be updated via PATCH on case comments. The case detail frontend supports editing comments.

Comment edits record a read-only `case_updated` activity with message `"Comment edited"`.

SLA, attachments, tags, and customer module are **not implemented**.

Phase 1 / Step 36 has **not started**.

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

## Universal Case API (Phase 1 / Steps 11–34)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/cases` | Create case (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/cases` | List cases in workspace, newest first |
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Case detail (workspace-scoped) |
| PATCH | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Update title, description, status, priority, source, customer metadata and assignment |
| DELETE | `/api/v1/workspaces/{workspace_id}/cases/{case_id}` | Delete case (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments` | Create comment on case (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments` | List case comments, oldest first |
| PATCH | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments/{comment_id}` | Update comment body and/or internal visibility (active members only) |
| DELETE | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/comments/{comment_id}` | Delete comment (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/activities` | List case activity timeline, newest first (active members only) |

All case, comment and activity endpoints require `Authorization: Bearer <token>` and active workspace membership.

Database tables: `universal_cases`, `case_comments`, `case_activities`. Models: `UniversalCase`, `CaseComment`, `CaseActivity`. Enums: `case_status`, `case_priority`, `case_source`, `case_activity_type`. All case and activity rows include `workspace_id` for tenant isolation.

Case create, update, assignment changes, comment create/edit/delete automatically record `case_activities` rows. There is no public API to create or mutate activity records directly.

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
