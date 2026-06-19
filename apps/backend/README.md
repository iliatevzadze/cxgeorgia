# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 64: Universal Cases list backend pagination)

`GET /api/v1/workspaces/{workspace_id}/cases` supports `limit` (default 50, max 100) and `offset` (default 0) pagination. Pagination combines with Step 60 filters. Response includes `items`, `total`, `limit`, and `offset`. Frontend consumes pagination from Step 65.

Phase 1 / Step 66 has **not started**.

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
| GET | `/api/v1/workspaces/{workspace_id}/cases` | List cases in workspace, newest first; optional filters (`status`, `priority`, `source`, `assigned_to_user_id`, `customer_id`, `sla_status`) and pagination (`limit`, `offset`); returns `items`, `total`, `limit`, `offset` |
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
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/attachments` | List case attachment metadata, oldest first (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/attachments` | Upload file and create attachment metadata (active members only) |
| DELETE | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/attachments/{attachment_id}` | Delete attachment metadata and stored file (active members only) |

## Case tag API (Phase 1 / Step 37)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/workspaces/{workspace_id}/case-tags` | List workspace case tags (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/case-tags` | Create workspace case tag (active members only) |
| PATCH | `/api/v1/workspaces/{workspace_id}/case-tags/{tag_id}` | Update tag name, slug and/or color (active members only) |
| DELETE | `/api/v1/workspaces/{workspace_id}/case-tags/{tag_id}` | Delete workspace case tag (active members only) |

## Operations API (Phase 1 / Step 46)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/workspaces/{workspace_id}/operations/dashboard` | Read-only operational aggregates (active members only) |

## Case QA API (Phase 1 / Step 48)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/qa-reviews` | List QA reviews for a case (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/qa-reviews` | Create QA review for a case (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/qa-reviews/{review_id}/criteria` | Add criterion score to a review (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/qa-reviews/{review_id}/approve` | Approve pending review (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/cases/{case_id}/qa-reviews/{review_id}/reject` | Reject pending review (active members only) |

## Agent Workforce API (Phase 1 / Step 50)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/agent-workforce/clock-in` | Start active shift for current user (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/agent-workforce/clock-out` | Close active shift for current user (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/agent-workforce/me/active-shift` | Current user's active shift or null (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/agent-workforce/active-shifts` | List active shifts in workspace (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/agent-workforce/case-metrics` | List agent case metrics with optional `user_id` / `case_id` filters (active members only) |

## Customer Records API (Phase 1 / Step 53)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/workspaces/{workspace_id}/customers` | List customers with optional `search` and `status` filters (active members only) |
| POST | `/api/v1/workspaces/{workspace_id}/customers` | Create customer (active members only) |
| GET | `/api/v1/workspaces/{workspace_id}/customers/{customer_id}` | Get customer by id (active members only) |
| PATCH | `/api/v1/workspaces/{workspace_id}/customers/{customer_id}` | Update customer, including archive via `status: archived` (active members only) |
| DELETE | `/api/v1/workspaces/{workspace_id}/customers/{customer_id}` | Hard-delete customer (active members only) |

Universal Cases may optionally include `customer_id` on create and PATCH. The customer must belong to the same workspace; deleting a customer sets linked case `customer_id` to null.

All case, comment, activity, tag and attachment endpoints require `Authorization: Bearer <token>` and active workspace membership.

File storage is configured via `STORAGE_ENDPOINT`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY` and `STORAGE_BUCKET_DEFAULT` (legacy `MINIO_*` env vars are also accepted).

Database tables: `universal_cases`, `case_comments`, `case_activities`, `case_tags`, `universal_case_tags`, `case_attachments`, `agent_shifts`, `agent_case_metrics`, `case_qa_reviews`, `case_qa_criteria_scores`, `customers`. Models: `UniversalCase`, `CaseComment`, `CaseActivity`, `CaseTag`, `UniversalCaseTag`, `CaseAttachment`, `AgentShift`, `AgentCaseMetric`, `CaseQaReview`, `CaseQaCriteriaScore`, `Customer`. Enums: `case_status`, `case_priority`, `case_source`, `case_activity_type`, `customer_status`. Universal Case SLA fields: `first_response_due_at`, `first_response_at`, `resolution_due_at`, `resolved_at`, `sla_status`. All case and activity rows include `workspace_id` for tenant isolation.

Case create, update, assignment changes, comment create/edit/delete automatically record `case_activities` rows. There is no public API to create or mutate activity records directly.

## Migrations

```bash
alembic upgrade head   # applies through 0014
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
