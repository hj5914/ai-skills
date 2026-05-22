# MEMORY Entry Template

Append short lessons to the project's `MEMORY.md` after a successful delivery when the task revealed reusable knowledge.

```markdown
## YYYY-MM-DD - <feature-or-incident-name>

- Context:
- Lesson:
- Actionable rule for future work:
- Evidence:
```

## Example

```markdown
## 2026-05-22 - bulk-task-archive

- Context: Added bulk archive to the task list.
- Lesson: The task list keeps stale rows after bulk mutations unless the list query is invalidated explicitly.
- Actionable rule for future work: Any bulk task mutation must invalidate the task list query before showing a success toast.
- Evidence: Manual smoke test plus `TaskToolbar.test.tsx`.
```

## Notes

- Keep entries short and specific.
- Skip trivial facts that are obvious from reading the diff.
- Prefer project pitfalls, framework quirks, and repeatable guardrails.
