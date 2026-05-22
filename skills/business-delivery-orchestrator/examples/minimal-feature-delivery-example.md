# Minimal Feature Delivery Example

Request:

```text
Add a bulk archive action to the task list page. Users can select multiple completed tasks and archive them in one action. Show a success toast and refresh the list. Do not allow archiving active tasks.
```

Assumed codebase:
- React frontend
- Node/Express backend
- Existing task list, task status filter, and toast component

## BDO Progress

```markdown
1. [x] Classify
2. [x] Contract
3. [-] Delegate (single agent)
4. [x] Plan ownership
5. [x] Implement
6. [x] Verify
7. [x] Deliver
```

## Clarify Quiz

```markdown
1. Should the archive action be hidden when no completed tasks are selected, or shown but disabled?
2. If the selection contains one active task and two completed tasks, should the request fail entirely or archive only the valid ones?
3. Should archived tasks disappear immediately from the current list view, or remain until manual refresh?
```

Assumed answers:
- Show the action but keep it disabled until at least one completed task is selected
- Reject the whole request if any selected task is not completed
- Remove archived tasks from the current list immediately after success

## Lightweight Contract

```markdown
Goal:
- Let users archive multiple completed tasks from the task list in one action.

Behavior:
- Users can select tasks from the list.
- The bulk archive action is enabled only when all selected tasks are completed.
- Submitting archives all selected tasks in one request.
- On success, show a toast and refresh the list so archived tasks disappear.
- If any selected task is not completed, return a validation error and keep the current list state.

Constraints (Constitution):
- Follow existing task list selection and toast patterns.
- Reuse the current bulk action request shape if one exists.
- Do not introduce a new state library or new backend framework.

Non-goals:
- Undo archive
- Partial success handling
- Archive history screen

Acceptance:
- [ ] Selecting only completed tasks enables the archive action.
- [ ] Selecting any active task keeps the action disabled or returns a clear validation error.
- [ ] Successful archive removes the tasks from the visible list and shows feedback.

Verification:
- Frontend component test for selection and action state
- Backend test for validation and successful archive path
- Manual smoke check on the task list page

Assumptions:
- Archive is represented by an existing `archived` flag or archived status.
```

## Plan Ownership

```markdown
Owner: Primary agent

1. Inspect task list selection and bulk action patterns.
2. Add archive action state and request wiring.
3. Enforce "completed only" validation in backend service.
4. Add focused tests.
5. Run manual smoke check and prepare handoff.
```

## Delta

```markdown
## Delta

Changed:
- Backend already exposes `POST /tasks/archive`; only frontend wiring and validation message copy are needed.

Impact:
- Files/contracts affected:
  - `frontend/src/features/tasks/TaskToolbar.tsx`
  - `frontend/src/features/tasks/api.ts`
- Verification changes:
  - Reduce backend work to a regression check
```

## Verify

```markdown
Verified:
- Frontend component test covering disabled/enabled archive action states
- Backend service test covering reject-active-task and archive-success cases
- Manual smoke: selected completed tasks archived, toast shown, list refreshed

Potential failure modes reviewed:
- Mixed-status selection bypasses UI guard and reaches backend
- Archived tasks remain visible because list cache is not invalidated
- Double-submit sends duplicate archive requests
```

## Deliver

```markdown
Changed:
- Added bulk archive action wiring on the task list toolbar
- Enforced completed-only validation in the backend archive path
- Added focused frontend and backend regression tests

Verified:
- Component test for action enablement
- Backend validation and success-path tests
- Manual smoke on the task list flow

Not verified:
- High-volume archive performance

Risks:
- If another screen mutates task status concurrently, stale selection could cause a validation error until refresh

Lessons Learned (Update MEMORY.md):
- The task list relies on explicit cache invalidation after bulk mutations
- Bulk action buttons should derive enabled state from selected row data, not only row count

Next:
- Consider adding an undo pattern only if product explicitly asks for recovery
```
