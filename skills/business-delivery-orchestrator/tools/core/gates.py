from __future__ import annotations

from pathlib import Path


def ensure_contract_allowed(state: dict, mode: str) -> None:
    surfaces = set(state.get("surfaces", []))
    size = state.get("size", "")
    if surfaces & {"auth", "data", "payment", "migration"} and mode != "full":
        raise ValueError("auth/data/payment/migration tasks require `contract --mode full`")
    if size in {"L", "XL"} and mode != "full":
        raise ValueError("L/XL tasks require `contract --mode full`")


def ensure_phase_transition_allowed(state: dict, phase: str) -> None:
    size = state.get("size", "")
    contract_path = state.get("contract_path", "")
    contract_stage = state.get("contract_stage", "")
    verification_path = state.get("verification_path", "")
    if phase in {"implement", "review", "verify", "deliver"} and size in {"M", "L", "XL"}:
        if not contract_path:
            raise ValueError(f"phase {phase} requires a contract for M/L/XL tasks")
        if not Path(contract_path).exists():
            raise ValueError(f"phase {phase} requires an existing contract file: {contract_path}")
        if size in {"L", "XL"} and contract_stage == "what":
            raise ValueError(f"phase {phase} requires a HOW or full contract for L/XL tasks")
    if phase == "deliver":
        if not verification_path:
            raise ValueError("phase deliver requires a verification report")
        if not Path(verification_path).exists():
            raise ValueError(f"phase deliver requires an existing verification report: {verification_path}")


def ensure_contract_exists(state: dict, *, command: str) -> None:
    size = state.get("size", "")
    contract_path = state.get("contract_path", "")
    contract_stage = state.get("contract_stage", "")
    if size in {"M", "L", "XL"} and not contract_path:
        raise ValueError(f"{command} requires a generated contract for M/L/XL tasks")
    if contract_path and not Path(contract_path).exists():
        raise ValueError(f"{command} requires an existing contract file: {contract_path}")
    if size in {"L", "XL"} and contract_stage == "what":
        raise ValueError(f"{command} requires a HOW or full contract for L/XL tasks")


def ensure_verification_complete(state: dict) -> None:
    size = state.get("size", "")
    summary = state.get("verification_summary", {})
    evidence = summary.get("evidence", []) if isinstance(summary, dict) else []
    verification_path = state.get("verification_path", "")
    if not verification_path:
        raise ValueError("handoff requires a verification report")
    if not Path(verification_path).exists():
        raise ValueError(f"handoff requires an existing verification report: {verification_path}")
    if size in {"L", "XL"} and not evidence:
        raise ValueError("handoff for L/XL tasks requires verification evidence")
    if size in {"L", "XL"}:
        ensure_required_reviews(state)


def ensure_required_reviews(state: dict) -> None:
    reviews = state.get("reviews", [])
    completed_statuses = {"DONE", "DONE_WITH_CONCERNS"}
    completed_kinds = {
        review.get("kind", "")
        for review in reviews
        if isinstance(review, dict) and review.get("status", "") in completed_statuses
    }
    missing = [kind for kind in ("spec", "quality") if kind not in completed_kinds]
    if missing:
        raise ValueError(
            "handoff for L/XL tasks requires completed reviews for: " + ", ".join(missing)
        )


def invalidate_downstream_artifacts_if_contract_changed(
    state: dict,
    *,
    previous_contract: tuple[str, str],
    current_contract: tuple[str, str],
    empty_verification_summary: dict,
) -> None:
    if previous_contract == current_contract:
        return
    state["verification_path"] = ""
    state["handoff_path"] = ""
    state["reviews"] = []
    state["verification_summary"] = empty_verification_summary


def invalidate_handoff_if_upstream_changed(state: dict) -> None:
    state["handoff_path"] = ""
