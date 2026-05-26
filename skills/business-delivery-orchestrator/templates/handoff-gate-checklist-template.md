# Handoff Gate Checklist Template

Use this checklist before final delivery for `P0-P2` implementation work or any task with moderate-to-high user impact.

```markdown
## Handoff Gate

- [ ] Evidence attached
  - Screenshot, log output, test report, or equivalent proof included
- [ ] Residual risk stated
  - Example: "Not tested with production-like volume"
- [ ] Lessons learned captured when reusable
  - `MEMORY.md` entry prepared only for reusable project knowledge, recurring failure modes, or durable guardrails
- [ ] Cleanup complete
  - No debug logs, temporary files, stray `TODO`s, or unmerged scratch worktrees
```

## Notes

- The checklist is a gate, not the final handoff report itself.
- Pair this with `templates/handoff-template.md`.
- For low-risk small changes, use judgment instead of forcing full ceremony.
