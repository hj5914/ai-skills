---
name: business-delivery-orchestrator
description: End-to-end business requirement delivery workflow for Codex, Claude Code, and Gemini. Use when asked to take a product or engineering requirement from analysis through implementation, testing, verification, and handoff; when deciding whether to stay single-agent or delegate frontend, backend, product, test, review, or research subtasks; when coordinating full-stack feature work while avoiding unnecessary subagent cost and context bloat.
---

# Business Delivery Orchestrator

Use this skill to deliver a business requirement as one controlled workflow. Default to a single primary agent. Delegate only when the work is clearly separable and worth the coordination cost. When native subagents are unavailable, keep the same phases and treat delegation as role-based self-review.

## Core Rule

Maintain one owner for the outcome. The primary agent owns scope, contract, implementation consistency, verification, and the final user report. Subagents may advise, explore, review, or implement bounded slices, but they do not own the product behavior.

Prefer the lightest path that satisfies the user's request. If the user asks for a quick fix, direct answer, or small change, do not expand into a full delivery workflow.

## Fast Path

Use the fast path for small, clear work:
- One file or a tightly related small set of files.
- No schema, API contract, permissions, billing, security, or migration impact.
- Existing pattern is obvious.
- Verification can be local and focused.

Fast path steps:
1. Restate only the essential assumption if needed.
2. Make the change directly.
3. Run the smallest meaningful check.
4. Report the result briefly.

Skip delivery-contract templates, subagent decisions, and detailed handoff sections on the fast path unless a risk appears.

Users can explicitly request the fast path by saying "quick fix", "fast path", or "skip process" unless a Hard Trigger applies.

## Task Sizing

Size the task before choosing process depth:

| Size | Signals | Hard Triggers (Force larger size) | Default path |
|---|---|---|---|
| XS | Read-only answer, docs/copy, one-file mechanical fix, no behavior risk | N/A | Answer or fast path |
| S | 1-3 related files, known pattern, focused local check | N/A | Fast path |
| M | 4-10 files, one boundary crossing, moderate ambiguity, meaningful tests | Auth logic, migration scripts | Lightweight contract, usually single-agent |
| L | Full-stack flow, API/schema/data/permissions, new user workflow | Payment logic, public API change | Full contract, consider bounded delegation |
| XL | Multiple services, release coordination, security/payment/migration risk, team handoff | Cross-repo coordination, irreversible actions | Plan first; use references before execution |

When signals conflict, choose the heavier path only for the risky surface. Do not let a large file count alone turn a simple mechanical change into a product workflow.

## Hard Gates

These gates block progress until satisfied. Treat them as mandatory, not advisory:

| Gate | Trigger | Requirement |
|---|---|---|
| Auth/Data/Payment/Migration | Any change touching these surfaces | Full contract, no fast path |
| Implementation start | M+ task without a contract | Contract written and confirmed |
| Subagent dispatch | Delegation without a prompt contract | Prompt contract filled per Subagent Prompt Contract section |
| Delivery | L/XL task without adversarial review | Adversarial review completed (Step 6) |
| Tech stack change | Proposal to swap DB/framework/library | Explicit user confirmation keyword (CONFIRM_TECH) |

## Workflow

1. Classify the request.
   - **Impact Scan**: Before sizing, perform a quick read-only scan of likely dependents. When using the bundled CLI, `scan` checks direct path matches first, then import/use references, then separates code/test/doc text fallback matches and applies a small sensitive-surface bump to inform sizing. Treat the result as a heuristic, not a complete dependency graph.
   - Identify user goal, affected surfaces, expected deliverable, deadline pressure, and ambiguity.
   - Before committing to one M/L/XL workflow, check whether the request is actually several low-coupling fixes that should be split into separate deliveries.
   - For M+ tasks, report the classified size, risk, and rationale to the user before proceeding; if the user disagrees, reclassify.
   - If the request is only analysis or brainstorming, stop before implementation and return the analysis.
   - If the request qualifies for the fast path, use the fast path and avoid the full workflow.
   - If the request is implementation, continue through verification unless blocked.

2. Build a delivery contract before coding.
   - **Constitution Mining**: Extract technical constraints by reading project config files (e.g., `package.json`, `tsconfig.json`, `.eslintrc`). When using the bundled CLI, `mine` can prefill a lightweight set of detected constraints. The primary agent still owns validation and interpretation. **Hard constraint**: Never swap the project's existing database, framework, language, or key library for an alternative without explicit user approval — even if blocked by setup issues.
   - **Clarify Quiz**: Identify 3-5 technical ambiguities or boundary risks before drafting the contract. Present them to the user only when the answers materially affect behavior, safety, permissions, or irreversible actions.
   - Capture goal, non-goals, user flow, data/API contract, UI states, acceptance criteria, risks, and verification commands.
   - **Two-Pass Contract (L/XL only)**: For L/XL tasks, the primary agent should split the contract into two passes. **Pass 1 (WHAT)**: Goal, Behavior, Non-goals, Acceptance Criteria — confirm with user before proceeding. **Pass 2 (HOW)**: Data/API, Frontend/Backend contract, Verification plan — written after WHAT is confirmed. This prevents premature technical decisions from polluting requirement understanding.
   - For M tasks, use the lightweight template in `templates/lightweight-contract-template.md`.
   - **No Placeholders**: Contracts and plans must never contain TBD, TODO, "implement later", "add appropriate error handling", "Similar to Task N", or steps that describe what to do without showing how. Every step must have exact file paths and complete code.
   - Keep it concise. Use `references/delivery-contract.md` when the requirement is ambiguous, cross-functional, or L/XL.

3. Decide whether to delegate.
   - Default: no subagents.
   - Before spawning any subagent or recommending a multi-agent plan, read `references/delegation-matrix.md`.
   - Delegate only if the delegation matrix says the task is medium/high complexity and the work can be isolated.
   - Skip the delegation reference entirely when the task remains single-agent or fast-path.
   - **Branch Isolation**: If delegating write access and the environment supports isolated branches or worktrees, prefer them for physical code isolation. This skill does not create worktrees automatically.

4. Plan file ownership.
   - Assign each implementation slice to one owner.
   - Avoid parallel edits to the same file unless using isolated branches/worktrees and a merge step.
   - Keep product/research/review agents read-only unless the user explicitly wants artifact drafts.

5. Implement.
   - **Micro-Tasking**: Break the plan into granular tasks that can be verified in ~5 minutes (Red-Green-Refactor cycle).
   - Prefer the repository's existing patterns.
   - Keep changes scoped to the delivery contract.
   - **Contract Alignment**: After each sub-task, verify the implementation still aligns with the contract. If deviating, pause and update the contract delta before proceeding.
   - Treat subagent output as draft input, not final truth.
   - If the user changes scope midstream, record the delta before continuing.

6. Verify.
   - **Adversarial Review (Two-Stage for L/XL)**:
     1. **Spec Compliance Review**: Verify the implementation matches the contract — nothing missing, nothing extra. Prefer an independent read-only Reviewer subagent for L/XL tasks when the host environment supports it.
     2. **Code Quality Review**: Inspect for correctness, performance, security, and maintainability. Prefer a separate Reviewer subagent (not the same one from Stage 1) when available.
     3. Identify 3 potential failure modes (concurrency, data loss, UI lag). If no flaws are found, the review is incomplete.
     For M tasks, combine both stages into a single self-review pass.
   - For L/XL tasks that require adversarial review, use at least one independent read-only Reviewer subagent when the environment supports subagents. If subagents are unavailable, proceed with role-based self-review but explicitly report that review independence is limited.
   - For M+ tasks, run `tools/bdo.py verify` before reporting verification complete.
   - **Cross-Phase Consistency Check (L/XL)**: Before running tests, verify Contract → Plan → Implementation alignment.
   - Run the smallest meaningful checks first, then broader checks when risk warrants it.
   - For `auth/data/payment/migration` work, include configuration presence checks and one key user or caller flow verification, not just build or typecheck.
   - For `config + backend/api/auth` changes, verify the service can start with deployment-like configuration and that newly required env or config keys are actually available at runtime.
   - When dynamic validation runs, record it explicitly as runtime evidence instead of folding it into generic build or test evidence.
   - Use `references/verification-gates.md` for verification depth and stop conditions.
   - Self-review the final diff for scope drift, existing-pattern fit, boundary cases, and unrelated changes before reporting completion.

7. Deliver.
   - Report what changed, what was verified, known residual risks, and any follow-up that is truly useful.
   - **Knowledge Base Update**: After a successful delivery, append 1-2 reusable lessons to `MEMORY.md`.
   - For M+ tasks, run `tools/bdo.py handoff` before reporting delivery complete.
   - Record scope-external findings or debt as explicit follow-up items instead of silently absorbing them into the current delivery.
   - If blocked, report the blocker, evidence, and the next concrete action.
   - Use `templates/handoff-template.md` unless the environment already has a stricter handoff format.

## Progress Tracking

After completing each phase, mark it in a brief status block. This gives the user visibility into where the task stands:

```markdown
## BDO Progress
1. [x] Classify
2. [x] Contract
3. [ ] Delegate (skipped — single agent)
4. [x] Plan ownership
5. [ ] Implement (in progress)
6. [ ] Verify
7. [ ] Deliver
```

Update this block at each phase transition. Use `[x]` for done, `[ ]` for pending, `[-]` for skipped.

## Delegation Policy

Do not create subagents just because roles exist. Create them only when at least one of these is true:
- The work has independent frontend/backend/test/research slices with low file overlap.
- The codebase is unfamiliar and a parallel explorer can answer a bounded question while implementation proceeds.
- The requirement is security, performance, accessibility, or data-sensitive enough to justify an independent review.
- The implementation is large enough that a single context would crowd out verification details.

**Context isolation**: Subagents must receive only crafted, bounded context — never inherit the primary agent's full session history or conversation. Construct exactly what the subagent needs: the relevant contract excerpt, the exact file scope, and the output format. This prevents context pollution and keeps subagents focused.

Do not delegate when:
- The task is a small bug fix, copy change, simple endpoint, simple UI tweak, or one-file refactor.
- The next step depends on the subagent's answer and would block local progress.
- The subagent would need to modify the same files as the primary agent without isolation.
- The only benefit is role theater.

Before spawning subagents, state the reason in one sentence. If the reason sounds weak, stay single-agent.

Common bounded delegation:
- Explorer: answer one concrete codebase question; read-only.
- Reviewer: inspect risk in a final or near-final diff; read-only.
- Tester: design or implement focused tests; test files only unless approved.
- Worker: implement one isolated slice with a disjoint write set.

**Model selection by task type**:
- Mechanical (1-2 files, clear spec, existing pattern) → cheapest available model
- Integration (multi-file coordination, moderate ambiguity) → standard model
- Review, architecture, or design judgment → most capable model

## Subagent Prompt Contract

When delegation is warranted, every subagent prompt must include:
- The delivery contract or the relevant excerpt.
- The exact role and responsibility.
- Read/write scope, including file or module boundaries.
- Output format and length limit.
- A reminder that other work may happen concurrently and they must not revert unrelated changes.

Require this output:

```markdown
## Result

Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED

- DONE: Task complete, proceed to review.
- DONE_WITH_CONCERNS: Completed but flagged doubts. Read concerns before proceeding.
- NEEDS_CONTEXT: Missing information blocked progress. Provide context and re-dispatch.
- BLOCKED: Cannot complete. Assess: (1) more context needed, (2) task needs stronger model, (3) task too large — split it, (4) plan is wrong — escalate to user.

Completed:
Changed files (or Files inspected):
Contract assumptions:
Risks:
Needs primary integration:
```

For read-only review or exploration, replace "Changed files" with "Files inspected".

For reviewer-specific work, prefer the dedicated prompt templates:
- `templates/reviewer-spec-prompt-template.md` for Stage 1 spec-compliance review
- `templates/reviewer-quality-prompt-template.md` for Stage 2 code-quality review

## Context Budget

Use the smallest process that preserves correctness:
- Small context or simple task: single agent, no subagents.
- Medium context or medium task: at most one explorer/reviewer/test designer in parallel.
- Long context or high-complexity task: up to three bounded subagents, plus primary integration.
- Avoid more than four concurrent workers unless the user explicitly asks for large-scale orchestration and isolated worktrees are available.

Summarize subagent results before integrating them. Do not paste full long outputs into the main context unless a specific detail is needed.

## Anti-Overhead Controls

- **Confirmation Protocol**: On critical gates (Contract approval, Plan review, Release), prefer a 3-line summary and a specific confirmation keyword (e.g., `CONFIRM_PLAN`) when the host environment and user workflow support explicit approvals.
- Cap the active delivery contract at roughly 20 bullets unless the user asks for a detailed plan.
- Ask at most three clarifying questions before making conservative assumptions.
- Do not read reference files unless the current phase needs them.
- Do not run broad test suites when a focused check covers the change and risk is low.
- Do not force product-style acceptance criteria onto pure refactors, dependency fixes, or infra chores.
- If the workflow starts feeling heavier than the task, collapse to the fast path and continue.
- If the user explicitly asks to skip planning or avoid subagents, obey unless safety or data-loss risk requires a pause.

## ECC-Inspired Compatibility

This skill intentionally borrows these patterns without depending on ECC:
- Team selection is optional, like `team-builder`; use it only when choosing specialists adds value.
- Planning precedes execution, like `multi-plan`.
- The primary agent keeps code sovereignty, like `multi-execute`.
- Parallel work must have clear boundaries, like `dmux-workflows`.
- Verification is part of delivery, like `tdd-workflow`, `verification-loop`, and `e2e-testing`.

If ECC tools or agents are installed, use them as implementation mechanisms, but keep this skill's delegation thresholds and primary-owner rule.

## Reference Files

- Read `references/delegation-matrix.md` when deciding whether to use subagents, external agents, worktrees, or role-based self-review.
- Read `references/delivery-contract.md` when requirements need a shared contract before implementation.
- Read `references/verification-gates.md` when selecting verification depth, escalation triggers, or stop conditions.
- Reuse `templates/lightweight-contract-template.md`, `templates/full-delivery-contract-template.md`, `templates/reviewer-spec-prompt-template.md`, `templates/reviewer-quality-prompt-template.md`, `templates/handoff-gate-checklist-template.md`, `templates/handoff-template.md`, and `templates/memory-entry-template.md` instead of rewriting these artifacts from scratch.
- Read `examples/minimal-feature-delivery-example.md` when a user or teammate needs a concise end-to-end example of how this skill should be applied.

## Bundled CLI

This skill includes a local helper at `tools/bdo.py`. Use it when structured artifacts or machine-readable output are useful; skip it for trivial fast-path work.

- Core commands: `init`, `classify`, `phase`, `quiz`, `scan`, `mine`, `contract`, `contract-what`, `contract-how`, `review`, `verify`, `handoff`, `memory`, `delta`, `status`, `resume`
- Enforced checks: `auth/data/payment/migration` work requires a full contract; manual `phase` transitions cannot bypass required contract / verify artifacts; M/L/XL verification requires a contract; L/XL work cannot stop at `contract-what` and must reach `contract-how` or `contract --mode full`; handoff requires contract and verification files that still exist; L/XL handoff also requires completed `spec` and `quality` reviews
- Soft reminders: `classify` and contract commands suggest `quiz` when the task is large or risky and no clarify quiz has been recorded yet
- `resume` summarizes missing artifacts, phase/state mismatches, and minimal recovery actions for blocked reviews
- Output: add `--json` for machine-readable output
- State shape: see `schema/bdo-state.schema.json`
