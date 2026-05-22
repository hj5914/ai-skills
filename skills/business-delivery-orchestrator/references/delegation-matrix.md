# Delegation Matrix

Use this reference before creating subagents or recommending multi-agent execution.

## Complexity Levels

| Level | Signals | Default execution |
|---|---|---|
| XS | Read-only answer, docs/copy, one-file mechanical fix, no behavior risk | Answer or fast path |
| Small | 1-3 files, known pattern, no API/schema change, low risk | Single primary agent |
| Medium | 4-10 files, one boundary crossing, moderate tests, some unknowns | Primary agent plus optional explorer/reviewer |
| High | Full-stack flow, data/API contract, migrations, UI states, integration tests | Primary agent plus bounded specialist subagents |
| Very high | Multiple services, high-risk security/data/payment behavior, conflicting ownership | Plan first; consider worktrees or external orchestration |

Use the higher level when a risky surface appears even if the file count is low: auth, permissions, billing, data migration, destructive operations, public API changes, or irreversible user-visible behavior.

## Delegation Decision

Delegate only when all are true:
- The subtask has a clear output that can be reviewed.
- The subtask can proceed without blocking the primary agent's immediate next step.
- File ownership is disjoint or the subagent is read-only.
- The expected value exceeds the context and coordination cost.

Stay single-agent when any are true:
- The implementation is a small linear change.
- The files are tightly coupled and likely to conflict.
- Requirements are still too vague to assign.
- The subagent would repeat context gathering the primary agent already completed.

## Cost Controls

- Prefer one read-only helper over multiple implementation helpers.
- **Physical Isolation**: When environment permits (e.g., local shell access), use `git worktree` or temporary branches for subagents to prevent workspace pollution.
- Prefer sequential local work over parallel work when integration would take longer than implementation.
- Reuse already gathered context instead of asking subagents to rediscover it.
- Give subagents excerpts, not entire plans, when an excerpt is enough.
- Limit each subagent to one role and one deliverable.
- If two subagents would inspect the same files for similar reasons, merge the assignment.

## Misclassification Recovery

If a task was classified too large:
- Stop adding process.
- Keep the useful contract notes.
- Finish as a single-agent fast path.

If a task was classified too small and risk appears:
- Pause implementation.
- Write or update the delivery contract.
- Decide whether one targeted subagent or reviewer is justified.

## Role Patterns

| Role | Best use | Write access |
|---|---|---|
| Product | Clarify acceptance criteria, edge cases, non-goals | Read-only, unless drafting docs |
| Frontend | Isolated UI components, state handling, accessibility pass | Frontend files only |
| Backend | API, domain logic, persistence, validation | Backend files only |
| Test | Test matrix, focused test implementation, regression gaps | Test files only, or read-only review |
| Security | Auth, permissions, data exposure, injection risks | Usually read-only review |
| Explorer | Locate code paths, map dependencies, answer concrete questions | Read-only |
| Reviewer | Find bugs in final diff | Read-only |

## Role Boundaries

- Explorer: one question, one answer, no implementation suggestions unless asked.
- Product: clarify behavior and acceptance criteria; do not invent scope expansion.
- Frontend: owns view/component/state files listed in the prompt.
- Backend: owns endpoint/domain/persistence files listed in the prompt.
- Test: owns test files or returns a test matrix; do not change production code unless explicitly assigned.
- Security/performance/accessibility reviewer: inspect the changed behavior and report concrete risks with file references.
- Worker: implement a bounded slice; never edit files outside the assigned write set without asking.

Avoid parallel workers when their output must be merged into the same file. Use one owner for that file and make other agents read-only reviewers.

## Recommended Patterns

Small task:
```text
Primary agent only.
```

Medium task:
```text
Primary implements.
One read-only explorer or reviewer runs in parallel.
```

High full-stack task:
```text
Primary freezes contract.
Backend subagent owns backend files.
Frontend subagent owns frontend files.
Test/review subagent is read-only or owns test files.
Primary integrates and verifies.
Prefer temporary branches for subagents.
```

Very high task:
```text
Create a plan and ask for approval before large execution.
Mandatory isolated worktrees or mission-based orchestration.
Primary agent merges, resolves conflicts, and verifies.
```

## Stop Delegating

Collapse back to primary-agent execution when:
- Subagent outputs conflict with the contract.
- Integration cost exceeds remaining implementation cost.
- The same context must be repeated to multiple agents.
- The next meaningful step is blocked on a single design decision.

## Prompt Template

```markdown
You are not alone in this codebase. Other work may happen concurrently. Do not revert unrelated changes.

Task:
[bounded subtask]

Shared contract:
[relevant excerpt]

Scope (Principle of Least Privilege):
- Read: [Explicit list of allowed files. Do not discover globally.]
- Write: [Explicit list of allowed files.]
- Do not touch: [Any overlapping/risky files.]

Return:
## Result
- Completed:
- Changed files or files inspected:
- Contract assumptions:
- Risks:
- Needs primary integration:

Keep the response concise. If blocked, explain the exact blocker and evidence.
```
