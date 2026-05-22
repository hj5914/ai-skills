## Delivery Contract - WHAT

Goal:
- Two pass contract

Non-goals:
- Do not expand scope into unrelated cleanup, redesign, or tech-stack changes.

Constraints (Constitution):
- Follow project-wide instructions first (`CLAUDE.md`, `AGENT.md`, `GEMINI.md`, repo docs, existing config).
- Preserve existing contracts and avoid widening external behavior without explicit approval.

Users and workflow:
- Actor: End user
- Trigger: Two pass contract
- Success path: User action completes end-to-end and the visible state reflects the persisted result.
- Failure states: validation or request failure
- Empty/loading states: Define loading, empty, and retry states wherever the changed flow can pause or fail.

Data and API:
- Shared behavior is intentionally deferred to the HOW pass.
- 

Frontend contract:
- Shared behavior is intentionally deferred to the HOW pass.
- 

Backend contract:
- Shared behavior is intentionally deferred to the HOW pass.
- 

Acceptance criteria:
- [ ] The changed behavior satisfies the requested outcome without expanding scope.
- [ ] User-visible states cover success, loading, empty, and failure where relevant.
- [ ] Contract boundaries remain aligned across callers and handlers.

Verification plan:
- Shared behavior is intentionally deferred to the HOW pass.
- 

Risks and assumptions:
- size=L
- risk=medium
- surfaces=ui, backend
