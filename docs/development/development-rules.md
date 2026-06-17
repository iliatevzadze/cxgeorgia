# Development Rules

Mandatory rules for all contributors and AI coding agents working on the Georgian CX Platform.

## Core principles

### One safe step at a time

Each phase step delivers a small, verifiable increment. Do not combine unrelated work in a single change. Finish and verify one step before starting the next.

### No scope creep

If a task says "create folder structure," do not also scaffold FastAPI routes, database models, or UI screens. Stay within the approved step boundary.

### Broken steps must be fixed before moving forward

If a step fails acceptance criteria, fix it before proposing the next step. Do not accumulate deferred fixes.

## Phase boundaries

| Rule | Detail |
|------|--------|
| No real integrations before planned phases | Channel connectors start in Phase 5 (mock) and Phase 6 (real) |
| No AI before planned phases | AI features are not in the current roadmap phases |
| No billing before planned phases | Billing is explicitly deferred |
| No auth before Phase 1 | Registration, login, JWT, and RBAC code belong in Phase 1 |
| No Universal Case code before Phase 2 | Case models, APIs, and business rules start in Phase 2 |
| No UI-heavy MVP before Phase 3 | Agent workspace UI starts in Phase 3 |

## Security rules

- Security-sensitive tests **cannot be skipped**
- Tenant isolation tests are **mandatory from Phase 1 onward**
- RBAC permission tests are **mandatory from Phase 1 onward**
- Never commit `.env` files or real secrets
- Never expose sequential IDs as public resource identifiers
- API-layer authorization is required — UI hiding is not sufficient

## Code quality

- Match existing conventions in each app
- Type hints in Python; strict TypeScript in frontend
- All user-facing strings through next-intl (no hardcoded Georgian/English in components)
- Cursor-based pagination on all list endpoints (when APIs exist)
- No unbounded database queries

## Documentation

- All documentation in English
- Significant technical decisions recorded as ADRs in `docs/decisions/`
- Update docs when changing architecture or security boundaries

## What agents must not do unprompted

- Install dependencies outside an approved step
- Create Docker Compose files before Phase 0 / Step 2
- Implement features from a future phase
- Add third-party SDK integrations
- Create production deployment configuration
- Commit secrets or real credentials

## Related docs

- [Cursor workflow](cursor-workflow.md)
- [Product roadmap](../product/roadmap.md)
- [Security baseline](../security/security-baseline.md)
