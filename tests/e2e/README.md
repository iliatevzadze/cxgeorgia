# End-to-end tests

Cross-application E2E tests live in this directory. **No E2E tests exist yet.**

## Planned tooling

**Playwright** will be used for browser-based end-to-end tests covering critical user flows across the Next.js frontend and FastAPI backend.

## When E2E tests begin

E2E tests start in **later phases** when real UI flows exist:

| Phase | E2E scope |
|-------|-----------|
| Phase 1 | Auth flows (register, login, workspace switch) |
| Phase 3 | Case creation, assignment, resolution |
| Phase 6 | Channel import and webhook flows |

No E2E framework is installed in Phase 0.

## Mandatory coverage (future)

| Area | Requirement |
|------|-------------|
| Security-critical flows | Login, logout, token refresh, role enforcement |
| Tenant isolation | User in workspace A cannot access workspace B data |
| RBAC | Each role's permitted and denied actions |
| Critical agent workflows | Case lifecycle happy paths |

Tenant isolation and RBAC tests are **mandatory from Phase 1 onward**.

## Phase completion rule

**No phase is considered complete if its required tests fail.** This includes unit, integration, tenant isolation, permission, and E2E tests defined for that phase.

## Per-app tests

Unit and integration tests live inside each application:

- `apps/backend/tests/`
- `apps/frontend/` (when test setup is added)
- `apps/worker/tests/`

This directory is only for tests that span multiple apps or require a running browser.

## Related docs

- [Development rules](../../docs/development/development-rules.md)
- [Security baseline](../../docs/security/security-baseline.md)
- [Product roadmap](../../docs/product/roadmap.md)
