# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 40: Universal Case attachments database foundation)

The `case_attachments` table stores file metadata for Universal Cases.

Attachment upload/download API is **not implemented yet**.

SLA and customer module are **not implemented**.

Phase 1 / Step 41 has **not started**.

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

## Universal Case API (Phase 1 / Steps 11–37)

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
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/tags` | List tags attached to case (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/tags/{tag_id}` | Attach workspace tag to case (idempotent) |
| DELETE | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/tags/{tag_id}` | Detach tag from case (active members only) |

## Case tag API (Phase 1 / Step 37)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/workspaces/{workspace_id}/case-tags` | List workspace case tags (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/case-tags` | Create workspace case tag (active members only) |
| PATCH | `/api/v1/workspaces/{workspace_id}/case-tags/{tag_id}` | Update tag name, slug and/or color (active members only) |
| DELETE | `/api/v1/workspaces/{workspace_id}/case-tags/{tag_id}` | Delete workspace case tag (active members only) |

All case, comment, activity and tag endpoints require `Authorization: Bearer <token>` and active workspace membership.

Database tables: `universal_cases`, `case_comments`, `case_activities`, `case_tags`, `universal_case_tags`. Models: `UniversalCase`, `CaseComment`, `CaseActivity`, `CaseTag`, `UniversalCaseTag`. Enums: `case_status`, `case_priority`, `case_source`, `case_activity_type`. All case and activity rows include `workspace_id` for tenant isolation.

Case create, update, assignment changes, comment create/edit/delete automatically record `case_activities` rows. There is no public API to create or mutate activity records directly.

## Migrations

```bash
alembic upgrade head   # applies through 0009
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
