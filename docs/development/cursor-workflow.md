# Cursor Workflow

How the Georgian CX Platform team uses AI assistants and Cursor for phased development.

## Roles

| Role | Who | Responsibility |
|------|-----|----------------|
| **Project manager** | ChatGPT / Claude | Phase planning, step proposals, prompt authoring, output review |
| **Product architect** | ChatGPT / Claude | Vision, Universal Case model, roadmap alignment |
| **Technical architect** | ChatGPT / Claude | Stack decisions, architecture docs, ADRs |
| **Security reviewer** | ChatGPT / Claude | Security baseline, RBAC design, acceptance criteria |
| **QA planner** | ChatGPT / Claude | Test strategy per phase, acceptance criteria |
| **Cursor prompt author** | ChatGPT / Claude | Ready-to-paste implementation prompts |
| **Implementation agent** | Cursor Pro | Code and file changes within approved step scope |
| **Product owner** | Founder | Approves steps, tests output, makes final decisions |
| **Tester** | Founder | Verifies acceptance criteria before next step |
| **Decision-maker** | Founder | Approves or rejects phase transitions |

## Working method

```text
1. ChatGPT/Claude proposes ONE step
         │
         ▼
2. Founder approves (or adjusts scope)
         │
         ▼
3. ChatGPT/Claude generates a ready-to-paste Cursor prompt
         │
         ▼
4. Founder pastes prompt into Cursor Pro
         │
         ▼
5. Cursor runs the step (creates/modifies files)
         │
         ▼
6. Founder reports Cursor output back to ChatGPT/Claude
         │
         ▼
7. ChatGPT/Claude reviews against acceptance criteria
         │
         ▼
8. If pass → propose next step
   If fail → generate correction prompt for Cursor
```

## Rules for Cursor prompts

- Each prompt covers **one step** with explicit acceptance criteria
- Prompts list what **must not** be built
- Prompts reference the current phase (e.g. Phase 0 / Step 1)
- Correction prompts fix alignment only — no feature creep
- Never skip to a future phase without founder approval

## Rules for Cursor implementation

- Read existing code and docs before changing files
- Do not install dependencies unless the step explicitly requires it
- Do not implement business logic in foundation steps
- Do not create files with alternative names when exact names are specified
- Report what was created, modified, and verified at the end

## Current position

| Item | Value |
|------|-------|
| Phase | 0 — Project Foundation |
| Completed step | Step 1 — Monorepo skeleton and documentation alignment |
| Next step | Phase 0 / Step 2 — Docker Compose local services |
| Phase 1 | **Not started** |

## Related docs

- [Development rules](development-rules.md)
- [Product roadmap](../product/roadmap.md)
