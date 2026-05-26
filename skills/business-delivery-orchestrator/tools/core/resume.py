from __future__ import annotations

from pathlib import Path


def build_resume_summary(state: dict) -> dict:
    phase = str(state.get("phase", "init"))
    size = str(state.get("size", "M"))
    contract_path = str(state.get("contract_path", ""))
    contract_stage = str(state.get("contract_stage", ""))
    verification_path = str(state.get("verification_path", ""))
    handoff_path = str(state.get("handoff_path", ""))
    reviews = state.get("reviews", [])

    contract_exists = bool(contract_path) and Path(contract_path).exists()
    verification_exists = bool(verification_path) and Path(verification_path).exists()
    handoff_exists = bool(handoff_path) and Path(handoff_path).exists()
    completed_review_kinds = sorted(
        {
            review.get("kind", "")
            for review in reviews
            if isinstance(review, dict) and review.get("status", "") in {"DONE", "DONE_WITH_CONCERNS"}
        }
    )
    blocked_recovery = build_blocked_recovery(state)

    blockers: list[str] = []
    if contract_path and not contract_exists:
        blockers.append(f"Missing contract artifact: {contract_path}")
    if verification_path and not verification_exists:
        blockers.append(f"Missing verification artifact: {verification_path}")
    if handoff_path and not handoff_exists:
        blockers.append(f"Missing handoff artifact: {handoff_path}")
    if phase in {"verify", "deliver"} and not contract_path and size in {"M", "L", "XL"}:
        blockers.append("Phase/state mismatch: verification or delivery is recorded without a contract.")
    if phase == "deliver" and not handoff_path and size in {"L", "XL"}:
        blockers.append("Phase/state mismatch: L/XL delivery is recorded without a handoff artifact.")
    if size in {"L", "XL"} and contract_stage == "what":
        blockers.append("L/XL work is paused at WHAT; generate HOW or full contract before verification.")
    if size in {"L", "XL"} and verification_exists and {"spec", "quality"} - set(completed_review_kinds):
        missing = ", ".join(sorted({"spec", "quality"} - set(completed_review_kinds)))
        blockers.append(f"Missing completed L/XL reviews: {missing}.")
    if blocked_recovery:
        blockers.append(blocked_recovery["blocker"])

    next_step = "Review status and continue from the current phase."
    suggested_command = ""
    if not state.get("objective"):
        next_step = "Initialize the workflow objective before resuming delivery."
        suggested_command = 'init --objective "..."'
    elif phase in {"verify", "deliver"} and not contract_path and size in {"M", "L", "XL"}:
        next_step = "Regenerate the required contract before trusting verify or delivery state."
        suggested_command = "contract --mode full" if size in {"L", "XL"} else "contract --mode lightweight"
    elif phase in {"init", "classify"} and size in {"M", "L", "XL"} and not contract_path:
        next_step = "Generate the delivery contract before implementation or verification."
        suggested_command = "contract --mode full" if size in {"L", "XL"} else "contract --mode lightweight"
    elif size in {"L", "XL"} and contract_stage == "what":
        next_step = "Complete the HOW pass before verification."
        suggested_command = "contract-how"
    elif contract_path and not contract_exists:
        next_step = "Regenerate the missing contract artifact before proceeding."
        suggested_command = (
            "contract-how"
            if contract_stage == "what"
            else "contract --mode full"
            if size in {"L", "XL"}
            else "contract --mode lightweight"
        )
    elif phase in {"contract", "implement", "review"} and not verification_path:
        next_step = "Run verification and record evidence before handoff."
        suggested_command = 'verify --evidence "..."'
    elif verification_path and not verification_exists:
        next_step = "Regenerate the missing verification report before handoff."
        suggested_command = 'verify --evidence "..."'
    elif size in {"L", "XL"} and {"spec", "quality"} - set(completed_review_kinds):
        missing = ", ".join(sorted({"spec", "quality"} - set(completed_review_kinds)))
        next_step = f"Record the missing completed reviews before handoff: {missing}."
        suggested_command = "review --kind spec|quality --status DONE"
    elif blocked_recovery:
        next_step = blocked_recovery["next_step"]
        suggested_command = blocked_recovery["suggested_command"]
    elif phase == "deliver" and not handoff_path and size in {"L", "XL"}:
        next_step = "Generate the missing handoff artifact before treating delivery as complete."
        suggested_command = "handoff"
    elif not handoff_path and size in {"L", "XL"}:
        next_step = "Generate the handoff artifact to complete delivery."
        suggested_command = "handoff"
    elif not handoff_path:
        next_step = "Handoff artifact is optional for this size; continue with a concise evidence-oriented final report unless the workflow needs a durable artifact."
        suggested_command = ""
    elif handoff_path and not handoff_exists:
        next_step = "Regenerate the missing handoff artifact."
        suggested_command = "handoff"
    elif phase == "deliver" and handoff_exists:
        next_step = "Delivery artifacts are present; review residual risks or close the task."

    artifact_review_order = [
        ("contract", contract_path, contract_exists),
        ("verification", verification_path, verification_exists),
        ("handoff", handoff_path, handoff_exists),
    ]
    artifacts_to_review = [path for _label, path, exists in artifact_review_order if path and exists]
    workflow_status = "blocked" if blockers else "ready"
    if blockers:
        takeover_hint = "Inspect the latest existing artifact, resolve the blocker, then run the suggested command."
    elif phase in {"verify", "deliver"}:
        takeover_hint = "Inspect the latest verification or handoff artifact, then continue from the suggested command."
    elif contract_exists:
        takeover_hint = "Inspect the current contract artifact before continuing implementation."
    else:
        takeover_hint = "No artifact context exists yet; start from the suggested command."
    artifact_phrase = ", ".join(Path(path).name for path in artifacts_to_review) if artifacts_to_review else "no existing artifacts"
    if blockers:
        recovery_summary = (
            f"Resume blocked {size} task at phase `{phase}`. Review {artifact_phrase}, clear blockers, then run `{suggested_command or 'the next required command'}`."
        )
    else:
        recovery_summary = (
            f"Resume {size} task at phase `{phase}`. Review {artifact_phrase}, then continue with `{suggested_command or 'the next workflow step'}`."
        )

    return {
        "objective": state.get("objective", ""),
        "phase": phase,
        "size": size,
        "risk": state.get("risk", ""),
        "workflow_status": workflow_status,
        "surfaces": state.get("surfaces", []),
        "contract_stage": contract_stage,
        "artifacts": {
            "contract_path": contract_path,
            "contract_exists": contract_exists,
            "verification_path": verification_path,
            "verification_exists": verification_exists,
            "handoff_path": handoff_path,
            "handoff_exists": handoff_exists,
        },
        "artifacts_to_review": artifacts_to_review,
        "completed_reviews": completed_review_kinds,
        "blocked_recovery": blocked_recovery,
        "blockers": blockers,
        "takeover_hint": takeover_hint,
        "recovery_summary": recovery_summary,
        "next_step": next_step,
        "suggested_command": suggested_command,
    }


def build_blocked_recovery(state: dict) -> dict | None:
    reviews = state.get("reviews", [])
    blocked_review = next(
        (
            review
            for review in reversed(reviews)
            if isinstance(review, dict) and review.get("status", "") in {"NEEDS_CONTEXT", "BLOCKED"}
        ),
        None,
    )
    if not blocked_review:
        return None

    status = blocked_review.get("status", "")
    kind = blocked_review.get("kind", "review")
    focus = blocked_review.get("focus", "")
    findings = blocked_review.get("findings", [])
    decision_text = " ".join([focus, *findings]).lower()
    size = str(state.get("size", "M"))

    if status == "NEEDS_CONTEXT" or any(
        token in decision_text for token in ("context", "missing", "unknown", "credential", "access")
    ):
        return {
            "mode": "provide_context",
            "review_kind": kind,
            "status": status,
            "blocker": f"Blocked {kind} review needs more context before it can proceed.",
            "next_step": "Provide the missing context or assumptions, then rerun the blocked review.",
            "suggested_command": 'quiz --assumption "..."',
        }

    if any(token in decision_text for token in ("plan", "contract", "scope")):
        return {
            "mode": "escalate_plan",
            "review_kind": kind,
            "status": status,
            "blocker": f"Blocked {kind} review points to a contract or plan problem.",
            "next_step": "Update the contract or plan before rerunning the blocked review.",
            "suggested_command": (
                "contract-how"
                if state.get("contract_stage", "") == "what"
                else 'delta --summary "plan adjustment for blocked review"'
            ),
        }

    if any(token in decision_text for token in ("split", "too large", "too broad")) or size in {"L", "XL"}:
        return {
            "mode": "split_task",
            "review_kind": kind,
            "status": status,
            "blocker": f"Blocked {kind} review suggests the work should be split into smaller slices.",
            "next_step": "Split the blocked slice or reduce its scope before rerunning the review.",
            "suggested_command": 'delta --summary "split blocked work into smaller slices"',
        }

    return {
        "mode": "collapse_to_single_agent",
        "review_kind": kind,
        "status": status,
        "blocker": f"Blocked {kind} review is not worth another delegated pass at the current task size.",
        "next_step": "Stop delegating this slice and finish it in the primary agent context.",
        "suggested_command": "phase implement",
    }
