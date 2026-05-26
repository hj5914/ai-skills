from __future__ import annotations

VERIFY_RECIPES = {
    "smoke": [
        "Recipe smoke: start the affected service or app and exercise one representative happy path before handoff.",
    ],
    "ui-smoke": [
        "Recipe ui-smoke: render the changed screen in a running app and exercise one representative user-visible flow.",
        "Recipe ui-smoke: if the touched view owns them, inspect loading, empty, and error states in the running UI.",
    ],
    "api-smoke": [
        "Recipe api-smoke: start the changed service and send one representative request that covers the modified contract.",
        "Recipe api-smoke: capture the observed status code or payload shape in runtime evidence.",
    ],
    "frontend-backend-smoke": [
        "Recipe frontend-backend-smoke: start the touched frontend and backend together and exercise one representative end-to-end flow across the changed boundary.",
        "Recipe frontend-backend-smoke: capture the user-visible result plus one backend-observed proof such as response status, persisted change, or log line.",
    ],
    "auth-runtime": [
        "Recipe auth-runtime: verify one login or session happy path and one denial or expired-session path in a running environment.",
        "Recipe auth-runtime: record cookie, token, origin, or CORS behavior that matters to the changed auth flow.",
    ],
    "config-runtime": [
        "Recipe config-runtime: start the service with deployment-like configuration and confirm required env or config keys are present.",
        "Recipe config-runtime: capture one startup log, health-path check, or equivalent runtime proof.",
    ],
    "env-change-runtime": [
        "Recipe env-change-runtime: start the changed service or app with the new or changed environment variables actually populated.",
        "Recipe env-change-runtime: record one observed proof that the runtime consumed the expected configuration rather than only compiling with it.",
    ],
    "deploy-config-check": [
        "Recipe deploy-config-check: compare newly required env or config keys against the intended deployment-like environment before handoff.",
        "Recipe deploy-config-check: record one startup, health-path, or deployment-log proof that the target environment shape is sufficient.",
    ],
}
RUNTIME_EVIDENCE_EXAMPLES = {
    "smoke": [
        'Example runtime evidence: "Opened the changed app flow and completed one representative happy path successfully."',
    ],
    "ui-smoke": [
        'Example runtime evidence: "Rendered the changed screen and confirmed loading -> success transition in the running UI."',
    ],
    "api-smoke": [
        'Example runtime evidence: "curl -i http://localhost:3000/example returned 200 with the expected payload shape."',
    ],
    "frontend-backend-smoke": [
        'Example runtime evidence: "Completed the changed end-to-end flow; UI updated and backend returned 200 with the persisted change visible."',
    ],
    "auth-runtime": [
        'Example runtime evidence: "Login happy path returned 200 and set-cookie; denial path returned 403 with the expected error body."',
    ],
    "config-runtime": [
        'Example runtime evidence: "Service startup log showed required env loaded and /health returned 200 in the deployment-like environment."',
    ],
    "env-change-runtime": [
        'Example runtime evidence: "Started the service with the new env vars populated; startup log and behavior confirmed the runtime consumed them."',
    ],
    "deploy-config-check": [
        'Example runtime evidence: "Compared required env keys against the target environment and verified startup/health succeeded without missing-config errors."',
    ],
}
GAP_CATEGORY_ORDER = {"static": 0, "runtime": 1, "deploy": 2}
DEPLOY_RUNTIME_KEYWORDS = (
    "health",
    "startup",
    "started",
    "boot",
    "booted",
    "env",
    "environment",
    "config",
    "configuration",
    "deploy",
    "deployment",
    "listening",
    "ready",
)


def verify_recipe_choices() -> list[str]:
    return sorted(VERIFY_RECIPES)


def render_verify(state: dict, *, recipes: list[str] | None = None) -> str:
    summary = state.get("verification_summary") or build_verification_summary(state)
    size = state.get("size", "")
    risk = state.get("risk", "")
    surfaces = state.get("surfaces", [])
    checks = summary["checks"]
    escalation = summary["escalation"]
    stop_conditions = summary["stop_conditions"]
    evidence = summary.get("evidence", [])
    runtime_evidence = summary.get("runtime_evidence", [])
    gaps = summary.get("gaps", [])
    formatted_gaps = format_verification_gaps(gaps)
    example_runtime_evidence = runtime_evidence_examples(recipes=recipes or [], surfaces=surfaces)

    return f"""# Verification Report

State:
- phase={state.get("phase", "")}
- size={size}
- risk={risk}
- surfaces={", ".join(surfaces) if surfaces else "none"}

Recommended checks:
{_as_bullets(checks)}

Evidence collected:
{_as_bullets(evidence or ["No execution evidence recorded yet"])}

Runtime evidence collected:
{_as_bullets(runtime_evidence or ["No runtime or end-to-end evidence recorded yet"])}

Coverage gaps:
{_as_bullets(formatted_gaps or ["No explicit gaps recorded; add one if verification is partial"])}

Suggested runtime evidence entries:
{_as_bullets(example_runtime_evidence or ["No recipe-specific runtime evidence examples suggested."])}

Escalation:
{_as_bullets(escalation)}

Stop conditions:
{_as_bullets(stop_conditions)}

Notes:
- Use `--evidence` for commands or manual checks that actually ran.
- Use `--runtime-evidence` for service startup, representative requests, UI flows, or other dynamic behavior checks that actually ran.
- Use `--recipe` to add a verification checklist template; recipes do not execute commands or start tools for you.
- Use `--gap` for skipped validation, missing environments, or unresolved coverage holes.
- Build or typecheck success is not enough to claim runtime behavior is correct.
"""


def build_verification_summary(
    state: dict,
    *,
    evidence: list[str] | None = None,
    runtime_evidence: list[str] | None = None,
    gaps: list[str] | None = None,
    recipes: list[str] | None = None,
) -> dict:
    size = state.get("size", "")
    risk = state.get("risk", "")
    surfaces = state.get("surfaces", [])
    selected_recipes = _normalize_unique(recipes or [])
    runtime_entries = runtime_evidence or []
    gap_entries = verification_gap_hints(
        state,
        runtime_evidence=runtime_entries,
        gaps=gaps or [],
        recipes=selected_recipes,
    )
    return {
        "checks": _normalize_unique(_checks_for_surfaces(surfaces) + _checks_for_recipes(selected_recipes)),
        "escalation": _escalation_triggers(size=size, risk=risk, surfaces=surfaces),
        "stop_conditions": _stop_conditions(size=size, risk=risk, surfaces=surfaces),
        "evidence": evidence or [],
        "runtime_evidence": runtime_entries,
        "gaps": _normalize_unique(gap_entries),
    }


def verification_gap_hints(
    state: dict,
    *,
    runtime_evidence: list[str] | None = None,
    gaps: list[str] | None = None,
    recipes: list[str] | None = None,
) -> list[str]:
    surface_set = set(state.get("surfaces", []))
    runtime_entries = runtime_evidence or []
    selected_recipes = recipes or []
    gap_entries = list(gaps or [])
    if selected_recipes and not runtime_entries:
        gap_entries.append(
            "[runtime_recipe_pending] Selected verification recipe(s) still need host-run runtime checks; add `--runtime-evidence` after they actually run."
        )
    if not runtime_entries and ({"ui", "backend"} & surface_set or "api" in surface_set or "auth" in surface_set):
        gap_entries.append(
            "[runtime_not_run] No runtime or end-to-end evidence was recorded yet for the changed app/service flow."
        )
    if "config" in surface_set and {"backend", "api", "auth"} & surface_set and not has_deploy_like_runtime_evidence(runtime_entries):
        gap_entries.append(
            "[deploy_env_unchecked] Deployment-like startup or health-path verification is still missing; required env or config keys remain unproven at runtime."
        )
    return _normalize_unique(gap_entries)


def has_deploy_like_runtime_evidence(runtime_evidence: list[str] | None) -> bool:
    for entry in runtime_evidence or []:
        lowered = entry.lower()
        if any(keyword in lowered for keyword in DEPLOY_RUNTIME_KEYWORDS):
            return True
    return False


def runtime_evidence_examples(*, recipes: list[str], surfaces: list[str]) -> list[str]:
    examples: list[str] = []
    for recipe in recipes:
        examples.extend(RUNTIME_EVIDENCE_EXAMPLES.get(recipe, []))
    surface_set = set(surfaces)
    if not examples and "auth" in surface_set:
        examples.append(
            'Example runtime evidence: "Auth happy path succeeded and denial path returned the expected status/body."'
        )
    if not examples and "config" in surface_set and {"backend", "api", "auth"} & surface_set:
        examples.append(
            'Example runtime evidence: "Service startup/health proved the required env or config keys were present at runtime."'
        )
    if not examples and "ui" in surface_set and ("backend" in surface_set or "api" in surface_set):
        examples.append(
            'Example runtime evidence: "Completed one representative end-to-end user flow and confirmed the backend-observed result."'
        )
    if not examples and ("backend" in surface_set or "api" in surface_set):
        examples.append(
            'Example runtime evidence: "Representative request returned the expected status/payload in the running service."'
        )
    return _normalize_unique(examples)


def gap_category(gap: str) -> str:
    if gap.startswith("[deploy_env_unchecked]"):
        return "deploy"
    if gap.startswith("[runtime_"):
        return "runtime"
    return "static"


def format_verification_gaps(gaps: list[str]) -> list[str]:
    ordered = sorted(gaps, key=lambda gap: (GAP_CATEGORY_ORDER.get(gap_category(gap), 99), gap))
    labels = {"static": "Static", "runtime": "Runtime", "deploy": "Deploy"}
    return [f"{labels[gap_category(gap)]}: {gap}" for gap in ordered]


def _as_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _checks_for_surfaces(surfaces: list[str]) -> list[str]:
    checks = ["Inspect final diff for unrelated changes", "Confirm contract alignment before delivery"]
    surface_set = set(surfaces)
    mapping = {
        "copy": "Run formatter or preview check if available",
        "config": "Run config validation or targeted typecheck",
        "ui": "Run component test or manual UI render check; cover loading/empty/error states",
        "backend": "Run focused unit/integration test for the changed backend logic",
        "api": "Run representative request or contract-oriented integration check",
        "utility": "Run direct caller regression coverage for the shared utility",
        "data": "Run migration or dry-run reasoning plus rollback review",
        "auth": "Verify positive and negative permission cases",
        "payment": "Verify success, failure, retry, and duplicate-submission payment paths",
        "migration": "Run migration or dry-run plus rollback and compatibility review",
        "external": "Verify timeout/error behavior and no-credential fallback path",
        "performance": "Inspect complexity and run a targeted benchmark/profile if available",
    }
    for surface in surfaces:
        if surface in mapping:
            checks.append(mapping[surface])
    if "auth" in surface_set:
        checks.append("Run login/session happy-path and denial-path verification, not just build or typecheck")
    if "auth" in surface_set and {"ui", "backend"} & surface_set:
        checks.append(
            "Confirm cookie or session behavior, including sameSite and secure expectations for the active environment"
        )
    if "auth" in surface_set and {"api", "backend", "config"} & surface_set:
        checks.append(
            "Confirm required auth-related env or config keys exist and CORS or origin settings match the changed flow"
        )
    if "config" in surface_set and {"backend", "api", "auth"} & surface_set:
        checks.append(
            "Start the service with deployment-like configuration and verify required env or config keys are present via startup or health-path behavior"
        )
    if {"ui", "backend"} & surface_set or "api" in surface_set or "auth" in surface_set:
        checks.append("Start the affected service or app and exercise one representative runtime or end-to-end flow.")
    if not surfaces:
        checks.append("Run one focused test or manual smoke check")
    return checks


def _checks_for_recipes(recipes: list[str]) -> list[str]:
    checks: list[str] = []
    for recipe in recipes:
        checks.extend(VERIFY_RECIPES.get(recipe, []))
    return checks


def _normalize_unique(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _escalation_triggers(*, size: str, risk: str, surfaces: list[str]) -> list[str]:
    triggers = []
    if size in {"L", "XL"}:
        triggers.append("Run adversarial review and broader integration validation")
    if risk.lower() in {"high", "critical"}:
        triggers.append("Increase verification depth because the task risk is high")
    if {"auth", "data", "payment", "migration"} & set(surfaces):
        triggers.append("Add explicit rollback, denial, or irreversible-path review for sensitive surfaces")
    if {"ui", "backend"} <= set(surfaces) or {"ui", "api"} <= set(surfaces):
        triggers.append("Verify frontend/backend contract alignment because multiple layers changed")
    if not triggers:
        triggers.append("No extra escalation required beyond focused verification")
    return triggers


def _stop_conditions(*, size: str, risk: str, surfaces: list[str]) -> list[str]:
    conditions = [
        "Stop if required credentials, services, or user decisions are missing",
        "Stop if the repo has unrelated dirty changes that make isolation impossible",
    ]
    if {"data", "auth", "payment", "migration"} & set(surfaces) or risk.lower() in {"high", "critical"}:
        conditions.append("Stop before destructive validation unless approval is explicit")
    if size in {"L", "XL"}:
        conditions.append("Stop if contract and implementation drift before verification is complete")
    return conditions
