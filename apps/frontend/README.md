# Frontend

Next.js App Router application for the Georgian CX Platform workspace UI.

## Current phase

**Phase 1 — SaaS Base** (Step 65: Case list frontend pagination compatibility)

The Cases list page consumes paginated case list responses (`items`, `total`, `limit`, `offset`) with total count and Previous/Next controls.

Phase 1 / Step 66 has **not started**.

## What exists now

- Next.js App Router with TypeScript
- `next-intl` with Georgian (`ka`) default and English (`en`)
- Locale routes: `/ka`, `/en`
- API client with backend response envelope support
- Same-origin `/api/v1` proxy via Next.js rewrites
- Auth pages: login, register, account (`/me`)
- Workspace pages: list, create, detail, memberships
- Workspace app shell: `/workspaces/{id}/app` with internal navigation
- Workspace app Cases page with create form, list and detail (`/workspaces/{id}/app/cases`)
- Case create form and case detail support optional customer record linking
- Case list and case detail show read-only SLA status and timestamps
- Workspace app Operations dashboard (`/workspaces/{id}/app/dashboard`) with case, SLA, agent and QA summaries
- Agent Workforce panel on the dashboard: clock in/out, active shifts and case metrics
- Workspace app Customers page with list, search, create, update, delete and linked case history
- Case detail update, assignment, comments (list/create/edit/delete), tags, attachments, activity timeline, QA reviews and case delete controls
- Workspace app placeholder routes: settings
- `useWorkspace` hook for loading workspace context with safe error states
- JWT access token stored in `localStorage`
- `AuthProvider`, `useAuth`, `useWorkspaces`, and `useWorkspace` hooks
- Protected workspace routes via `RequireAuth`
- i18n key consistency and unit tests
- Docker container runs as non-root `node`; Next.js telemetry disabled in Docker (`NEXT_TELEMETRY_DISABLED=1`)

## What does not exist yet

- Activity create/edit/delete UI
- Product settings
- Workspace switcher or invitation UI
- Advanced RBAC UI
- React Query, SWR, or component libraries
- Tailwind, shadcn/ui, Material UI
- HttpOnly refresh token handling
- Playwright E2E tests

## Auth routes

| Path | Description |
|------|-------------|
| `/ka/login`, `/en/login` | Sign in |
| `/ka/register`, `/en/register` | Create account |
| `/ka/account`, `/en/account` | Current user profile (`GET /api/v1/auth/me`) |

## Workspace routes

All workspace routes require login.

| Path | Description |
|------|-------------|
| `/ka/workspaces`, `/en/workspaces` | List workspaces (`GET /api/v1/workspaces`) |
| `/ka/workspaces/new`, `/en/workspaces/new` | Create workspace (`POST /api/v1/workspaces`) |
| `/ka/workspaces/{id}`, `/en/workspaces/{id}` | Workspace detail (`GET /api/v1/workspaces/{id}`) |
| `/ka/workspaces/{id}/memberships`, `/en/workspaces/{id}/memberships` | Memberships (`GET /api/v1/workspaces/{id}/memberships`) |
| `/ka/workspaces/{id}/app`, `/en/workspaces/{id}/app` | Workspace app home (foundation) |
| `/ka/workspaces/{id}/app/cases`, `/en/workspaces/{id}/app/cases` | Universal Cases create + list |
| `/ka/workspaces/{id}/app/cases/{caseId}`, `/en/...` | Universal Case detail with update, assignment, comments, tags, activity timeline and delete |
| `/ka/workspaces/{id}/app/dashboard`, `/en/...` | Operations dashboard and Agent Workforce panel |
| `/ka/workspaces/{id}/app/customers`, `/en/...` | Customer records list and management |

## API integration

Browser requests use same-origin paths such as `/api/v1/auth/login`. Next.js rewrites them to the backend (`BACKEND_URL`, default `http://localhost:8000`).

Optional override: set `NEXT_PUBLIC_API_URL` to call the backend directly (requires backend CORS for browser use).

## Folder structure

```text
apps/frontend/
├── app/
│   ├── [locale]/
│   │   ├── account/page.tsx
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── workspaces/
│   │   │   ├── page.tsx
│   │   │   ├── new/page.tsx
│   │   │   └── [workspaceId]/
│   │   │       ├── page.tsx
│   │   │       ├── memberships/page.tsx
│   │   │       └── app/cases/page.tsx
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── globals.css
│   ├── layout.tsx
│   └── not-found.tsx
├── messages/
│   ├── ka.json
│   └── en.json
├── src/
│   ├── components/
│   │   ├── workspace-cases-list.tsx
│   │   └── ...
│   ├── hooks/
│   ├── i18n/
│   └── lib/
│       ├── api/
│       ├── auth/
│       ├── cases/
│       │   ├── api.ts
│       │   └── types.ts
│       ├── operations/
│       │   ├── api.ts
│       │   └── types.ts
│       ├── agent-workforce/
│       │   ├── api.ts
│       │   └── types.ts
│       ├── customers/
│       │   ├── api.ts
│       │   └── types.ts
│       └── workspaces/
├── tests/
│   ├── cases-api-config.test.ts
│   ├── cases-types.test.ts
│   └── ...
├── middleware.ts
├── next.config.ts
├── package.json
└── tsconfig.json
```

## Install dependencies

```bash
cd apps/frontend
npm install
```

## Run dev server

Requires the backend running at `http://localhost:8000` (or Docker Compose stack).

```bash
npm run dev        # default port 3000
npm run dev:3001   # port 3001 if 3000 is busy
```

**Important:** Dev scripts use `--hostname localhost` (not `127.0.0.1`). With Next.js 15 + `next-intl` middleware, binding to `127.0.0.1` causes middleware rewrites to be proxied to `http://localhost:PORT/...` and return **500 Internal Server Error**. Using `localhost` keeps rewrites internal.

| URL | Locale |
|-----|--------|
| [http://127.0.0.1:3000/ka](http://127.0.0.1:3000/ka) | Georgian (default) |
| [http://127.0.0.1:3000/en](http://127.0.0.1:3000/en) | English |

Both `127.0.0.1` and `localhost` work in the browser when the dev server binds to `localhost`.

Root `/` redirects to `/ka` via middleware.

## Docker (local development)

From repository root:

```bash
docker compose up -d --build frontend backend postgres
```

| URL | Locale |
|-----|--------|
| [http://localhost:3001/ka](http://localhost:3001/ka) | Georgian |
| [http://localhost:3001/en](http://localhost:3001/en) | English |

Container internal port: `3000`. Host port: `3001` (`FRONTEND_PORT` in `.env`).

Dockerfile: `apps/frontend/Dockerfile` (runs as non-root `node`, telemetry disabled)

## Other commands

```bash
npm run typecheck
npm run lint
npm run build
npm run test
```

## Locales

| Locale | Role |
|--------|------|
| `ka` | Default — Georgian |
| `en` | Secondary — English |

All visible UI strings come from `messages/ka.json` and `messages/en.json`.

## Related docs

- [Frontend local development](../../docs/development/frontend-local.md)
- [Backend local development](../../docs/development/backend-local.md)
