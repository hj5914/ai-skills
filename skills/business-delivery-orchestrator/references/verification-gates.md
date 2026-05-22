# Verification Gates

Use this reference to choose verification depth and prepare handoff.

## Verification Depth

| Change type | Minimum checks | Add when risk is higher |
|---|---|---|
| Docs/copy | Formatting or preview when available | Link checks |
| UI-only | Component/unit tests or manual render check | Accessibility, visual, E2E |
| Backend logic | Unit tests, focused integration tests | Contract tests, security review |
| Full-stack feature | Unit/integration plus smoke path | E2E, browser check, API regression |
| Data/schema | Migration test or dry-run, rollback reasoning | Backup/compatibility review |
| Auth/security/payment | Focused tests plus independent review | Threat review, audit logs, negative tests |

## Quick Selection Table

| Surface changed | Minimum useful verification |
|---|---|
| Copy/config only | Inspect diff; run formatter or config validation when available |
| UI component | Render or component test; check loading/empty/error states if touched |
| API endpoint | Focused unit/integration test or representative request |
| Shared utility | Existing tests for direct callers plus one regression case |
| Database migration | Apply/dry-run migration; reason about rollback and compatibility |
| Permissions/auth | Positive and negative cases; verify denial behavior |
| External API/network | Timeout/error behavior; no-credential fallback or mocked test |
| Performance-sensitive path | Inspect complexity and run targeted benchmark/profile if available |

## Gate Sequence

1. Static sanity:
   - Format/lint/typecheck if available and relevant.
   - Inspect final diff for unrelated changes.

2. Focused tests:
   - Run the smallest test target that covers the touched code.
   - Add or update tests when behavior changed and the repo has a test pattern.

3. Integration checks:
   - Verify frontend/backend contract alignment.
   - Check error, empty, loading, and permission states.

4. User-facing smoke:
   - Run dev server or browser checks when the task is UI-heavy and tooling is available.
   - For CLI/API tasks, run representative commands or requests.

5. Adversarial Review (Mandatory for L/XL):
   - Identify 3 potential failure modes (concurrency, data loss, UI lag).
   - Document how they are addressed or why they are acceptable risks.

6. Review:
   - Use self-review for small/medium changes.
   - Use subagent or specialist review for high-risk security, data, performance, or accessibility changes.

## Self-Review Checklist

Before reporting completion, check:
- The diff matches the contract or documented delta.
- No unrelated files or generated churn slipped in.
- **Adversarial Review**: 3 failure modes identified and addressed (L/XL).
- Existing patterns, naming, and error handling were followed.
- Boundary cases are covered: empty, invalid, unauthorized, loading, failure, and rollback where relevant.
- Tests or manual checks exercise the changed behavior, not just implementation details.
- Remaining risks are explicit in the handoff.

## Low-Risk Shortcut

For small changes, verification may be:
- Inspect diff.
- Run one focused test, typecheck, lint target, or manual smoke check.
- If no relevant check exists, state that clearly and explain the manual reasoning.

Do not run slow broad checks by default when the change is isolated and the project has a clearer focused check.

## Escalation Triggers

Increase verification depth when:
- A public API, database schema, auth, billing, permissions, or data migration changed.
- Frontend and backend contracts changed together.
- A bug fix touches shared utilities or framework configuration.
- Existing tests are absent around risky behavior.
- A subagent or review found a concrete issue.

## Handoff Format

```markdown
Changed:
- 

Verified:
- 

Not verified:
- 

Risks:
- 

Next:
- 
```

## Stop Conditions

Stop and report instead of forcing completion when:
- Required credentials, services, or user decisions are missing.
- Tests require destructive operations without approval.
- The codebase has unrelated dirty changes that make the task impossible to isolate.
- The requirement conflicts with existing architecture or policy.
