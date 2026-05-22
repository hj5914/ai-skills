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

## Task Sizing

Size the task before choosing process depth:

| Size | Signals | Default path |
|---|---|---|
| XS | Read-only answer, docs/copy, one-file mechanical fix, no behavior risk | Answer or fast path |
| S | 1-3 related files, known pattern, focused local check | Fast path |
| M | 4-10 files, one boundary crossing, moderate ambiguity, meaningful tests | Lightweight contract, usually single-agent |
| L | Full-stack flow, API/schema/data/permissions, new user workflow | Full contract, consider bounded delegation |
| XL | Multiple services, release coordination, security/payment/migration risk, team handoff | Plan first; use references before execution |

When signals conflict, choose the heavier path only for the risky surface. Do not let a large file count alone turn a simple mechanical change into a product workflow.

## Workflow

1. Classify the request.
   - Identify user goal, affected surfaces, expected deliverable, deadline pressure, and ambiguity.
   - If the request is only analysis or brainstorming, stop before implementation and return the analysis.
   - If the request qualifies for the fast path, use the fast path and avoid the full workflow.
   - If the request is implementation, continue through verification unless blocked.

2. Build a delivery contract before coding.
   - Capture goal, non-goals, user flow, data/API contract, UI states, acceptance criteria, risks, and verification commands.
   - For M tasks, use this lightweight contract inline:
     ```markdown
     Goal:
     Behavior:
     Acceptance:
     Verification:
     Assumptions:
     ```
   - Keep it concise in the working context. Use `references/delivery-contract.md` when the requirement is ambiguous, cross-functional, full-stack, or L/XL.

3. Decide whether to delegate.
   - Default: no subagents.
   - Delegate only if the delegation matrix says the task is medium/high complexity and the work can be isolated.
   - Read `references/delegation-matrix.md` before spawning any subagent or recommending a multi-agent plan.

4. Plan file ownership.
   - Assign each implementation slice to one owner.
   - Avoid parallel edits to the same file unless using isolated branches/worktrees and a merge step.
   - Keep product/research/review agents read-only unless the user explicitly wants artifact drafts.

5. Implement.
   - Prefer the repository's existing patterns.
   - Keep changes scoped to the delivery contract.
   - If subagents produce code or diffs, treat them as drafts. The primary agent reviews, adapts, and applies final changes.
   - If the user changes scope midstream, record the delta before continuing: added behavior, removed behavior, affected files/contracts, and verification impact.

6. Verify.
   - Run the smallest meaningful checks first, then broader checks when risk warrants it.
   - Use `references/verification-gates.md` for selecting tests, lint/type checks, E2E, review passes, and handoff criteria.
   - Self-review the final diff for scope drift, existing-pattern fit, boundary cases, and unrelated changes before reporting completion.

7. Deliver.
   - Report what changed, what was verified, known residual risks, and any follow-up that is truly useful.
   - If blocked, report the blocker, evidence, and the next concrete action.
   - Use a short handoff shape when helpful:
     ```markdown
     Changed:
     Verified:
     Not verified:
     Risks:
     Next:
     ```

## Delegation Policy

Do not create subagents just because roles exist. Create them only when at least one of these is true:
- The work has independent frontend/backend/test/research slices with low file overlap.
- The codebase is unfamiliar and a parallel explorer can answer a bounded question while implementation proceeds.
- The requirement is security, performance, accessibility, or data-sensitive enough to justify an independent review.
- The implementation is large enough that a single context would crowd out verification details.

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
- Completed:
- Changed files:
- Contract assumptions:
- Risks:
- Needs primary integration:
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
- Read `references/verification-gates.md` when selecting verification depth or preparing the final handoff.
