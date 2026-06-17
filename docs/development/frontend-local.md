# Frontend Local Development

Guide for running the Next.js frontend skeleton locally (Phase 0 / Step 4).

## Scope

This frontend is a **minimal skeleton**:

- Next.js App Router + TypeScript
- `next-intl` for Georgian (`ka`) and English (`en`)
- Static Phase 0 landing page
- No backend API calls, auth, or business UI

The frontend runs **without Docker** and does not require PostgreSQL, Redis, MinIO, or Mailpit.

## Folder structure

```text
apps/frontend/
├── app/
│   ├── [locale]/           # Locale-prefixed routes (/ka, /en)
│   ├── globals.css
│   ├── layout.tsx          # Root passthrough layout
│   └── not-found.tsx
├── messages/
│   ├── ka.json             # Georgian strings
│   └── en.json             # English strings
├── src/
│   ├── i18n/
│   │   ├── routing.ts      # Locale config (ka default, en secondary)
│   │   ├── request.ts      # next-intl request config
│   │   └── navigation.ts   # Localized Link helpers
│   └── components/
│       └── locale-switcher.tsx
├── tests/
│   └── i18n.test.ts        # Message key consistency
├── middleware.ts           # Locale routing middleware
├── next.config.ts
└── package.json
```

## Prerequisites

- Node.js 20+ (LTS recommended)
- npm

## Setup

```bash
cd apps/frontend
npm install
```

No `.env.local` is required for this step.

## Development

```bash
npm run dev        # port 3000
npm run dev:3001   # port 3001
```

Use `--hostname localhost` (configured in `package.json`). Do **not** use `next dev --hostname 127.0.0.1` with `next-intl` on Next.js 15 — middleware locale rewrites are incorrectly proxied to `http://localhost:PORT/...` and return HTTP 500.

| URL | Content |
|-----|---------|
| [http://127.0.0.1:3000/ka](http://127.0.0.1:3000/ka) | Georgian landing page |
| [http://127.0.0.1:3000/en](http://127.0.0.1:3000/en) | English landing page |
| [http://127.0.0.1:3001/ka](http://127.0.0.1:3001/ka) | Georgian (when using `dev:3001`) |

Visiting `/` redirects to `/ka` (default locale).

## Build and quality checks

```bash
npm run typecheck
npm run lint
npm run build
npm run test:i18n
```

## i18n structure

| File | Purpose |
|------|---------|
| `src/i18n/routing.ts` | `locales: ["ka", "en"]`, `defaultLocale: "ka"` |
| `src/i18n/request.ts` | Loads messages from `messages/{locale}.json` |
| `messages/ka.json` | Georgian UI strings |
| `messages/en.json` | English UI strings |

Visible landing page text must come from message files — not hardcoded in components.

The locale switcher links between `/ka` and `/en` without persisting user preference yet.

## What is intentionally not implemented

- Login, registration, dashboard, cases, customers
- Backend health check integration
- API client, React Query, SWR
- Auth tokens, cookies, localStorage
- Server actions that mutate data
- Component libraries (Tailwind, shadcn, MUI)
- Playwright E2E tests
- Frontend Docker container

## Related docs

- [Frontend README](../../apps/frontend/README.md)
- [Backend local development](backend-local.md)
- [Development rules](development-rules.md)
