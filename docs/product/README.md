# Product

## Vision

Georgian CX Platform is a **Georgian-first unified customer experience platform** for businesses that need one workspace for customer support, messages, social complaints, reviews, phone-call logs, and analytics.

It is a focused CX operating system — not a generic helpdesk clone. The product should feel locally useful for Georgian businesses from day one.

## Core concept: Universal Case

Every external customer interaction should eventually become either:

1. A **Universal Case** — a trackable, assignable, resolvable unit of work representing a customer need; or
2. A **Customer Event** — an entry on a customer timeline attached to an existing customer profile.

This unifies channels (email, chat, social, phone, reviews) under one mental model instead of siloed inboxes.

```text
External interaction
        │
        ▼
  ┌─────────────┐
  │  Ingestion  │  (future: webhooks, polling, manual import)
  └──────┬──────┘
         │
    ┌────┴────┐
    ▼         ▼
Universal   Customer
  Case       Event
(trackable) (timeline)
```

## Target users (Phase 0)

- IT support teams
- Hosting and domain companies
- Google Workspace resellers
- SaaS support desks
- SMBs managing support through Gmail, Facebook, Instagram, WhatsApp, phone calls, and spreadsheets

## What we are not building (yet)

- Full Zendesk feature parity
- AI-powered automation
- Billing and subscriptions
- Social media or call-center integrations (planned for later phases)
- Third-party CRM replacements

## Locales

| Locale | Language | Role |
|--------|----------|------|
| `ka` | Georgian | Default UI and content language |
| `en` | English | Secondary language for mixed teams and documentation |

## Related docs

- [Architecture overview](../architecture/README.md)
- [Glossary](glossary.md)
