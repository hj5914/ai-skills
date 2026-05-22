---
name: business-delivery-orchestrator
description: End-to-end business requirement delivery workflow for Codex, Claude Code, and Gemini. Use when asked to take a product or engineering requirement from analysis through implementation, testing, verification, and handoff; when deciding whether to stay single-agent or delegate frontend, backend, product, test, review, or research subtasks; when coordinating full-stack feature work while avoiding unnecessary subagent cost and context bloat.
---

# Business Delivery Orchestrator

Use this skill to deliver a business requirement as one controlled workflow. Default to a single primary agent. Delegate only when the task crosses clear complexity thresholds and the delegated work can run independently with bounded files, bounded outputs, and a stable contract.

This skill is harness-neutral:
- In Codex, use native subagents only when explicitly available and appropriate.
- In Claude Code, use Task/subagent calls or installed agents only when the thresholds below are met.
- In Gemini or single-agent environments, execute the same phases locally and treat "delegation" as role-based self-review.

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

Users can explicitly request the fast path by saying "quick fix", "fast path", or "skip process" — this bypasses auto-classification and forces the lightweight workflow unless a Hard Trigger fires.

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
| Auth/Payment/Migration | Any change touching these surfaces | Full contract, no fast path |
| Implementation start | M+ task without a contract | Contract written and confirmed |
| Subagent dispatch | Delegation without a prompt contract | Prompt contract filled per Subagent Prompt Contract section |
| Delivery | L/XL task without adversarial review | Adversarial review completed (Step 6) |
| Tech stack change | Proposal to swap DB/framework/library | Explicit user confirmation keyword (CONFIRM_TECH) |

## Workflow

1. Classify the request.
   - **Impact Scan**: Before sizing, perform a quick "read-only" scan of the project's dependency graph. Identify how many files import the target module or share the data schema. Use this to confirm the Size and Hard Triggers.
   - Identify user goal, affected surfaces, expected deliverable, deadline pressure, and ambiguity.
   - When using the bundled CLI, record touched surfaces in `.bdo.state.json` via repeated `--surface` flags so later verification can scale appropriately.
   - If the request is only analysis or brainstorming, stop before implementation and return the analysis.
   - If the request qualifies for the fast path, use the fast path and avoid the full workflow.
   - If the request is implementation, continue through verification unless blocked.

2. Build a delivery contract before coding.
   - **Constitution Mining**: Automatically extract technical constraints by reading project config files (e.g., `package.json`, `tsconfig.json`, `.eslintrc`). Add these to the `Constraints` section to ensure compliance with the existing tech stack. **Hard constraint**: Never swap the project's existing database, framework, language, or key library for an alternative without explicit user approval — even if blocked by setup issues.
   - **Clarify Quiz**: Before drafting the contract, identify 3-5 technical ambiguities or boundary risks (e.g., edge cases, legacy impact). Present them to the user as a structured "quiz" to resolve unknowns early.
   - Capture goal, non-goals, user flow, data/API contract, UI states, acceptance criteria, risks, and verification commands.
   - **Two-Pass Contract (L/XL only)**: For L/XL tasks, split the contract into two passes. **Pass 1 (WHAT)**: Goal, Behavior, Non-goals, Acceptance Criteria — confirm with user before proceeding. **Pass 2 (HOW)**: Data/API, Frontend/Backend contract, Verification plan — written after WHAT is confirmed. This prevents premature technical decisions from polluting requirement understanding.
   - For M tasks, use the lightweight template in `templates/lightweight-contract-template.md`.
   - **No Placeholders**: Contracts and plans must never contain TBD, TODO, "implement later", "add appropriate error handling", "Similar to Task N", or steps that describe what to do without showing how. Every step must have exact file paths and complete code.
   - Keep it concise in the working context. Use `references/delivery-contract.md` or `templates/full-delivery-contract-template.md` when the requirement is ambiguous, cross-functional, full-stack, or L/XL.

3. Decide whether to delegate.
   - Default: no subagents.
   - Delegate only if the delegation matrix says the task is medium/high complexity and the work can be isolated.
   - **Branch Isolation**: If delegating write access and the environment supports it (e.g., Claude Code, local Shell), prefer creating a temporary branch or worktree for the subagent to ensure physical code isolation.
   - Read `references/delegation-matrix.md` before spawning any subagent or recommending a multi-agent plan.

4. Plan file ownership.
   - Assign each implementation slice to one owner.
   - Avoid parallel edits to the same file unless using isolated branches/worktrees and a merge step.
   - Keep product/research/review agents read-only unless the user explicitly wants artifact drafts.

5. Implement.
   - **Micro-Tasking**: Break the plan into granular tasks that can be verified in ~5 minutes (Red-Green-Refactor cycle).
   - Prefer the repository's existing patterns.
   - Keep changes scoped to the delivery contract.
   - **Contract Alignment**: After each sub-task, verify the implementation still aligns with the contract. If deviating, pause and update the contract delta before proceeding.
   - If subagents produce code or diffs, treat them as drafts. The primary agent reviews, adapts, and applies final changes.
   - If the user changes scope midstream, record the delta before continuing: added behavior, removed behavior, affected files/contracts, and verification impact.

6. Verify.
   - **Adversarial Review (Two-Stage for L/XL)**:
     1. **Spec Compliance Review**: Verify the implementation matches the contract — nothing missing, nothing extra. Use an independent read-only Reviewer subagent for L/XL tasks.
     2. **Code Quality Review**: Inspect for correctness, performance, security, and maintainability. Use a separate Reviewer subagent (not the same one from Stage 1).
     3. Identify 3 potential failure modes (concurrency, data loss, UI lag). If no flaws are found, the review is incomplete.
     For M tasks, combine both stages into a single self-review pass.
   - **Cross-Phase Consistency Check (L/XL)**: Before running tests, verify alignment across all artifacts: Contract → Plan → Implementation. Check: (1) every AC has a corresponding task, (2) every implemented file traces back to the plan, (3) no extra features beyond the contract scope slipped in.
   - Run the smallest meaningful checks first, then broader checks when risk warrants it.
   - Use `references/verification-gates.md` for selecting tests, lint/type checks, E2E, review passes, and stop conditions.
   - When using the bundled CLI, persist structured verification results (`checks`, `escalation`, `stop_conditions`) into state so handoff can reuse them.
   - Self-review the final diff for scope drift, existing-pattern fit, boundary cases, and unrelated changes before reporting completion.

7. Deliver.
   - Report what changed, what was verified, known residual risks, and any follow-up that is truly useful.
   - **Knowledge Base Update**: After a successful delivery, identify 1-2 lessons learned (e.g., a tricky library behavior or a project-specific pitfall). Append these to the project's `MEMORY.md` using `templates/memory-entry-template.md`.
   - If blocked, report the blocker, evidence, and the next concrete action.
   - Use `templates/handoff-template.md` for the delivery report unless the environment already has a stricter handoff format.
   - When using the bundled CLI, prefer generating handoff after verify so it can pull the latest delta and verification summary from state.

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

## Context Budget

Use the smallest process that preserves correctness:
- Small context or simple task: single agent, no subagents.
- Medium context or medium task: at most one explorer/reviewer/test designer in parallel.
- Long context or high-complexity task: up to three bounded subagents, plus primary integration.
- Avoid more than four concurrent workers unless the user explicitly asks for large-scale orchestration and isolated worktrees are available.

Summarize subagent results before integrating them. Do not paste full long outputs into the main context unless a specific detail is needed.

## Anti-Overhead Controls

- **Confirmation Protocol**: On critical gates (Contract approval, Plan review, Release), provide a 3-line summary and wait for a specific confirmation keyword (e.g., `CONFIRM_PLAN`).
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
- Reuse `templates/lightweight-contract-template.md`, `templates/full-delivery-contract-template.md`, `templates/handoff-gate-checklist-template.md`, `templates/handoff-template.md`, and `templates/memory-entry-template.md` instead of rewriting these artifacts from scratch.
- Read `examples/minimal-feature-delivery-example.md` when a user or teammate needs a concise end-to-end example of how this skill should be applied.

## Bundled CLI

This skill includes a local helper at `tools/bdo.py`. Use it when structured artifacts or stable machine-readable output are useful; skip it for trivial fast-path work.

- `python3 tools/bdo.py init --objective "..."` initializes `.bdo.state.json`
- `python3 tools/bdo.py classify --size M --risk medium --surface ui --surface api` records task shape and touched surfaces
- `python3 tools/bdo.py contract`, `verify`, `handoff`, `memory`, `delta`, `status` generate or inspect workflow artifacts
- Contract generation pre-fills surface-aware defaults from state, `delta` writes a structural summary, and state writes are atomic so repeated CLI calls do not leave half-written JSON
- `verify` supports `--evidence` and `--gap`, `memory` supports `--context` / `--lesson` / `--rule` / `--evidence`, and `handoff` reuses the latest delta plus verification evidence instead of recomputing from scratch
- Add `--json` when another agent or script should consume the result programmatically
- State shape is documented in `schema/bdo-state.schema.json`
