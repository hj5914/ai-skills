from __future__ import annotations


def build_clarify_quiz(*, objective: str, size: str, risk: str, surfaces: list[str]) -> dict:
    questions: list[str] = []
    assumptions = [f"size={size}", f"risk={risk}", f"surfaces={', '.join(surfaces) if surfaces else 'none'}"]
    resolved: list[str] = []

    questions.append(
        f"Behavior: What is the exact success outcome for '{objective or 'this change'}', and what should explicitly not happen?"
    )
    questions.append(
        "Boundary risk: Which edge case should fail differently from the happy path, and why would that difference matter to users or callers?"
    )

    if "ui" in surfaces:
        questions.append(
            "UI states: What should loading, empty, error, and retry states look like for the changed flow?"
        )
    if "backend" in surfaces or "api" in surfaces:
        questions.append(
            "Contract boundary: Which request/response field, validation rule, or status behavior is most likely to break existing callers?"
        )
    if "auth" in surfaces:
        questions.append(
            "Permissions: Which actor should be denied, what should they see, and what evidence would prove the denial path works?"
        )
    if "data" in surfaces:
        questions.append(
            "Data safety: What compatibility or rollback assumption would be most dangerous if it turns out to be false?"
        )
    if "external" in surfaces:
        questions.append(
            "Dependency failure: What timeout, fallback, or retry behavior should happen when the external dependency is slow or unavailable?"
        )

    return {
        "questions": questions[:5],
        "assumptions": assumptions,
        "resolved": resolved,
    }


def clarify_warning(*, size: str, risk: str, surfaces: list[str], has_quiz: bool) -> str:
    normalized_risk = risk.lower()
    surface_set = set(surfaces)
    warnings: list[str] = []
    if size in {"M", "L", "XL"} and len(surface_set) >= 3:
        warnings.append(
            "Confirm whether this is one delivery or several independent fixes before committing to a single workflow."
        )
    if has_quiz:
        return " ".join(warnings)
    if size in {"L", "XL"} or normalized_risk in {"high", "critical"} or surface_set & {"auth", "data", "external"}:
        warnings.append("Consider running `quiz` before continuing so contract assumptions are explicit.")
    return " ".join(warnings)
