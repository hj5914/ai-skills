# Full Delivery Contract Template

Use this when the requirement crosses product, frontend, backend, data, or test boundaries and needs a shared source of truth.

```markdown
## Delivery Contract

Goal:
- 

Non-goals:
- 

Constraints (Constitution):
- Global project instructions always win (`CLAUDE.md`, `AGENT.md`, `GEMINI.md`, repo policies, existing config).
- Existing framework, language, database, and key library choices are fixed unless the user explicitly approves a change.
- 

Users and workflow:
- Actor:
- Trigger:
- Success path:
- Failure states:
- Empty/loading states:

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

## Notes

- Prefer existing repository behavior over new invention.
- Update the contract before changing code when product behavior or API shape shifts.
- For `L/XL` tasks, split into a WHAT pass and a HOW pass before implementation.
