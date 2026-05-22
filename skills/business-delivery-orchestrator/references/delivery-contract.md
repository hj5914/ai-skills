# Delivery Contract Reference

Use this file to decide which contract artifact to use and how to keep it aligned during delivery. The actual reusable templates live in `templates/`.

## Template Selection

Choose the smallest contract that still prevents behavior drift:

| Situation | Use |
|---|---|
| `XS/S` task, no meaningful behavior risk | No dedicated contract; fast path |
| `M` task, one main boundary crossing, limited ambiguity | `templates/lightweight-contract-template.md` |
| `L/XL` task, cross-functional workflow, shared API/data/UI truth needed | `templates/full-delivery-contract-template.md` or bundled CLI `contract-what` / `contract-how` |

Escalate from lightweight to full when frontend/backend/data/test boundaries need a shared source of truth.

## Contract Workflow

1. Run a quick impact scan.
   - Check which files import the touched module or share the schema.
   - Confirm whether the task size still matches reality.

2. Mine constraints before filling the contract.
   - Read project config and instruction files such as `package.json`, `tsconfig.json`, `CLAUDE.md`, `AGENT.md`, `GEMINI.md`, and local repo docs.
   - Record framework, language, database, and key library constraints before planning implementation.

3. Resolve ambiguity early.
   - Ask only when the missing answer affects product behavior, data safety, billing, permissions, or irreversible actions.
   - Make conservative assumptions when the repository pattern is obvious and the choice is easy to revise.
   - When using the bundled CLI, `quiz` can draft candidate clarifying questions and record resolved assumptions for later contract reuse.

4. Freeze shared behavior.
   - Lock names, API shapes, and acceptance criteria before splitting work across frontend/backend or primary/subagent boundaries.
   - Treat the contract as the shared source of truth during implementation and review.

## Contract Rules

- **Constitution Mining**: Always read project config files (`package.json`, `tsconfig.json`, etc.) before filling the Constraints section to align with existing standards.
- Global project-level rules always take precedence over task-level contract notes.
- Freeze names and shapes before splitting frontend/backend work.
- Treat API, schema, and acceptance criteria as shared truth.
- If implementation reveals the contract is wrong, update the contract first, then adjust code.
- Do not let each role invent its own version of product behavior.
- Keep contracts proportional. A small task should not grow a full product spec just because a template exists.
- Prefer existing product and codebase patterns over newly invented behavior.

## Delta Handling

When requirements change after work has started, do not rewrite the whole contract by default. Add a short delta:

```markdown
## Delta

Added:
- 

Removed:
- 

Changed:
- 

Impact:
- Files/contracts affected:
- Verification changes:
- Work to revisit:
```

Use a delta when the original contract remains mostly true. Rewrite the contract only when the goal, user workflow, or data/API shape changes enough that the old contract would mislead implementers.

## Two-Pass Contract For L/XL

For larger work, avoid jumping straight into implementation details:

1. WHAT pass:
   - Goal
   - Behavior
   - Non-goals
   - Acceptance criteria

2. HOW pass:
   - Data/API
   - Frontend/backend contract
   - Verification plan

Confirm the WHAT pass before writing the HOW pass when the task has high product or integration risk.

When using the bundled CLI, `contract-what` and `contract-how` generate these two passes as separate artifacts.

## Template Discipline

- Leave irrelevant sections out instead of filling them with "N/A".
- Keep acceptance criteria testable and few.
- Do not convert obvious implementation chores into product ceremony.
- Prefer repository-derived behavior over invented requirements.
- Reuse `templates/lightweight-contract-template.md` and `templates/full-delivery-contract-template.md` instead of copying contract skeletons into this reference file.
