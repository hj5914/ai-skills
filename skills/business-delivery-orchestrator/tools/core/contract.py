from __future__ import annotations

from core.templates import (
    checklist_block,
    fill_once,
    list_block,
    load_template_code_block,
    replace_section_placeholder,
)

SURFACE_BEHAVIOR = {
    "ui": "Update user-visible states and feedback using existing UI patterns.",
    "backend": "Keep backend validation and business rules aligned with the requested behavior.",
    "api": "Preserve request/response contract alignment across callers and handlers.",
    "auth": "Enforce explicit allow/deny behavior for permission-sensitive paths.",
    "data": "Preserve data compatibility and rollback reasoning for stored state changes.",
    "external": "Handle timeout and failure behavior for external dependencies.",
    "performance": "Avoid regressions on latency-sensitive or high-volume paths.",
    "config": "Keep configuration changes scoped and compatible with existing defaults.",
    "utility": "Protect shared callers from unintended regressions.",
    "copy": "Keep wording changes consistent with the existing UX tone and context.",
}


def render_contract(
    *,
    objective: str,
    size: str,
    risk: str,
    mode: str,
    surfaces: list[str],
    constraints_detected: list[str] | None = None,
    clarify_assumptions: list[str] | None = None,
) -> str:
    if mode == "what":
        return _render_what_contract(
            objective=objective,
            size=size,
            risk=risk,
            surfaces=surfaces,
            clarify_assumptions=clarify_assumptions,
        )
    if mode == "how":
        return _render_how_contract(
            objective=objective,
            size=size,
            risk=risk,
            surfaces=surfaces,
            constraints_detected=constraints_detected,
            clarify_assumptions=clarify_assumptions,
        )
    if mode == "full" or size in {"L", "XL"}:
        return _render_full_contract(
            objective=objective,
            size=size,
            risk=risk,
            surfaces=surfaces,
            constraints_detected=constraints_detected,
            clarify_assumptions=clarify_assumptions,
        )
    return _render_lightweight_contract(
        objective=objective,
        size=size,
        risk=risk,
        surfaces=surfaces,
        constraints_detected=constraints_detected,
        clarify_assumptions=clarify_assumptions,
    )


def _render_what_contract(
    *, objective: str, size: str, risk: str, surfaces: list[str], clarify_assumptions: list[str] | None = None
) -> str:
    template = load_template_code_block("full-delivery-contract-template.md")
    template = fill_once(template, "## Delivery Contract", "## Delivery Contract - WHAT")
    template = fill_once(template, "Goal:\n- ", f"Goal:\n- {objective or ''}")
    template = replace_section_placeholder(template, "Non-goals:", list_block(_non_goal_defaults(surfaces)))
    template = replace_section_placeholder(template, "Constraints (Constitution):", list_block(_constraints_defaults(surfaces)))
    template = fill_once(template, "- Actor:", f"- Actor: {'End user' if 'ui' in surfaces else 'API or service caller'}")
    template = fill_once(template, "- Trigger:", f"- Trigger: {objective or 'Requested feature change'}")
    template = fill_once(template, "- Success path:", f"- Success path: {_success_path(surfaces)}")
    template = fill_once(template, "- Failure states:", f"- Failure states: {_failure_states(surfaces)}")
    template = fill_once(template, "- Empty/loading states:", f"- Empty/loading states: {_empty_loading_defaults(surfaces)}")
    template = replace_section_placeholder(template, "Acceptance criteria:", checklist_block(_acceptance_defaults(surfaces)[:3]))
    template = replace_section_placeholder(
        template,
        "Risks and assumptions:",
        list_block(_assumption_defaults(size=size, risk=risk, surfaces=surfaces, clarify_assumptions=clarify_assumptions)),
    )
    template = replace_section_placeholder(template, "Data and API:", "- Shared behavior is intentionally deferred to the HOW pass.\n- ")
    template = replace_section_placeholder(template, "Frontend contract:", "- Shared behavior is intentionally deferred to the HOW pass.\n- ")
    template = replace_section_placeholder(template, "Backend contract:", "- Shared behavior is intentionally deferred to the HOW pass.\n- ")
    template = replace_section_placeholder(template, "Verification plan:", "- Shared behavior is intentionally deferred to the HOW pass.\n- ")
    return template


def _render_how_contract(
    *,
    objective: str,
    size: str,
    risk: str,
    surfaces: list[str],
    constraints_detected: list[str] | None = None,
    clarify_assumptions: list[str] | None = None,
) -> str:
    template = load_template_code_block("full-delivery-contract-template.md")
    template = fill_once(template, "## Delivery Contract", "## Delivery Contract - HOW")
    template = fill_once(template, "Goal:\n- ", f"Goal:\n- {objective or ''}")
    template = replace_section_placeholder(template, "Non-goals:", list_block(_non_goal_defaults(surfaces)))
    template = replace_section_placeholder(
        template,
        "Constraints (Constitution):",
        list_block(_constraints_defaults(surfaces, constraints_detected=constraints_detected)),
    )
    template = fill_once(template, "- Actor:", f"- Actor: {'End user' if 'ui' in surfaces else 'API or service caller'}")
    template = fill_once(template, "- Trigger:", f"- Trigger: {objective or 'Requested feature change'}")
    template = fill_once(template, "- Success path:", f"- Success path: {_success_path(surfaces)}")
    template = fill_once(template, "- Failure states:", f"- Failure states: {_failure_states(surfaces)}")
    template = fill_once(template, "- Empty/loading states:", f"- Empty/loading states: {_empty_loading_defaults(surfaces)}")
    template = fill_once(template, "- Inputs:", f"- Inputs: {_data_inputs(surfaces)}")
    template = fill_once(template, "- Outputs:", f"- Outputs: {_data_outputs(surfaces)}")
    template = fill_once(template, "- Validation:", f"- Validation: {_validation_defaults(surfaces)}")
    template = fill_once(template, "- Error behavior:", f"- Error behavior: {_error_behavior_defaults(surfaces)}")
    template = fill_once(template, "- Permissions:", f"- Permissions: {'Follow the existing access-control model and denial behavior.' if 'auth' in surfaces else 'No new permission model assumed.'}")
    template = fill_once(template, "- Views/components:", f"- Views/components: {'Reuse existing screens/components that expose the changed flow.' if 'ui' in surfaces else 'No frontend surface change planned.'}")
    template = fill_once(template, "- State transitions:", f"- State transitions: {'Keep visible state, loading, empty, and failure transitions aligned with the contract.' if 'ui' in surfaces else 'No client-side state transition change planned.'}")
    template = fill_once(template, "- Accessibility:", f"- Accessibility: {_accessibility_defaults(surfaces)}")
    template = fill_once(template, "- Responsive behavior:", f"- Responsive behavior: {_responsive_defaults(surfaces)}")
    template = fill_once(template, "- Endpoints/functions:", f"- Endpoints/functions: {'Update the relevant endpoint/service boundary without widening scope.' if {'backend', 'api', 'auth', 'data'} & set(surfaces) else 'No backend endpoint or service contract change planned.'}")
    template = fill_once(template, "- Persistence:", f"- Persistence: {'Preserve compatibility of persisted data and rollback reasoning.' if 'data' in surfaces else 'No persistence schema change planned.'}")
    template = fill_once(template, "- Side effects:", f"- Side effects: {'Make external calls and notifications explicit in the implementation boundary.' if 'external' in surfaces else 'No new external side effects planned.'}")
    template = fill_once(template, "- Observability:", f"- Observability: {_observability_defaults(surfaces)}")
    template = replace_section_placeholder(template, "Acceptance criteria:", checklist_block(_acceptance_defaults(surfaces)[:3]))
    template = replace_section_placeholder(
        template,
        "Risks and assumptions:",
        list_block(_assumption_defaults(size=size, risk=risk, surfaces=surfaces, clarify_assumptions=clarify_assumptions)),
    )
    return template


def _render_lightweight_contract(
    *,
    objective: str,
    size: str,
    risk: str,
    surfaces: list[str],
    constraints_detected: list[str] | None = None,
    clarify_assumptions: list[str] | None = None,
) -> str:
    template = load_template_code_block("lightweight-contract-template.md")
    template = fill_once(template, "Goal:\n- ", f"Goal:\n- {objective or ''}")
    constraints = _constraints_defaults(surfaces, constraints_detected=constraints_detected)
    non_goals = _non_goal_defaults(surfaces)
    behaviors = _behavior_defaults(surfaces)
    acceptance = _acceptance_defaults(surfaces)
    verification = _verification_defaults(surfaces)
    assumptions = _assumption_defaults(size=size, risk=risk, surfaces=surfaces, clarify_assumptions=clarify_assumptions)
    if constraints:
        template = replace_section_placeholder(template, "Constraints (Constitution):", list_block(constraints))
    if behaviors:
        template = replace_section_placeholder(template, "Behavior:", list_block(behaviors))
    if non_goals:
        template = replace_section_placeholder(template, "Non-goals:", list_block(non_goals))
    if acceptance:
        template = replace_section_placeholder(template, "Acceptance:", checklist_block(acceptance[:2]))
    if verification:
        template = replace_section_placeholder(template, "Verification:", list_block(verification))
    template = replace_section_placeholder(template, "Assumptions:", list_block(assumptions))
    return template


def _render_full_contract(
    *,
    objective: str,
    size: str,
    risk: str,
    surfaces: list[str],
    constraints_detected: list[str] | None = None,
    clarify_assumptions: list[str] | None = None,
) -> str:
    template = load_template_code_block("full-delivery-contract-template.md")
    template = fill_once(template, "Goal:\n- ", f"Goal:\n- {objective or ''}")

    actor = "End user" if "ui" in surfaces else "API or service caller"
    trigger = objective or "Requested feature change"
    success_path = _success_path(surfaces)
    failure_states = _failure_states(surfaces)
    inputs = _data_inputs(surfaces)
    outputs = _data_outputs(surfaces)
    validation = _validation_defaults(surfaces)
    error_behavior = _error_behavior_defaults(surfaces)
    permissions = (
        "Follow the existing access-control model and denial behavior."
        if "auth" in surfaces
        else "No new permission model assumed."
    )
    frontend_views = (
        "Reuse existing screens/components that expose the changed flow."
        if "ui" in surfaces
        else "No frontend surface change planned."
    )
    frontend_state = (
        "Keep visible state, loading, empty, and failure transitions aligned with the contract."
        if "ui" in surfaces
        else "No client-side state transition change planned."
    )
    backend_endpoints = (
        "Update the relevant endpoint/service boundary without widening scope."
        if {"backend", "api", "auth", "data"} & set(surfaces)
        else "No backend endpoint or service contract change planned."
    )
    backend_persistence = (
        "Preserve compatibility of persisted data and rollback reasoning."
        if "data" in surfaces
        else "No persistence schema change planned."
    )
    backend_side_effects = (
        "Make external calls and notifications explicit in the implementation boundary."
        if "external" in surfaces
        else "No new external side effects planned."
    )
    verification = _verification_plan_for_full(surfaces)
    acceptance = _acceptance_defaults(surfaces)[:3]
    risks = _assumption_defaults(size=size, risk=risk, surfaces=surfaces, clarify_assumptions=clarify_assumptions)
    if "auth" in surfaces:
        risks.append("permission-denial behavior must be verified explicitly")
    if "data" in surfaces:
        risks.append("data compatibility and rollback path need review")

    template = replace_section_placeholder(template, "Non-goals:", list_block(_non_goal_defaults(surfaces)))
    template = replace_section_placeholder(
        template,
        "Constraints (Constitution):",
        list_block(_constraints_defaults(surfaces, constraints_detected=constraints_detected)),
    )
    template = fill_once(template, "- Actor:", f"- Actor: {actor}")
    template = fill_once(template, "- Trigger:", f"- Trigger: {trigger}")
    template = fill_once(template, "- Success path:", f"- Success path: {success_path}")
    template = fill_once(template, "- Failure states:", f"- Failure states: {failure_states}")
    template = fill_once(template, "- Empty/loading states:", f"- Empty/loading states: {_empty_loading_defaults(surfaces)}")
    template = fill_once(template, "- Inputs:", f"- Inputs: {inputs}")
    template = fill_once(template, "- Outputs:", f"- Outputs: {outputs}")
    template = fill_once(template, "- Validation:", f"- Validation: {validation}")
    template = fill_once(template, "- Error behavior:", f"- Error behavior: {error_behavior}")
    template = fill_once(template, "- Permissions:", f"- Permissions: {permissions}")
    template = fill_once(template, "- Views/components:", f"- Views/components: {frontend_views}")
    template = fill_once(template, "- State transitions:", f"- State transitions: {frontend_state}")
    template = fill_once(template, "- Accessibility:", f"- Accessibility: {_accessibility_defaults(surfaces)}")
    template = fill_once(template, "- Responsive behavior:", f"- Responsive behavior: {_responsive_defaults(surfaces)}")
    template = fill_once(template, "- Endpoints/functions:", f"- Endpoints/functions: {backend_endpoints}")
    template = fill_once(template, "- Persistence:", f"- Persistence: {backend_persistence}")
    template = fill_once(template, "- Side effects:", f"- Side effects: {backend_side_effects}")
    template = fill_once(template, "- Observability:", f"- Observability: {_observability_defaults(surfaces)}")
    template = fill_once(template, "- Unit:", f"- Unit: {verification['unit']}")
    template = fill_once(template, "- Integration:", f"- Integration: {verification['integration']}")
    template = fill_once(template, "- E2E/manual:", f"- E2E/manual: {verification['manual']}")
    template = fill_once(template, "- Build/lint/typecheck:", f"- Build/lint/typecheck: {verification['build']}")
    template = replace_section_placeholder(template, "Acceptance criteria:", checklist_block(acceptance))
    template = replace_section_placeholder(template, "Risks and assumptions:", list_block(risks))
    return template


def _constraints_defaults(surfaces: list[str], *, constraints_detected: list[str] | None = None) -> list[str]:
    items = ["Follow project-wide instructions first (`CLAUDE.md`, `AGENT.md`, `GEMINI.md`, repo docs, existing config)."]
    if constraints_detected:
        items.extend(constraints_detected[:4])
    if {"api", "backend", "auth", "data"} & set(surfaces):
        items.append("Preserve existing contracts and avoid widening external behavior without explicit approval.")
    else:
        items.append("Stay within existing repository patterns and avoid incidental redesign.")
    return items


def _behavior_defaults(surfaces: list[str]) -> list[str]:
    defaults = [SURFACE_BEHAVIOR[s] for s in surfaces if s in SURFACE_BEHAVIOR]
    if not defaults:
        defaults.append("Keep the requested behavior aligned with the existing repository patterns.")
    return defaults


def _non_goal_defaults(surfaces: list[str]) -> list[str]:
    items = ["Do not expand scope into unrelated cleanup, redesign, or tech-stack changes."]
    if "ui" in surfaces and not ({"api", "backend"} & set(surfaces)):
        items.append("Do not invent new backend behavior that is not already supported.")
    if {"api", "backend"} & set(surfaces) and "ui" not in surfaces:
        items.append("Do not introduce new user-visible flows beyond the requested boundary.")
    return items


def _acceptance_defaults(surfaces: list[str]) -> list[str]:
    items = ["The changed behavior satisfies the requested outcome without expanding scope."]
    if "ui" in surfaces:
        items.append("User-visible states cover success, loading, empty, and failure where relevant.")
    if "api" in surfaces or "backend" in surfaces:
        items.append("Contract boundaries remain aligned across callers and handlers.")
    if "auth" in surfaces:
        items.append("Authorized and unauthorized paths behave explicitly and predictably.")
    if "data" in surfaces:
        items.append("Data changes preserve compatibility and rollback reasoning.")
    return items


def _verification_defaults(surfaces: list[str]) -> list[str]:
    items = ["Inspect the final diff for unrelated churn."]
    if "ui" in surfaces:
        items.append("Run a component test or manual UI render check.")
    if "backend" in surfaces or "api" in surfaces:
        items.append("Run a focused integration or representative request check.")
    if "auth" in surfaces:
        items.append("Verify both positive and negative permission paths.")
    if "data" in surfaces:
        items.append("Review migration, compatibility, or rollback behavior.")
    if len(items) == 1:
        items.append("Run one focused test or manual smoke check.")
    return items


def _success_path(surfaces: list[str]) -> str:
    if "ui" in surfaces and ("api" in surfaces or "backend" in surfaces):
        return "User action completes end-to-end and the visible state reflects the persisted result."
    if "ui" in surfaces:
        return "User-visible flow completes with clear feedback."
    return "Caller receives the expected result without contract drift."


def _failure_states(surfaces: list[str]) -> str:
    items = []
    if "auth" in surfaces:
        items.append("permission denial")
    if "external" in surfaces:
        items.append("timeout or dependency failure")
    if "data" in surfaces:
        items.append("validation or compatibility failure")
    return ", ".join(items) if items else "validation or request failure"


def _empty_loading_defaults(surfaces: list[str]) -> str:
    if "ui" in surfaces:
        return "Define loading, empty, and retry states wherever the changed flow can pause or fail."
    return "No user-visible loading or empty state is expected."


def _data_inputs(surfaces: list[str]) -> str:
    if "api" in surfaces or "backend" in surfaces:
        return "request payload plus existing persisted state"
    if "ui" in surfaces:
        return "user input and current client-side view state"
    return "the minimal inputs required by the changed behavior"


def _data_outputs(surfaces: list[str]) -> str:
    if "ui" in surfaces and ("api" in surfaces or "backend" in surfaces):
        return "updated server result and synchronized UI state"
    if "api" in surfaces or "backend" in surfaces:
        return "updated response payload and any persisted changes"
    return "the changed user-visible output"


def _validation_defaults(surfaces: list[str]) -> str:
    parts = []
    if "backend" in surfaces or "api" in surfaces:
        parts.append("request shape and domain rule validation")
    if "auth" in surfaces:
        parts.append("permission validation")
    if "data" in surfaces:
        parts.append("compatibility validation")
    return "; ".join(parts) if parts else "follow existing repository validation rules"


def _error_behavior_defaults(surfaces: list[str]) -> str:
    if "external" in surfaces:
        return "surface dependency failures clearly and avoid silent retries by default"
    if "ui" in surfaces:
        return "show an explicit failure state without leaving stale optimistic state behind"
    return "return the existing error shape without widening scope"


def _accessibility_defaults(surfaces: list[str]) -> str:
    if "ui" in surfaces:
        return "Preserve existing keyboard, focus, labeling, and screen-reader semantics."
    return "No new accessibility surface is expected."


def _responsive_defaults(surfaces: list[str]) -> str:
    if "ui" in surfaces:
        return "Preserve existing breakpoint behavior and avoid layout regressions."
    return "No responsive behavior change planned."


def _observability_defaults(surfaces: list[str]) -> str:
    if {"backend", "api", "external", "data", "auth"} & set(surfaces):
        return "Reuse existing logs/metrics where available; add only the minimal diagnostics needed for changed paths."
    return "No observability change planned."


def _verification_plan_for_full(surfaces: list[str]) -> dict[str, str]:
    return {
        "unit": "focus on direct logic changes and boundary cases",
        "integration": (
            "verify changed contracts across touched layers"
            if {"api", "backend", "ui"} & set(surfaces)
            else "run one representative integration path if applicable"
        ),
        "manual": "smoke the user-facing flow and failure states" if "ui" in surfaces else "run a representative command or request",
        "build": "run relevant build, lint, or typecheck targets for touched modules",
    }


def _assumption_defaults(
    *, size: str, risk: str, surfaces: list[str], clarify_assumptions: list[str] | None = None
) -> list[str]:
    items = [f"size={size}", f"risk={risk}", f"surfaces={', '.join(surfaces) if surfaces else 'none'}"]
    if clarify_assumptions:
        items.extend(clarify_assumptions[:4])
    return items
