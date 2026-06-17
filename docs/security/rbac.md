# Role-Based Access Control (RBAC)

Planned workspace-scoped roles for the Georgian CX Platform. **No RBAC code exists yet.** Implementation is planned for Phase 1.

## Scope

RBAC applies within a **workspace** (tenant). A user can belong to multiple workspaces with a **different role in each**.

## Roles

Phase 1 / Step 2 stores minimal tenant roles on `workspace_memberships.role`. Step 5 allows authenticated users to create workspaces and receive `owner` membership automatically. **No RBAC enforcement or invitation flow exists yet.**

### Owner (planned enforcement)

The workspace creator and ultimate authority.

| Permission area | Access |
|-----------------|--------|
| Workspace settings | Full — name, locale, configuration |
| Member management | Full — invite, remove, change roles |
| Billing (future) | Full |
| Cases and customers | Full |
| Analytics (future) | Full |
| Audit log | Read |
| Delete workspace | Yes (sole Owner only) |

**Constraints:**

- Every workspace must have exactly one Owner at all times.
- The Owner **cannot be removed** without transferring ownership first.
- Role changes involving Owner transfer must be recorded in the audit log.

### Admin

Day-to-day workspace administration without ownership transfer.

| Permission area | Access |
|-----------------|--------|
| Workspace settings | Read and update (except ownership transfer) |
| Member management | Invite, remove, change roles (except Owner) |
| Cases and customers | Full |
| Analytics (future) | Full |
| Audit log | Read |
| Delete workspace | No |

### Agent

Primary support role — handles cases and communicates with customers.

| Permission area | Access |
|-----------------|--------|
| Workspace settings | Read only |
| Member management | No |
| Cases and customers | Create, read, update, assign (within workspace) |
| Analytics (future) | Read own metrics |
| Audit log | No |
| Delete workspace | No |

### Viewer

Read-only access for managers, auditors, or observers.

| Permission area | Access |
|-----------------|--------|
| Workspace settings | Read only |
| Member management | No |
| Cases and customers | Read only |
| Analytics (future) | Read |
| Audit log | No |
| Delete workspace | No |

## Enforcement rules (planned)

1. **Every API endpoint** must verify workspace membership and role before processing the request.
2. **Frontend visibility is not security** — the API must reject unauthorized requests regardless of what the UI shows.
3. **Role changes** must be recorded in the audit log with actor, target, old role, and new role.
4. **Object-level checks** — even with the correct role, users must not access resources outside their workspace (`workspace_id` filter on every query).
5. **Owner protection** — APIs must reject attempts to remove or demote the sole Owner without a valid ownership transfer.

## Multi-workspace membership

```text
User A
├── Workspace 1 → Owner
├── Workspace 2 → Agent
└── Workspace 3 → Viewer
```

JWT or session context must include the **active workspace** for each request. Switching workspaces changes the effective role.

## Status

`workspace_memberships` and core SaaS tables exist (Phase 1 / Step 2). RBAC middleware, permission decorators, and API enforcement are **not** implemented. See Phase 1 in the [roadmap](../product/roadmap.md).

## Related docs

- [Security baseline](security-baseline.md)
- [Development rules](../development/development-rules.md)
