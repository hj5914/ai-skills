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
from core.gates import ensure_contract_allowed as _ensure_contract_allowed
from core.gates import ensure_contract_exists as _ensure_contract_exists
from core.gates import ensure_phase_transition_allowed as _ensure_phase_transition_allowed
from core.gates import ensure_verification_complete as _ensure_verification_complete
from core.gates import invalidate_downstream_artifacts_if_contract_changed as _invalidate_downstream_artifacts_if_contract_changed_core
from core.gates import invalidate_handoff_if_upstream_changed as _invalidate_handoff_if_upstream_changed
from core.memory import dedupe_memory_entries, parse_memory_entry, render_memory_entry, split_memory_entries
from core.quiz import build_clarify_quiz, clarify_warning
from core.resume import build_blocked_recovery as _build_blocked_recovery
from core.resume import build_resume_summary
from core.scan import mine_constraints, run_impact_scan
from core.state import (
    STATE_FILE_NAME,
    default_state,
    load_state,
    save_state,
    set_phase,
)
from core.verify import build_verification_summary, render_verify, verify_recipe_choices


def _invalidate_downstream_artifacts_if_contract_changed(
    state: dict, *, previous_contract: tuple[str, str], current_contract: tuple[str, str]
) -> None:
    _invalidate_downstream_artifacts_if_contract_changed_core(
        state,
        previous_contract=previous_contract,
        current_contract=current_contract,
        empty_verification_summary=default_state()["verification_summary"],
    )


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
    _ensure_phase_transition_allowed(state, args.name)
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
    runtime_evidence = args.runtime_evidence or []
    recipes = args.recipe or []
    state["verification_summary"] = build_verification_summary(
        state,
        evidence=args.evidence or [],
        runtime_evidence=runtime_evidence,
        gaps=args.gap or [],
        recipes=recipes,
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
        data={
            **state["verification_summary"],
            "recipes": recipes,
            "warning": _verify_warning(state, runtime_evidence=runtime_evidence),
        },
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
            "verification_runtime_evidence": state.get("verification_summary", {}).get("runtime_evidence", []),
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
    existing_entries = split_memory_entries(previous)
    merged_entries = dedupe_memory_entries(existing_entries + [entry.strip()])
    appended = len(merged_entries) > len(existing_entries)
    combined = ("\n\n".join(merged_entries) + "\n") if merged_entries else ""
    _write_text(memory_path, combined)
    state["memory"] = dedupe_memory_entries(state.get("memory", []) + [entry.strip()])
    set_phase(state, "memory")
    save_state(state_path, state)
    parsed = parse_memory_entry(entry)
    return _emit(
        args,
        command="memory",
        state_path=state_path,
        output_path=memory_path,
        data={
            **parsed,
            "appended": appended,
            "entry_count": len(merged_entries),
        },
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
        "follow_ups": args.follow_up or [],
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
    p.add_argument(
        "--recipe",
        action="append",
        choices=verify_recipe_choices(),
        help="Verification checklist template to apply; recipes add guidance only and do not execute tools",
    )
    p.add_argument(
        "--runtime-evidence",
        action="append",
        help="Actual runtime or end-to-end checks that ran, such as service startup, requests, or UI flows",
    )
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
    p.add_argument("--follow-up", action="append", help="Scope-external finding or deferred follow-up item")
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


def _verify_warning(state: dict, *, runtime_evidence: list[str]) -> str:
    surfaces = set(state.get("surfaces", []))
    if "config" in surfaces and surfaces & {"backend", "api", "auth"} and not runtime_evidence:
        return (
            "Config changes affecting backend/api/auth were verified without runtime evidence. "
            "Do not treat verification as runtime-safe until startup or health-path behavior is checked."
        )
    return ""


def _extract_warning(data: dict | list | None) -> str:
    if not isinstance(data, dict):
        return ""
    warning = data.get("warning", "")
    return warning if isinstance(warning, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())
