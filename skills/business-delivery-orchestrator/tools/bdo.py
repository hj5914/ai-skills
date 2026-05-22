#!/usr/bin/env python3
"""BDO CLI: lightweight delivery workflow helper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
THIS_MODULE = sys.modules.pop("bdo", None)
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from core.handoff import render_handoff
from core.contract import render_contract
from core.memory import parse_memory_entry, render_memory_entry
from core.quiz import build_clarify_quiz, clarify_warning
from core.scan import mine_constraints, run_impact_scan
from core.state import (
    STATE_FILE_NAME,
    default_state,
    load_state,
    save_state,
    set_phase,
)
from core.verify import build_verification_summary, render_verify


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _emit(args: argparse.Namespace, *, command: str, state_path: Path | None = None, output_path: Path | None = None, data: dict | list | None = None) -> int:
    if args.json:
        payload = {
            "ok": True,
            "command": command,
            "state_path": str(state_path) if state_path else None,
            "output_path": str(output_path) if output_path else None,
            "data": data,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if output_path:
            verb = "updated" if command == "memory" else "wrote"
            if command == "init":
                verb = "initialized"
            print(f"{verb} {output_path}")
        elif data is not None:
            if isinstance(data, (dict, list)):
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(data)
        warning = _extract_warning(data)
        if warning:
            print(f"warning: {warning}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = default_state()
    state["objective"] = args.objective or ""
    save_state(state_path, state)
    return _emit(
        args,
        command="init",
        state_path=state_path,
        output_path=state_path,
        data={"objective": state["objective"], "phase": state["phase"]},
    )


def cmd_status(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    return _emit(args, command="status", state_path=state_path, data=state)


def cmd_resume(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    return _emit(args, command="resume", state_path=state_path, data=build_resume_summary(state))


def cmd_classify(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    state["size"] = args.size
    state["risk"] = args.risk
    if args.clear_surfaces:
        state["surfaces"] = []
    elif args.surface:
        state["surfaces"] = args.surface
    set_phase(state, "classify")
    save_state(state_path, state)
    return _emit(
        args,
        command="classify",
        state_path=state_path,
        data={
            "size": args.size,
            "risk": args.risk,
            "surfaces": state["surfaces"],
            "warning": _clarify_warning(state),
        },
    )


def cmd_phase(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    set_phase(state, args.name)
    save_state(state_path, state)
    return _emit(args, command="phase", state_path=state_path, data={"phase": state["phase"]})


def cmd_quiz(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    quiz = build_clarify_quiz(
        objective=state.get("objective", ""),
        size=state.get("size", "M"),
        risk=state.get("risk", "medium"),
        surfaces=state.get("surfaces", []),
    )
    if args.assumption:
        quiz["resolved"] = args.assumption
    state["clarify_quiz"] = quiz
    save_state(state_path, state)
    return _emit(args, command="quiz", state_path=state_path, data=quiz)


def cmd_contract(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    _ensure_contract_allowed(state, args.mode)
    contract = render_contract(
        objective=state.get("objective", ""),
        size=state.get("size", "M"),
        risk=state.get("risk", "medium"),
        mode=args.mode,
        surfaces=state.get("surfaces", []),
        constraints_detected=state.get("constraints_detected", []),
        clarify_assumptions=_resolved_assumptions(state),
    )
    contract_path = args.output or Path.cwd() / "bdo.contract.md"
    previous_contract = (
        state.get("contract_path", ""),
        state.get("contract_stage", ""),
    )
    _write_text(contract_path, contract)
    state["contract_path"] = str(contract_path)
    state["contract_stage"] = args.mode
    _invalidate_downstream_artifacts_if_contract_changed(
        state,
        previous_contract=previous_contract,
        current_contract=(state["contract_path"], state["contract_stage"]),
    )
    set_phase(state, "contract")
    save_state(state_path, state)
    return _emit(
        args,
        command="contract",
        state_path=state_path,
        output_path=contract_path,
        data={
            "mode": args.mode,
            "size": state.get("size", ""),
            "risk": state.get("risk", ""),
            "surfaces": state.get("surfaces", []),
            "warning": _clarify_warning(state),
        },
    )


def cmd_contract_what(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    contract = render_contract(
        objective=state.get("objective", ""),
        size=state.get("size", "M"),
        risk=state.get("risk", "medium"),
        mode="what",
        surfaces=state.get("surfaces", []),
        constraints_detected=state.get("constraints_detected", []),
        clarify_assumptions=_resolved_assumptions(state),
    )
    contract_path = args.output or Path.cwd() / "bdo.contract.what.md"
    previous_contract = (
        state.get("contract_path", ""),
        state.get("contract_stage", ""),
    )
    _write_text(contract_path, contract)
    state["contract_path"] = str(contract_path)
    state["contract_stage"] = "what"
    _invalidate_downstream_artifacts_if_contract_changed(
        state,
        previous_contract=previous_contract,
        current_contract=(state["contract_path"], state["contract_stage"]),
    )
    set_phase(state, "contract")
    save_state(state_path, state)
    return _emit(
        args,
        command="contract-what",
        state_path=state_path,
        output_path=contract_path,
        data={
            "mode": "what",
            "size": state.get("size", ""),
            "risk": state.get("risk", ""),
            "surfaces": state.get("surfaces", []),
            "warning": _clarify_warning(state),
        },
    )


def cmd_contract_how(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    _ensure_contract_allowed(state, "full")
    contract = render_contract(
        objective=state.get("objective", ""),
        size=state.get("size", "M"),
        risk=state.get("risk", "medium"),
        mode="how",
        surfaces=state.get("surfaces", []),
        constraints_detected=state.get("constraints_detected", []),
        clarify_assumptions=_resolved_assumptions(state),
    )
    contract_path = args.output or Path.cwd() / "bdo.contract.how.md"
    previous_contract = (
        state.get("contract_path", ""),
        state.get("contract_stage", ""),
    )
    _write_text(contract_path, contract)
    state["contract_path"] = str(contract_path)
    state["contract_stage"] = "how"
    _invalidate_downstream_artifacts_if_contract_changed(
        state,
        previous_contract=previous_contract,
        current_contract=(state["contract_path"], state["contract_stage"]),
    )
    set_phase(state, "contract")
    save_state(state_path, state)
    return _emit(
        args,
        command="contract-how",
        state_path=state_path,
        output_path=contract_path,
        data={
            "mode": "how",
            "size": state.get("size", ""),
            "risk": state.get("risk", ""),
            "surfaces": state.get("surfaces", []),
            "warning": _clarify_warning(state),
        },
    )


def cmd_verify(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    _ensure_contract_exists(state, command="verify")
    state["verification_summary"] = build_verification_summary(
        state,
        evidence=args.evidence or [],
        gaps=args.gap or [],
    )
    set_phase(state, "verify")
    report = render_verify(state)
    report_path = args.output or Path.cwd() / "bdo.verify.md"
    _write_text(report_path, report)
    state["verification_path"] = str(report_path)
    _invalidate_handoff_if_upstream_changed(state)
    save_state(state_path, state)
    return _emit(
        args,
        command="verify",
        state_path=state_path,
        output_path=report_path,
        data=state["verification_summary"],
    )


def cmd_handoff(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    _ensure_contract_exists(state, command="handoff")
    _ensure_verification_complete(state)
    handoff = render_handoff(state)
    handoff_path = args.output or Path.cwd() / "bdo.handoff.md"
    _write_text(handoff_path, handoff)
    state["handoff_path"] = str(handoff_path)
    set_phase(state, "deliver")
    save_state(state_path, state)
    return _emit(
        args,
        command="handoff",
        state_path=state_path,
        output_path=handoff_path,
        data={
            "verification_summary": state.get("verification_summary", {}),
            "latest_delta": state.get("delta", [])[-1] if state.get("delta") else None,
            "latest_delta_summary": state.get("delta", [])[-1].get("summary", "") if state.get("delta") else "",
            "verification_evidence": state.get("verification_summary", {}).get("evidence", []),
            "verification_gaps": state.get("verification_summary", {}).get("gaps", []),
        },
    )


def cmd_memory(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    entry = render_memory_entry(
        state,
        context=args.context,
        lesson=args.lesson,
        rule=args.rule,
        evidence=args.evidence,
    )
    memory_path = args.output or Path.cwd() / "MEMORY.md"
    previous = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    combined = previous.rstrip() + ("\n\n" if previous.strip() else "") + entry.strip() + "\n"
    _write_text(memory_path, combined)
    state.setdefault("memory", []).append(entry.strip())
    set_phase(state, "memory")
    save_state(state_path, state)
    return _emit(
        args,
        command="memory",
        state_path=state_path,
        output_path=memory_path,
        data=parse_memory_entry(entry),
    )


def cmd_review(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    review = {
        "kind": args.kind,
        "status": args.status,
        "focus": args.focus or "",
        "findings": args.finding or [],
        "evidence": args.evidence or [],
    }
    state.setdefault("reviews", []).append(review)
    _invalidate_handoff_if_upstream_changed(state)
    set_phase(state, "review")
    save_state(state_path, state)
    return _emit(args, command="review", state_path=state_path, data=review)


def cmd_delta(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    summary = args.summary or _summarize_delta(args.added or [], args.removed or [], args.changed or [], args.impact or "")
    delta = {
        "added": args.added or [],
        "removed": args.removed or [],
        "changed": args.changed or [],
        "impact": args.impact or "",
        "summary": summary,
    }
    state.setdefault("delta", []).append(delta)
    _invalidate_handoff_if_upstream_changed(state)
    save_state(state_path, state)
    return _emit(args, command="delta", state_path=state_path, data=delta)


def cmd_scan(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    state["impact_scan"] = run_impact_scan(Path.cwd(), args.target or [])
    save_state(state_path, state)
    return _emit(args, command="scan", state_path=state_path, data=state["impact_scan"])


def cmd_mine(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    state["constraints_detected"] = mine_constraints(Path.cwd())
    save_state(state_path, state)
    return _emit(
        args,
        command="mine",
        state_path=state_path,
        data={"constraints_detected": state["constraints_detected"]},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bdo")
    parser.add_argument("--state", type=Path, help="Path to the bdo state file")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--objective", help="Initial objective")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("resume")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("classify")
    p.add_argument("--size", default="M", choices=["XS", "S", "M", "L", "XL"])
    p.add_argument("--risk", default="medium")
    p.add_argument(
        "--surface",
        action="append",
        choices=[
            "copy",
            "config",
            "ui",
            "backend",
            "api",
            "utility",
            "data",
            "auth",
            "payment",
            "migration",
            "external",
            "performance",
        ],
        help="Changed surface; repeat for multiple values",
    )
    p.add_argument(
        "--clear-surfaces",
        action="store_true",
        help="Clear previously recorded surfaces before saving this classification",
    )
    p.set_defaults(func=cmd_classify)

    p = sub.add_parser("phase")
    p.add_argument(
        "name",
        choices=["init", "classify", "plan", "contract", "implement", "review", "verify", "deliver", "memory"],
        help="Explicitly set the current workflow phase",
    )
    p.set_defaults(func=cmd_phase)

    p = sub.add_parser("quiz")
    p.add_argument("--assumption", action="append", help="Resolved assumption to carry into contracts")
    p.set_defaults(func=cmd_quiz)

    p = sub.add_parser("scan")
    p.add_argument("--target", action="append", help="Keyword, path, or module name to scan for impact")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("mine")
    p.set_defaults(func=cmd_mine)

    p = sub.add_parser("contract")
    p.add_argument("--mode", choices=["lightweight", "full"], default="lightweight")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_contract)

    p = sub.add_parser("contract-what")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_contract_what)

    p = sub.add_parser("contract-how")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_contract_how)

    p = sub.add_parser("verify")
    p.add_argument("--output", type=Path)
    p.add_argument("--evidence", action="append", help="Actual checks or commands that ran")
    p.add_argument("--gap", action="append", help="Known coverage gaps or skipped checks")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("handoff")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("memory")
    p.add_argument("--output", type=Path)
    p.add_argument("--context")
    p.add_argument("--lesson")
    p.add_argument("--rule")
    p.add_argument("--evidence")
    p.set_defaults(func=cmd_memory)

    p = sub.add_parser("review")
    p.add_argument("--kind", choices=["spec", "quality"], required=True)
    p.add_argument("--status", choices=["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"], required=True)
    p.add_argument("--focus", help="Review focus area")
    p.add_argument("--finding", action="append", help="Review finding")
    p.add_argument("--evidence", action="append", help="Evidence or command that informed the review")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("delta")
    p.add_argument("--added", action="append")
    p.add_argument("--removed", action="append")
    p.add_argument("--changed", action="append")
    p.add_argument("--impact")
    p.add_argument("--summary")
    p.set_defaults(func=cmd_delta)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _summarize_delta(added: list[str], removed: list[str], changed: list[str], impact: str) -> str:
    parts = []
    if changed:
        parts.append(f"changed {', '.join(changed[:2])}")
    if added:
        parts.append(f"added {', '.join(added[:2])}")
    if removed:
        parts.append(f"removed {', '.join(removed[:2])}")
    if impact:
        parts.append(impact)
    return "; ".join(parts) if parts else "No delta recorded"


def _ensure_contract_allowed(state: dict, mode: str) -> None:
    surfaces = set(state.get("surfaces", []))
    size = state.get("size", "")
    if surfaces & {"auth", "data", "payment", "migration"} and mode != "full":
        raise ValueError("auth/data/payment/migration tasks require `contract --mode full`")
    if size in {"L", "XL"} and mode != "full":
        raise ValueError("L/XL tasks require `contract --mode full`")


def _ensure_contract_exists(state: dict, *, command: str) -> None:
    size = state.get("size", "")
    contract_path = state.get("contract_path", "")
    contract_stage = state.get("contract_stage", "")
    if size in {"M", "L", "XL"} and not contract_path:
        raise ValueError(f"{command} requires a generated contract for M/L/XL tasks")
    if contract_path and not Path(contract_path).exists():
        raise ValueError(f"{command} requires an existing contract file: {contract_path}")
    if size in {"L", "XL"} and contract_stage == "what":
        raise ValueError(f"{command} requires a HOW or full contract for L/XL tasks")


def _ensure_verification_complete(state: dict) -> None:
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
        _ensure_required_reviews(state)


def _ensure_required_reviews(state: dict) -> None:
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


def _invalidate_downstream_artifacts_if_contract_changed(
    state: dict, *, previous_contract: tuple[str, str], current_contract: tuple[str, str]
) -> None:
    if previous_contract == current_contract:
        return
    state["verification_path"] = ""
    state["handoff_path"] = ""
    state["reviews"] = []
    state["verification_summary"] = default_state()["verification_summary"]


def _invalidate_handoff_if_upstream_changed(state: dict) -> None:
    state["handoff_path"] = ""


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
    blocked_recovery = _build_blocked_recovery(state)

    blockers: list[str] = []
    if contract_path and not contract_exists:
        blockers.append(f"Missing contract artifact: {contract_path}")
    if verification_path and not verification_exists:
        blockers.append(f"Missing verification artifact: {verification_path}")
    if handoff_path and not handoff_exists:
        blockers.append(f"Missing handoff artifact: {handoff_path}")
    if phase in {"verify", "deliver"} and not contract_path and size in {"M", "L", "XL"}:
        blockers.append("Phase/state mismatch: verification or delivery is recorded without a contract.")
    if phase == "deliver" and not handoff_path:
        blockers.append("Phase/state mismatch: delivery is recorded without a handoff artifact.")
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
        suggested_command = "init --objective \"...\""
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
        suggested_command = "contract-how" if contract_stage == "what" else "contract --mode full" if size in {"L", "XL"} else "contract --mode lightweight"
    elif phase in {"contract", "implement", "review"} and not verification_path:
        next_step = "Run verification and record evidence before handoff."
        suggested_command = "verify --evidence \"...\""
    elif verification_path and not verification_exists:
        next_step = "Regenerate the missing verification report before handoff."
        suggested_command = "verify --evidence \"...\""
    elif size in {"L", "XL"} and {"spec", "quality"} - set(completed_review_kinds):
        missing = ", ".join(sorted({"spec", "quality"} - set(completed_review_kinds)))
        next_step = f"Record the missing completed reviews before handoff: {missing}."
        suggested_command = "review --kind spec|quality --status DONE"
    elif blocked_recovery:
        next_step = blocked_recovery["next_step"]
        suggested_command = blocked_recovery["suggested_command"]
    elif phase == "deliver" and not handoff_path:
        next_step = "Generate the missing handoff artifact before treating delivery as complete."
        suggested_command = "handoff"
    elif not handoff_path:
        next_step = "Generate the handoff artifact to complete delivery."
        suggested_command = "handoff"
    elif handoff_path and not handoff_exists:
        next_step = "Regenerate the missing handoff artifact."
        suggested_command = "handoff"
    elif phase == "deliver" and handoff_exists:
        next_step = "Delivery artifacts are present; review residual risks or close the task."

    return {
        "objective": state.get("objective", ""),
        "phase": phase,
        "size": size,
        "risk": state.get("risk", ""),
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
        "completed_reviews": completed_review_kinds,
        "blocked_recovery": blocked_recovery,
        "blockers": blockers,
        "next_step": next_step,
        "suggested_command": suggested_command,
    }


def _build_blocked_recovery(state: dict) -> dict | None:
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
            "suggested_command": "contract-how" if state.get("contract_stage", "") == "what" else 'delta --summary "plan adjustment for blocked review"',
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


def _resolved_assumptions(state: dict) -> list[str]:
    quiz = state.get("clarify_quiz", {})
    if not isinstance(quiz, dict):
        return []
    resolved = quiz.get("resolved", [])
    assumptions = quiz.get("assumptions", [])
    result: list[str] = []
    if isinstance(resolved, list):
        result.extend([item for item in resolved if isinstance(item, str)])
    if not result and isinstance(assumptions, list):
        result.extend([item for item in assumptions if isinstance(item, str)])
    return result


def _clarify_warning(state: dict) -> str:
    return clarify_warning(
        size=str(state.get("size", "")),
        risk=str(state.get("risk", "")),
        surfaces=list(state.get("surfaces", [])),
        has_quiz=bool(state.get("clarify_quiz", {}).get("questions")),
    )


def _extract_warning(data: dict | list | None) -> str:
    if not isinstance(data, dict):
        return ""
    warning = data.get("warning", "")
    return warning if isinstance(warning, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())
