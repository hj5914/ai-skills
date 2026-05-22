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
from core.memory import render_memory_entry
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


def cmd_init(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = default_state()
    state["objective"] = args.objective or ""
    save_state(state_path, state)
    print(f"initialized {state_path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    state["size"] = args.size
    state["risk"] = args.risk
    state["surfaces"] = args.surface or []
    set_phase(state, "classify")
    save_state(state_path, state)
    print(
        json.dumps(
            {"size": args.size, "risk": args.risk, "surfaces": state["surfaces"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_contract(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    contract = render_contract(
        objective=state.get("objective", ""),
        size=state.get("size", "M"),
        risk=state.get("risk", "medium"),
        mode=args.mode,
    )
    contract_path = args.output or Path.cwd() / "bdo.contract.md"
    _write_text(contract_path, contract)
    state["contract_path"] = str(contract_path)
    set_phase(state, "contract")
    save_state(state_path, state)
    print(f"wrote {contract_path}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    state["verification_summary"] = build_verification_summary(state)
    report = render_verify(state)
    report_path = args.output or Path.cwd() / "bdo.verify.md"
    _write_text(report_path, report)
    state["verification_path"] = str(report_path)
    set_phase(state, "verify")
    save_state(state_path, state)
    print(f"wrote {report_path}")
    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    handoff = render_handoff(state)
    handoff_path = args.output or Path.cwd() / "bdo.handoff.md"
    _write_text(handoff_path, handoff)
    state["handoff_path"] = str(handoff_path)
    set_phase(state, "deliver")
    save_state(state_path, state)
    print(f"wrote {handoff_path}")
    return 0


def cmd_memory(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    entry = render_memory_entry(state)
    memory_path = args.output or Path.cwd() / "MEMORY.md"
    previous = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    combined = previous.rstrip() + ("\n\n" if previous.strip() else "") + entry.strip() + "\n"
    _write_text(memory_path, combined)
    set_phase(state, "memory")
    save_state(state_path, state)
    print(f"updated {memory_path}")
    return 0


def cmd_delta(args: argparse.Namespace) -> int:
    state_path = args.state or Path.cwd() / STATE_FILE_NAME
    state = load_state(state_path)
    delta = {
        "added": args.added or [],
        "removed": args.removed or [],
        "changed": args.changed or [],
        "impact": args.impact or "",
    }
    state.setdefault("delta", []).append(delta)
    save_state(state_path, state)
    print(json.dumps(delta, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bdo")
    parser.add_argument("--state", type=Path, help="Path to the bdo state file")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--objective", help="Initial objective")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("classify")
    p.add_argument("--size", default="M", choices=["XS", "S", "M", "L", "XL"])
    p.add_argument("--risk", default="medium")
    p.add_argument(
        "--surface",
        action="append",
        choices=["copy", "config", "ui", "backend", "api", "utility", "data", "auth", "external", "performance"],
        help="Changed surface; repeat for multiple values",
    )
    p.set_defaults(func=cmd_classify)

    p = sub.add_parser("contract")
    p.add_argument("--mode", choices=["lightweight", "full"], default="lightweight")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_contract)

    p = sub.add_parser("verify")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("handoff")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("memory")
    p.add_argument("--output", type=Path)
    p.set_defaults(func=cmd_memory)

    p = sub.add_parser("delta")
    p.add_argument("--added", action="append")
    p.add_argument("--removed", action="append")
    p.add_argument("--changed", action="append")
    p.add_argument("--impact")
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


if __name__ == "__main__":
    raise SystemExit(main())
