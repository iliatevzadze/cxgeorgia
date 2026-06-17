# Glossary

Terms used across the Georgian CX Platform documentation and codebase.

## Universal Case

A first-class, trackable unit of customer work. A case has a lifecycle (open → in progress → resolved → closed), can be assigned to agents, and aggregates related messages and events from any channel.

## Customer Event

A timestamped entry on a customer's timeline. Events may be informational (e.g. a phone call log) or linked to a Universal Case.

## Customer timeline

A chronological view of all interactions and events for a single customer, regardless of channel.

## Workspace

A tenant boundary — one business organization using the platform. Phase 1 / Step 2 defines the `workspaces` table (name, slug, status). No API or settings UI exists yet.

## Workspace membership

Links a `user` to a `workspace` with a role (`owner`, `admin`, `member`). Stored in `workspace_memberships`. No invitation or permission enforcement exists yet.

## Channel

A source of customer interaction: email, web chat, Facebook, Instagram, WhatsApp, phone, review platform, etc. Channel integrations are not implemented in Phase 0.

## Agent

A workspace member who handles Universal Cases and communicates with customers.

## CX

Customer Experience — the end-to-end perception a customer has when interacting with a business. This platform is the internal operating system for managing that experience.
