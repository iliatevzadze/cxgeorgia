# Backend

FastAPI REST API for the Georgian CX Platform.

## Current phase

**Phase 1 — SaaS Base** (Step 5: workspace bootstrap API)

Phase 1 / Step 6 has **not started**. No frontend workspace UI, invitations, or advanced RBAC.

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

Creating a workspace automatically assigns the current user `owner` role. Slugs are generated from the workspace name (`acme-support`, `acme-support-2`, …).

No invitation flow, workspace switcher UI, or advanced RBAC yet.

## Manual curl examples

```bash
# Login first, then:
curl -X POST http://localhost:8000/api/v1/workspaces \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Acme Support"}'

curl http://localhost:8000/api/v1/workspaces \
  -H "Authorization: Bearer $TOKEN"
```

## Migrations

Alembic head: `0003` (no new migration in Step 5).

## Tests

```bash
pytest
ruff check .
```

Workspace API tests require PostgreSQL (Docker Compose).

## Related docs

- [Backend local development](../../docs/development/backend-local.md)
- [RBAC](../../docs/security/rbac.md)
