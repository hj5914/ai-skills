from __future__ import annotations


def render_verify(state: dict) -> str:
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
{_as_bullets(gaps or ["No explicit gaps recorded; add one if verification is partial"])}

Escalation:
{_as_bullets(escalation)}

Stop conditions:
{_as_bullets(stop_conditions)}

Notes:
- Use `--evidence` for commands or manual checks that actually ran.
- Use `--runtime-evidence` for service startup, representative requests, UI flows, or other dynamic behavior checks that actually ran.
- Use `--gap` for skipped validation, missing environments, or unresolved coverage holes.
- Build or typecheck success is not enough to claim runtime behavior is correct.
"""


def build_verification_summary(
    state: dict,
    *,
    evidence: list[str] | None = None,
    runtime_evidence: list[str] | None = None,
    gaps: list[str] | None = None,
) -> dict:
    size = state.get("size", "")
    risk = state.get("risk", "")
    surfaces = state.get("surfaces", [])
    return {
        "checks": _checks_for_surfaces(surfaces),
        "escalation": _escalation_triggers(size=size, risk=risk, surfaces=surfaces),
        "stop_conditions": _stop_conditions(size=size, risk=risk, surfaces=surfaces),
        "evidence": evidence or [],
        "runtime_evidence": runtime_evidence or [],
        "gaps": gaps or [],
    }


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
