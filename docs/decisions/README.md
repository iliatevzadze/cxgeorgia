# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) — short documents that capture significant technical decisions, their context, and consequences.

## Format

Each ADR follows this template:

```markdown
# ADR-NNN: Title

## Status

Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## Context

What is the issue or question?

## Decision

What was decided?

## Consequences

What are the positive and negative outcomes?
```

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-monorepo-and-stack.md) | Monorepo layout and confirmed stack | Accepted |

## Creating a new ADR

1. Copy the template from `template.md`
2. Number sequentially (ADR-002, ADR-003, …)
3. Set status to `Proposed` and open for review
4. Update status to `Accepted` when agreed
5. Add a row to the index table above
