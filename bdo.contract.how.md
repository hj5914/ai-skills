## Delivery Contract - HOW

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
- Inputs: request payload plus existing persisted state
- Outputs: updated server result and synchronized UI state
- Validation: request shape and domain rule validation
- Error behavior: show an explicit failure state without leaving stale optimistic state behind
- Permissions: No new permission model assumed.

Frontend contract:
- Views/components: Reuse existing screens/components that expose the changed flow.
- State transitions: Keep visible state, loading, empty, and failure transitions aligned with the contract.
- Accessibility: Preserve existing keyboard, focus, labeling, and screen-reader semantics.
- Responsive behavior: Preserve existing breakpoint behavior and avoid layout regressions.

Backend contract:
- Endpoints/functions: Update the relevant endpoint/service boundary without widening scope.
- Persistence: No persistence schema change planned.
- Side effects: No new external side effects planned.
- Observability: Reuse existing logs/metrics where available; add only the minimal diagnostics needed for changed paths.

Acceptance criteria:
- [ ] The changed behavior satisfies the requested outcome without expanding scope.
- [ ] User-visible states cover success, loading, empty, and failure where relevant.
- [ ] Contract boundaries remain aligned across callers and handlers.

Verification plan:
- Unit:
- Integration:
- E2E/manual:
- Build/lint/typecheck:

Risks and assumptions:
- size=L
- risk=medium
- surfaces=ui, backend
