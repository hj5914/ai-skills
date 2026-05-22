# Delivery Contract

Use this template when a requirement crosses product, frontend, backend, data, or test boundaries. Keep it short enough to fit in the active context.

## Lightweight Contract

Use this version before the full template when the task is moderate but not complex:

```markdown
Goal:
- 

Behavior:
- 

Constraints (Constitution):
- 

Non-goals:
- 

Acceptance:
- [ ] 
- [ ] 

Verification:
- 

Assumptions:
- 
```

Escalate to the full template only when frontend/backend/data/test boundaries need a shared contract.

## Contract Template

```markdown
## Delivery Contract

Goal:
- 

Non-goals:
- 

Constraints (Constitution):
- 

Users and workflow:
- Actor:
- Trigger:
- Success path:
- Failure/empty/loading states:

Data and API:
- Inputs:
- Outputs:
- Validation:
- Error behavior:
- Permissions:

Frontend contract:
- Views/components:
- State transitions:
- Accessibility:
- Responsive behavior:

Backend contract:
- Endpoints/functions:
- Persistence:
- Side effects:
- Observability:

Acceptance criteria:
- [ ] 
- [ ] 
- [ ] 

Verification plan:
- Unit:
- Integration:
- E2E/manual:
- Build/lint/typecheck:

Risks and assumptions:
- 
```

## Contract Rules

- Freeze names and shapes before splitting frontend/backend work.
- Treat API, schema, and acceptance criteria as shared truth.
- If implementation reveals the contract is wrong, update the contract first, then adjust code.
- Do not let each role invent its own version of product behavior.
- Keep contracts proportional. A small task should not grow a full product spec just because a template exists.
- Prefer existing product and codebase patterns over newly invented behavior.

## Ambiguity Handling

Ask the user only when the missing answer changes product behavior, data safety, billing, permissions, or irreversible actions.

Make reasonable assumptions when:
- The repository has an obvious existing pattern.
- The missing detail is presentational and easy to revise.
- The choice can be implemented conservatively without narrowing future options.

State assumptions in the delivery report when they affect behavior.

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

## Template Discipline

- Leave irrelevant sections out instead of filling them with "N/A".
- Keep acceptance criteria testable and few.
- Do not convert obvious implementation chores into product ceremony.
- Prefer repository-derived behavior over invented requirements.
