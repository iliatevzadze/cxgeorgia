# Product Roadmap

Phased delivery plan for the Georgian CX Platform. Each phase has a clear scope boundary. Do not skip ahead.

## Phase 0 — Project Foundation

**Status: In progress**

- Monorepo folder structure
- Documentation skeleton
- `.env.example`, `.gitignore`, `.editorconfig`
- No dependencies, Docker Compose, or application code

**Definition of done:** All required folders, docs, and safety files exist. No business logic. Ready for Phase 0 / Step 2 (Docker Compose).

## Phase 1 — SaaS Base

- Docker Compose local services (PostgreSQL, Redis, MinIO, Mailpit)
- FastAPI and Next.js scaffolding with dependencies
- User registration and login
- JWT access token + HttpOnly refresh token
- Workspace creation and membership
- RBAC enforcement (Owner, Admin, Agent, Viewer)
- Tenant isolation tests
- Alembic migrations for core auth/workspace tables

## Phase 2 — Universal Case Core

- Universal Case and Customer Event data models
- Customer profile and timeline
- Case CRUD APIs under `/api/v1/`
- Assignment, priority, category, tags, comments
- SLA and resolution tracking
- UUID public IDs, `workspace_id` on all tenant tables
- Cursor-based pagination on list endpoints

## Phase 3 — Support Desk MVP

- Agent workspace UI (Georgian-first via next-intl)
- Case list, detail, and assignment views
- Customer timeline view
- Internal comments and customer replies
- Basic filtering and search
- Playwright E2E tests for critical flows

## Phase 4 — CX Analytics Studio v1

- Case volume and resolution metrics
- Agent performance summaries
- Channel breakdown (from case origin metadata)
- SLA compliance reporting
- Export capabilities

## Phase 5 — Mock Channel Imports

- CSV and manual import adapters
- Simulated email, social, and review ingestion
- Channel metadata on cases without real API integrations
- Import validation and error reporting

## Phase 6 — Real Integrations

- Live email (SMTP/IMAP or provider API)
- Social platform connectors (Facebook, Instagram, etc.)
- WhatsApp Business API
- Review platform polling
- Webhook ingestion endpoints
- Rate limiting and retry policies per channel

## Explicitly deferred across all pre-Phase-6 work

- AI features
- Billing and subscriptions
- Production deployment
- Real third-party OAuth integrations (until Phase 6)

## Related docs

- [Vision](vision.md)
- [Development rules](../development/development-rules.md)
- [Decision: local-first stack](../decisions/0001-local-first-stack.md)
