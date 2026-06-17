# Universal Case

## Definition

A **Universal Case** is the primary trackable unit of customer work in the Georgian CX Platform. It represents a customer need that requires attention, assignment, and resolution — regardless of which channel it arrived from.

Every external customer interaction should eventually become either:

1. A **Universal Case** — assignable, prioritizable, resolvable work; or
2. A **Customer Event** — an informational entry on a customer timeline (see below).

```text
External interaction
        │
        ▼
     Ingestion
        │
   ┌────┴────┐
   ▼         ▼
Universal   Customer
  Case       Event
```

## Customer Event definition

A **Customer Event** is a timestamped entry on a customer's timeline. Events record interactions that do not require case-level tracking — for example, an informational phone call log, a passive review observation, or a system-generated note.

Events may optionally link to an existing Universal Case when context is relevant.

## Case origin sources (planned)

All future channels must map into the Universal Case or Customer Event model. Planned origin sources include:

| Source | Example |
|--------|---------|
| Email | Support inbox message |
| Web form | Contact form submission |
| Phone | Call log or voicemail note |
| Facebook | Page message or comment |
| Instagram | DM or comment |
| WhatsApp | Business message |
| Review platform | Google or Facebook review |
| Manual | Agent-created case |
| Import | CSV or mock channel import |

No channel-specific silo tables. Channel metadata attaches to the case; the case is the unit of work.

## Case attributes (planned)

| Attribute | Purpose |
|-----------|---------|
| **Assignment** | Which agent or team owns the case |
| **Priority** | Urgency relative to other open cases |
| **Category** | Type of issue (billing, technical, account, etc.) |
| **Tags** | Flexible labels for filtering and reporting |
| **Comments** | Internal agent notes and customer-facing replies |
| **SLA** | Response and resolution time targets |
| **Resolution** | Outcome, resolution type, and closed timestamp |
| **Status** | Lifecycle state (open, in progress, waiting, resolved, closed) |

## Why all channels must map into this model

1. **One inbox mental model** — Agents work cases, not channels.
2. **Shared customer context** — History follows the customer, not the tool.
3. **Consistent reporting** — Metrics aggregate across channels without custom joins.
4. **Simpler permissions** — RBAC applies to cases and workspaces, not per-channel apps.
5. **Future integrations** — New channels are adapters, not new product surfaces.

Building channel-specific ticket systems (email tickets, social tickets, phone tickets) creates the fragmentation this platform exists to eliminate.

## Status

No Universal Case tables, APIs, or UI exist yet. Implementation is planned for Phase 2.

## Related docs

- [Vision](vision.md)
- [Roadmap](roadmap.md)
- [Glossary](glossary.md)
