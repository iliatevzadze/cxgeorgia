# Frontend Local Development

Guide for running the Next.js frontend locally (Phase 1 / Step 27).

## Scope

This frontend includes:

- Next.js App Router + TypeScript
- `next-intl` for Georgian (`ka`) and English (`en`)
- Auth foundation: login, register, account pages
- Workspace foundation: list, create, detail, memberships pages
- Workspace app shell at `/workspaces/{id}/app`
- Universal Cases create form, list and detail at `/workspaces/{id}/app/cases`
- Case detail update, assignment, comments and delete controls (PATCH / DELETE / comment API)
- Workspace app placeholder routes: dashboard, customers, settings
- API client with same-origin `/api/v1` proxy to the backend
- JWT access token in `localStorage`

It does **not** include functional dashboard, customer CRUD module, settings forms, billing, integrations, invitations, or advanced RBAC.

## Prerequisites

- Node.js 20+ (LTS recommended)
- npm
- Backend running at `http://localhost:8000` with PostgreSQL migrated

## Setup

```bash
cd apps/frontend
npm install
```

From repository root, ensure `.env` exists (copy from `.env.example`). The frontend uses:

| Variable | Purpose |
|----------|---------|
| `BACKEND_URL` | Next.js rewrite target (default `http://localhost:8000`) |
| `NEXT_PUBLIC_API_URL` | Optional direct backend URL; leave empty for same-origin proxy |

No `apps/frontend/.env.local` is required when using root `.env` with Docker Compose. For local `npm run dev`, defaults in `next.config.ts` point to `http://localhost:8000`.

## Development

Start infrastructure and backend first:

```bash
cd ~/cxgeorgia
docker compose up -d postgres
cd apps/backend && source .venv/bin/activate && alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Then start the frontend:

```bash
cd apps/frontend
npm run dev        # port 3000
npm run dev:3001   # port 3001
```

Use `--hostname localhost` (configured in `package.json`). Do **not** use `next dev --hostname 127.0.0.1` with `next-intl` on Next.js 15 — middleware locale rewrites are incorrectly proxied to `http://localhost:PORT/...` and return HTTP 500.

| URL | Content |
|-----|---------|
| [http://127.0.0.1:3000/ka](http://127.0.0.1:3000/ka) | Georgian home |
| [http://127.0.0.1:3000/ka/login](http://127.0.0.1:3000/ka/login) | Login |
| [http://127.0.0.1:3000/ka/account](http://127.0.0.1:3000/ka/account) | Account (requires login) |
| [http://127.0.0.1:3000/ka/workspaces](http://127.0.0.1:3000/ka/workspaces) | Workspace list (requires login) |
| [http://127.0.0.1:3000/ka/workspaces/new](http://127.0.0.1:3000/ka/workspaces/new) | Create workspace |
| `http://127.0.0.1:3000/ka/workspaces/{id}/app` | Workspace app shell (after login) |
| `http://127.0.0.1:3000/ka/workspaces/{id}/app/cases` | Cases create form + list |
| `http://127.0.0.1:3000/ka/workspaces/{id}/app/cases/{caseId}` | Case detail with update and delete |

Visiting `/` redirects to `/ka` (default locale).

## Manual workspace flow

1. Start backend and frontend (or `docker compose up -d backend postgres frontend`).
2. Register or log in at `/ka/register` or `/ka/login`.
3. Open `/ka/workspaces`.
4. If empty, open `/ka/workspaces/new` and create a workspace.
5. Confirm the workspace appears in the list.
6. Open workspace detail and click **Open app**.
7. Confirm `/ka/workspaces/{id}/app` shows the workspace app shell.
8. Click **Cases** in the sidebar — create a case from the form and confirm it appears in the list.
9. Click a case title to open the detail page; change source, customer metadata, title, description, status or priority and save; confirm success and updated values.
10. Assign the case to an active workspace member and save assignment; confirm the detail view updates; refresh and confirm persistence.
11. Unassign the case; confirm assignment clears in the detail view.
12. Add an internal comment on the case detail page; confirm it appears in the comments list; refresh and confirm persistence.
13. Add a public (non-internal) comment if the UI exposes the internal checkbox; confirm visibility label.
14. Clear description or customer metadata fields and save; confirm they clear safely.
15. Delete a case from the detail page; cancel confirmation first, then confirm and verify redirect to cases list.
16. Confirm deleted case no longer appears in the list.
17. Use **Back to cases** to return when not deleting.
18. Confirm `/en/workspaces/{id}/app/cases` and detail routes work with English UI.
19. Confirm submit is disabled when there are no changes.
20. Confirm an invalid case id shows a safe not-found state.

## Build and quality checks

```bash
npm run typecheck
npm run lint
npm run build
npm run test
```

## API proxy

Client code calls relative paths such as `/api/v1/workspaces`. `next.config.ts` rewrites them to `BACKEND_URL/api/v1/...`, so the browser stays same-origin and CORS is not required for the default setup.

## What is intentionally not implemented

- Comment edit/delete
- Timeline, SLA, attachments, tags, customer module
- Product dashboard, customers, billing, integrations
- Workspace switcher, invitation flow and advanced RBAC UI
- HttpOnly refresh tokens
- React Query, SWR, Tailwind, shadcn, MUI
- Playwright E2E tests

## Related docs

- [Frontend README](../../apps/frontend/README.md)
- [Backend local development](backend-local.md)
- [Development rules](development-rules.md)
