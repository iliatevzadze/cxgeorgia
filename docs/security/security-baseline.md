# Security Baseline

Security principles and planned controls for the Georgian CX Platform.

**Nothing is implemented yet.** This document defines mandatory requirements for all future phases.

## Secrets and configuration

| Rule | Detail |
|------|--------|
| No secrets in code | API keys, passwords, and tokens must never appear in source files |
| `.env` must never be committed | Real environment values live only in local `.env` (gitignored) |
| `.env.example` is allowed | Must contain **placeholder values only** — e.g. `change_me_local_only` |
| Production secrets | Environment variables or secret manager (future) |

## Identifiers

- All public-facing resource IDs must be **UUIDs**
- Sequential integer IDs must never appear in URLs or API responses
- Internal surrogate keys (if used) remain private to the database

## Authentication (planned — Phase 1)

| Control | Requirement |
|---------|-------------|
| Password hashing | bcrypt with minimum cost factor **12** |
| Access tokens | Short-lived JWT (default 15 minutes) |
| Refresh tokens | Stored in **HttpOnly**, Secure, SameSite cookies — never in localStorage |
| Token rotation | To be finalized in Phase 1 implementation |

## Authorization (planned — Phase 1)

- **RBAC enforced at the API layer** — every endpoint checks workspace membership and role
- **Object-level authorization** — users can only access resources in their workspace
- **Frontend visibility is not security** — hiding UI elements does not replace server-side checks

## Audit and monitoring (planned)

- Every sensitive action must be **audit-logged** (role changes, case assignment, data export, etc.)
- Auth endpoints must have **rate limiting**
- Structured error responses must **not leak stack traces** in production

## Data access (planned)

- All list endpoints must use **pagination** (cursor-based)
- **No unbounded queries** — every list request has a maximum page size
- All tenant-owned tables include `workspace_id`
- Queries must always filter by workspace

## Testing requirements

| Requirement | From |
|-------------|------|
| Tenant isolation tests | Phase 1 onward — mandatory |
| RBAC permission tests | Phase 1 onward — mandatory |
| Auth rate-limit tests | Phase 1 onward |
| Security-sensitive tests cannot be skipped | All phases |

## Dependency security

- Pin dependency versions when tooling is introduced
- Run `npm audit` and `pip-audit` in CI (when CI is added)
- No known-critical vulnerabilities in production dependencies

## Reporting vulnerabilities

Process to be defined before any production deployment.

## Related docs

- [RBAC roles](rbac.md)
- [Development rules](../development/development-rules.md)
- [Architecture overview](../architecture/overview.md)
