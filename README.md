# Georgian CX Platform

A Georgian-first, local-first unified customer experience platform for businesses that manage customer support, messages, social complaints, reviews, phone-call logs, and analytics in one workspace.

## Product philosophy

Georgian CX Platform is a **focused CX operating system** — not a Zendesk clone. The core concept is the **Universal Case**: every external customer interaction should eventually become either a trackable Universal Case or a Customer Event on a customer timeline.

The product is **human-agent-first** and **Georgian-first** (`ka` default, `en` secondary). It is built for local businesses that today juggle Gmail, Facebook, Instagram, WhatsApp, phone calls, and spreadsheets.

## Current phase

**Phase 1 — SaaS Base** (Step 52: Case Attachments frontend UI)

Users can view, upload, and delete attachments from the case detail page.

Phase 1 / Step 53 has **not started**.

## Confirmed stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js App Router, React, TypeScript |
| i18n | next-intl (default `ka`, secondary `en`) |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy async + asyncpg |
| Migrations | Alembic |
| Worker | Celery + Redis |
| Cache / queue | Redis |
| File storage | MinIO |
| Email (local) | Mailpit |
| Orchestration | Docker Compose (Step 2) |
| API | REST, versioned at `/api/v1/` |
| Auth (Phase 1) | JWT access token + HttpOnly refresh token |
| IDs | UUIDs only — no sequential public IDs |
| Testing | pytest, httpx (Phase 1+), Playwright (Phase 3+) |

## Planned local-first services

| Service | Role |
|---------|------|
| PostgreSQL | Primary data store |
| Redis | Celery broker, cache, pub/sub (later) |
| MinIO | S3-compatible file storage |
| Mailpit | Local email simulation |

Docker Compose runs the full Phase 0 stack (infrastructure + apps). See [local Docker workflow](docs/development/local-docker.md) and `.env.example`.

### Backend database (Phase 1)

Core SaaS tables: `users`, `workspaces`, `workspace_memberships`. No auth or API yet.

```bash
cd ~/cxgeorgia
docker compose up -d postgres

cd apps/backend
source .venv/bin/activate
alembic upgrade head
python scripts/check_db_connection.py
pytest
```

See [backend local development](docs/development/backend-local.md).

### Full stack via Docker Compose (Phase 0 / Step 6)

```bash
cp .env.example .env
docker compose config
docker compose up -d --build
docker compose ps
```

| URL | Service |
|-----|---------|
| [http://localhost:8000/health](http://localhost:8000/health) | Backend health |
| [http://localhost:8000/docs](http://localhost:8000/docs) | Backend Swagger |
| [http://localhost:3001/ka](http://localhost:3001/ka) | Frontend (Georgian) |
| [http://localhost:3001/en](http://localhost:3001/en) | Frontend (English) |
| [http://localhost:9001](http://localhost:9001) | MinIO console |
| [http://localhost:8025](http://localhost:8025) | Mailpit |

Stop safely: `docker compose down` (do **not** use `-v` unless wiping data).

App containers (`cx_backend`, `cx_frontend`, `cx_worker`) run as non-root users. The Celery worker no longer logs the root-user `SecurityWarning`.

### Local infrastructure (Phase 0 / Step 2)

| Service | Container | Local access |
|---------|-----------|--------------|
| PostgreSQL | `cx_postgres` | `localhost:15432` (host) → container `5432` |
| Redis | `cx_redis` | `localhost:16379` (host) → container `6379` |
| MinIO API | `cx_minio` | `localhost:9000` |
| MinIO Console | `cx_minio` | [http://localhost:9001](http://localhost:9001) |
| Mailpit SMTP | `cx_mailpit` | `localhost:1025` |
| Mailpit Web UI | `cx_mailpit` | [http://localhost:8025](http://localhost:8025) |

PostgreSQL: connect from the **host** at `localhost:15432` (`POSTGRES_HOST_PORT`). Future app containers on `cx_platform_network` use `postgres:5432` (`POSTGRES_PORT`).

Redis: connect from the **host** at `localhost:16379` (`REDIS_HOST_PORT`). Future app containers use `redis:6379` (`REDIS_PORT`).

**Validate and start manually** (from repository root):

```bash
cp .env.example .env
docker compose config
docker compose up -d
docker compose ps
```

**Stop safely** (preserves data volumes):

```bash
docker compose stop
docker compose down
```

Do **not** use `docker compose down -v` unless you want to wipe local data.

### Backend skeleton (Phase 0 / Step 3)

Minimal FastAPI app in `apps/backend` — health check only, no database or auth.

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

pytest
ruff check .
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

| URL | Purpose |
|-----|---------|
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Health check |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI |

See [backend local development](docs/development/backend-local.md).

### Frontend skeleton (Phase 0 / Step 4)

Next.js App Router with `next-intl` — Phase 0 landing page only, no API or auth.

```bash
cd apps/frontend
npm install
npm run typecheck
npm run lint
npm run build
npm run dev:3001   # use dev:3001 if port 3000 is busy
```

Dev server binds to `localhost` (required for `next-intl` middleware on Next.js 15). Both `127.0.0.1` and `localhost` work in the browser.

| URL | Locale |
|-----|--------|
| [http://127.0.0.1:3000/ka](http://127.0.0.1:3000/ka) | Georgian (default) |
| [http://127.0.0.1:3000/en](http://127.0.0.1:3000/en) | English |
| [http://127.0.0.1:3001/ka](http://127.0.0.1:3001/ka) | Georgian (`dev:3001`) |

See [frontend local development](docs/development/frontend-local.md).

### Worker skeleton (Phase 0 / Step 5)

Celery worker with Redis config and safe `debug.ping` task only — no real jobs or scheduler.

```bash
cd apps/worker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

pytest
ruff check .
```

Redis: host `localhost:16379` (future Docker worker: `redis:6379`). See [worker local development](docs/development/worker-local.md).

```bash
celery -A worker.celery_app:celery_app worker --loglevel=INFO
```

## Folder structure

```text
.
├── apps/
│   ├── frontend/       # Next.js App Router UI
│   ├── backend/        # FastAPI REST API (/api/v1/)
│   └── worker/         # Celery background jobs
├── packages/
│   └── shared/         # Shared types and API contracts
├── infra/
│   ├── docker/         # Docker Compose (Step 2)
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   └── mailpit/
├── docs/
│   ├── product/        # Vision, Universal Case, roadmap
│   ├── architecture/   # Overview, tech stack
│   ├── security/       # Baseline, RBAC
│   ├── development/    # Rules, Cursor workflow
│   └── decisions/      # ADRs
├── scripts/            # Dev helper scripts (future)
├── tests/
│   └── e2e/            # Playwright E2E (later phases)
└── .github/workflows/  # CI/CD (future)
```

## Development workflow

1. Read the [Cursor workflow](docs/development/cursor-workflow.md) — one approved step at a time.
2. Copy `.env.example` to `.env` locally when Docker Compose is added (Step 2). **Never commit `.env`.**
3. Follow [development rules](docs/development/development-rules.md) — no scope creep across phases.
4. Record significant decisions as ADRs in `docs/decisions/`.

## Testing strategy by phase

| Phase | Tests |
|-------|-------|
| Phase 0 | Backend, worker pytest; frontend typecheck/lint/build; i18n key test |
| Phase 1 | pytest + httpx: auth, workspace, **tenant isolation**, **RBAC** |
| Phase 2 | API tests: Universal Case CRUD, pagination, workspace scoping |
| Phase 3 | Playwright E2E: agent case workflows |
| Phase 4+ | Analytics, imports, integration tests per phase scope |

Security-critical tests (tenant isolation, RBAC) are **mandatory from Phase 1 onward**. No phase is complete if its required tests fail.

## Documentation

| Doc | Path |
|-----|------|
| Vision | [docs/product/vision.md](docs/product/vision.md) |
| Universal Case | [docs/product/universal-case.md](docs/product/universal-case.md) |
| Roadmap | [docs/product/roadmap.md](docs/product/roadmap.md) |
| Architecture | [docs/architecture/overview.md](docs/architecture/overview.md) |
| Tech stack | [docs/architecture/tech-stack.md](docs/architecture/tech-stack.md) |
| Security baseline | [docs/security/security-baseline.md](docs/security/security-baseline.md) |
| RBAC | [docs/security/rbac.md](docs/security/rbac.md) |
| Development rules | [docs/development/development-rules.md](docs/development/development-rules.md) |
| Cursor workflow | [docs/development/cursor-workflow.md](docs/development/cursor-workflow.md) |
| Local Docker | [docs/development/local-docker.md](docs/development/local-docker.md) |
| Backend local | [docs/development/backend-local.md](docs/development/backend-local.md) |
| Frontend local | [docs/development/frontend-local.md](docs/development/frontend-local.md) |
| Worker local | [docs/development/worker-local.md](docs/development/worker-local.md) |
| ADR: local-first stack | [docs/decisions/0001-local-first-stack.md](docs/decisions/0001-local-first-stack.md) |

## What is intentionally not built yet

- Application Docker containers in Compose (backend, frontend, worker)
- Frontend–backend API integration
- Database schema, SQLAlchemy models, Alembic migrations
- PostgreSQL / Redis / MinIO connectivity in backend code
- Authentication, JWT, registration, login
- RBAC enforcement code
- Universal Case tables and APIs
- Auth, dashboard, cases, and workspace UI
- Real email, social, review, or messaging integrations
- AI features, billing, analytics dashboards
- Production deployment and CI/CD

## Phase 0 definition of done

- [x] Monorepo folder structure exists
- [x] All required documentation files with exact filenames
- [x] `.env.example`, `.gitignore`, `.editorconfig` at repository root
- [x] Placeholder app files contain no business logic
- [x] No secrets committed; `.env.example` has placeholders only
- [x] Docker Compose local services (`postgres`, `redis`, `minio`, `mailpit`)
- [x] FastAPI backend skeleton with `GET /health` and pytest tests
- [x] Next.js frontend skeleton with `next-intl` (`ka` / `en`)
- [x] Celery worker skeleton with `debug.ping` and pytest tests
- [x] Docker Compose app containers (backend, frontend, worker)
- [x] App containers run as non-root users; Celery root-user warning fixed; Next.js telemetry disabled in Docker frontend
- [x] Backend SQLAlchemy async + Alembic baseline migration (Phase 1 / Step 1)
- [x] Core SaaS models: users, workspaces, workspace_memberships (Phase 1 / Step 2)
- [x] Auth utilities: password hashing + JWT access tokens (Phase 1 / Step 3)
- [x] Backend auth API: register, login, /me (Phase 1 / Step 4)
- [x] Workspace bootstrap API (Phase 1 / Step 5)
- [x] Frontend auth foundation (Phase 1 / Step 6)
- [x] Frontend workspace foundation (Phase 1 / Step 7)
- [x] Workspace app shell foundation (Phase 1 / Step 8)
- [x] Workspace app route skeleton (Phase 1 / Step 9)
- [x] Universal Case database foundation (Phase 1 / Step 10)
- [x] Universal Case backend API foundation (Phase 1 / Step 11)
- [x] Universal Case frontend read-only list (Phase 1 / Step 12)
- [x] Universal Case create form UI (Phase 1 / Step 13)
- [x] Universal Case detail page UI (Phase 1 / Step 14)
- [x] Universal Case status/priority PATCH API (Phase 1 / Step 15)
- [x] Universal Case status/priority update frontend UI (Phase 1 / Step 16)
- [x] Universal Case title/description PATCH API (Phase 1 / Step 17)
- [x] Universal Case title/description update frontend UI (Phase 1 / Step 18)
- [x] Universal Case customer/source PATCH API (Phase 1 / Step 19)
- [x] Universal Case customer/source update frontend UI (Phase 1 / Step 20)
- [x] Universal Case DELETE backend API (Phase 1 / Step 21)
- [x] Universal Case delete frontend UI (Phase 1 / Step 22)
- [x] Universal Case assignment backend API (Phase 1 / Step 23)
- [x] Universal Case assignment frontend UI (Phase 1 / Step 24)
- [x] Universal Case comments database foundation (Phase 1 / Step 25)
- [x] Universal Case comments backend API (Phase 1 / Step 26)
- [x] Universal Case comments frontend UI (Phase 1 / Step 27)
- [x] Universal Case comment delete backend API (Phase 1 / Step 28)
- [x] Universal Case comment delete frontend UI (Phase 1 / Step 29)
- [x] Universal Case activity timeline database foundation (Phase 1 / Step 30)
- [x] Universal Case activity timeline backend API (Phase 1 / Step 31)
- [x] Automatic Universal Case activity recording (Phase 1 / Step 32)
- [x] Universal Case activity timeline frontend UI (Phase 1 / Step 33)
- [x] Universal Case comment edit backend API (Phase 1 / Step 34)
- [x] Universal Case comment edit frontend UI (Phase 1 / Step 35)
- [x] Universal Case tags database foundation (Phase 1 / Step 36)
- [x] Universal Case tags backend API (Phase 1 / Step 37)
- [x] Universal Case tags frontend UI (Phase 1 / Step 38)
- [x] Universal Case tag activity recording (Phase 1 / Step 39)
- [x] Universal Case attachments database foundation (Phase 1 / Step 40)
- [x] Universal Case attachments backend metadata API (Phase 1 / Step 41)
- [x] Universal Case attachments file storage layer (Phase 1 / Step 42)
- [x] Universal Case SLA foundation (Phase 1 / Step 43)
- [x] Agent Workforce Tracking foundation (Phase 1 / Step 44)
- [x] QA / Ticket Evaluation system (Phase 1 / Step 45)
- [x] Operations Dashboard backend API (Phase 1 / Step 46)
- [x] Operations Dashboard frontend UI (Phase 1 / Step 47)
- [x] QA Review backend API (Phase 1 / Step 48)
- [x] QA Review frontend UI (Phase 1 / Step 49)
- [x] Agent Workforce backend API (Phase 1 / Step 50)
- [x] Agent Workforce frontend UI (Phase 1 / Step 51)
- [x] Case Attachments frontend UI (Phase 1 / Step 52)
- [ ] Phase 1 / Step 53 (not started)

## License

To be determined.
