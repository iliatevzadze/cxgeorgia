# Monorepo layout

Directory structure and responsibilities.

```text
.
├── apps/
│   ├── frontend/          # Next.js UI
│   ├── backend/           # FastAPI API
│   └── worker/            # Celery worker
├── packages/
│   └── shared/            # Shared types and contracts
├── infra/
│   ├── docker/            # Docker Compose (future)
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   └── mailpit/
├── docs/
│   ├── architecture/
│   ├── security/
│   ├── product/
│   ├── development/
│   └── decisions/
├── scripts/               # Dev/ops helper scripts
├── tests/
│   └── e2e/               # Cross-app E2E tests
└── .github/
    └── workflows/         # CI/CD (future)
```

## Conventions

### Apps are deployable units

Each directory under `apps/` is an independently deployable service with its own dependencies and README.

### Packages are libraries

`packages/` contains code consumed by apps but not deployed on its own.

### Infra is configuration, not application code

Service configs and init scripts live under `infra/`. Application code must not import from `infra/`.

### Docs are the source of truth for design intent

When implementation choices are made, record them as ADRs in `docs/decisions/`.

### Tests

- Unit and integration tests live inside each app (`apps/*/tests/`).
- Cross-app E2E tests live in `tests/e2e/`.

## Dependency direction

```text
packages/shared  ──►  apps/frontend
                   ──►  apps/backend
                   ──►  apps/worker

apps/frontend    ──►  apps/backend  (HTTP only, no direct imports)
apps/worker      ──►  apps/backend  (shared DB, no direct imports)
```

Apps must not import from each other directly.
