# Frontend

Next.js App Router application for the Georgian CX Platform workspace UI.

## Current phase

**Phase 0 — Project Foundation** (Step 4: frontend skeleton + i18n)

Phase 1 has **not started**. No auth, dashboard, API integration, or business logic exists yet.

## What exists now

- Next.js App Router with TypeScript
- `next-intl` with Georgian (`ka`) default and English (`en`)
- Locale routes: `/ka`, `/en`
- Phase 0 landing page (static, translation-driven)
- Locale switcher
- i18n key consistency test
- Docker container runs as non-root `node`; Next.js telemetry disabled in Docker (`NEXT_TELEMETRY_DISABLED=1`)

## What does not exist yet

- Authentication / login / registration UI
- Dashboard, cases, customers, settings
- Backend API integration (`GET /health` not called from frontend)
- React Query, SWR, state management, component libraries
- Tailwind, shadcn/ui, Material UI

## Folder structure

```text
apps/frontend/
├── app/
│   ├── [locale]/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── globals.css
│   ├── layout.tsx
│   └── not-found.tsx
├── messages/
│   ├── ka.json
│   └── en.json
├── src/
│   ├── i18n/
│   │   ├── routing.ts
│   │   ├── request.ts
│   │   └── navigation.ts
│   └── components/
│       └── locale-switcher.tsx
├── tests/
│   └── i18n.test.ts
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
docker compose up -d --build frontend
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
npm run test:i18n
```

## Locales

| Locale | Role |
|--------|------|
| `ka` | Default — Georgian |
| `en` | Secondary — English |

All visible landing page strings come from `messages/ka.json` and `messages/en.json`.

## Related docs

- [Frontend local development](../../docs/development/frontend-local.md)
