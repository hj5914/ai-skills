from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

STATE_FILE_NAME = ".bdo.state.json"
VALID_SIZES = {"XS", "S", "M", "L", "XL"}
VALID_PHASES = {"init", "classify", "plan", "contract", "implement", "review", "verify", "deliver", "memory"}
VALID_SURFACES = {
    "copy",
    "config",
    "ui",
    "backend",
    "api",
    "utility",
    "data",
    "auth",
    "external",
    "performance",
}


def default_state() -> dict:
    return {
        "objective": "",
        "size": "M",
        "risk": "medium",
        "phase": "init",
        "contract_path": "",
        "verification_path": "",
        "handoff_path": "",
        "surfaces": [],
        "verification_summary": {
            "checks": [],
            "escalation": [],
            "stop_conditions": [],
            "evidence": [],
            "gaps": [],
        },
        "reviews": [],
        "impact_scan": {
            "targets": [],
            "matched_files": [],
            "summary": "",
            "recommended_size": "",
            "notes": [],
        },
        "constraints_detected": [],
        "delta": [],
        "memory": [],
    }


def load_state(path: Path) -> dict:
    if not path.exists():
        return default_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"BDO state file is invalid JSON at {path}; rerun `init` or remove the corrupted file"
        ) from exc
    state = normalize_state(state)
    validate_state(state)
    return state


def save_state(path: Path, state: dict) -> None:
    validate_state(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def set_phase(state: dict, phase: str) -> dict:
    state["phase"] = phase
    return state


def normalize_state(state: dict) -> dict:
    if not isinstance(state, dict):
        return state

    merged = default_state()
    merged.update(state)

    summary = state.get("verification_summary", {})
    merged_summary = default_state()["verification_summary"]
    if isinstance(summary, dict):
        merged_summary.update(summary)
    merged["verification_summary"] = merged_summary

    normalized_reviews = []
    for item in state.get("reviews", []):
        if not isinstance(item, dict):
            normalized_reviews.append(item)
            continue
        normalized_reviews.append(
            {
                "kind": item.get("kind", ""),
                "status": item.get("status", ""),
                "focus": item.get("focus", ""),
                "findings": item.get("findings", []),
                "evidence": item.get("evidence", []),
            }
        )
    merged["reviews"] = normalized_reviews

    normalized_delta = []
    for item in state.get("delta", []):
        if not isinstance(item, dict):
            normalized_delta.append(item)
            continue
        normalized_item = {
            "added": item.get("added", []),
            "removed": item.get("removed", []),
            "changed": item.get("changed", []),
            "impact": item.get("impact", ""),
            "summary": item.get("summary", ""),
        }
        normalized_delta.append(normalized_item)
    merged["delta"] = normalized_delta

    scan = state.get("impact_scan", {})
    merged_scan = default_state()["impact_scan"]
    if isinstance(scan, dict):
        merged_scan.update(scan)
    merged["impact_scan"] = merged_scan
    return merged


def validate_state(state: dict) -> None:
    if not isinstance(state, dict):
        raise ValueError("BDO state must be a JSON object")

    required = {
        "objective": str,
        "size": str,
        "risk": str,
        "phase": str,
        "contract_path": str,
        "verification_path": str,
        "handoff_path": str,
        "surfaces": list,
        "verification_summary": dict,
        "reviews": list,
        "impact_scan": dict,
        "constraints_detected": list,
        "delta": list,
        "memory": list,
    }

    extra_keys = set(state.keys()) - set(required.keys())
    missing_keys = set(required.keys()) - set(state.keys())
    if missing_keys:
        raise ValueError(f"BDO state missing keys: {sorted(missing_keys)}")
    if extra_keys:
        raise ValueError(f"BDO state has unexpected keys: {sorted(extra_keys)}")

    for key, expected_type in required.items():
        if not isinstance(state[key], expected_type):
            raise ValueError(f"BDO state key '{key}' must be {expected_type.__name__}")

    if state["size"] not in VALID_SIZES:
        raise ValueError(f"BDO state size must be one of {sorted(VALID_SIZES)}")
    if state["phase"] not in VALID_PHASES:
        raise ValueError(f"BDO state phase must be one of {sorted(VALID_PHASES)}")
    if not all(isinstance(v, str) for v in state["surfaces"]):
        raise ValueError("BDO state surfaces must be a list of strings")
    invalid_surfaces = sorted(set(state["surfaces"]) - VALID_SURFACES)
    if invalid_surfaces:
        raise ValueError(f"BDO state surfaces contain invalid values: {invalid_surfaces}")
    summary = state["verification_summary"]
    if set(summary.keys()) != {"checks", "escalation", "stop_conditions", "evidence", "gaps"}:
        raise ValueError(
            "BDO state verification_summary must contain checks, escalation, stop_conditions, evidence, gaps"
        )
    for key in ("checks", "escalation", "stop_conditions", "evidence", "gaps"):
        if not isinstance(summary[key], list) or not all(isinstance(v, str) for v in summary[key]):
            raise ValueError(f"BDO state verification_summary.{key} must be a list of strings")

    for idx, item in enumerate(state["reviews"]):
        if not isinstance(item, dict):
            raise ValueError(f"BDO state reviews[{idx}] must be an object")
        for key in ("kind", "status", "focus"):
            if key not in item or not isinstance(item[key], str):
                raise ValueError(f"BDO state reviews[{idx}].{key} must be a string")
        for key in ("findings", "evidence"):
            if key not in item or not isinstance(item[key], list) or not all(isinstance(v, str) for v in item[key]):
                raise ValueError(f"BDO state reviews[{idx}].{key} must be a list of strings")

    scan = state["impact_scan"]
    if set(scan.keys()) != {"targets", "matched_files", "summary", "recommended_size", "notes"}:
        raise ValueError(
            "BDO state impact_scan must contain targets, matched_files, summary, recommended_size, notes"
        )
    for key in ("targets", "matched_files", "notes"):
        if not isinstance(scan[key], list) or not all(isinstance(v, str) for v in scan[key]):
            raise ValueError(f"BDO state impact_scan.{key} must be a list of strings")
    for key in ("summary", "recommended_size"):
        if not isinstance(scan[key], str):
            raise ValueError(f"BDO state impact_scan.{key} must be a string")
    if scan["recommended_size"] and scan["recommended_size"] not in VALID_SIZES:
        raise ValueError(f"BDO state impact_scan.recommended_size must be one of {sorted(VALID_SIZES)}")

    if not all(isinstance(v, str) for v in state["constraints_detected"]):
        raise ValueError("BDO state constraints_detected must be a list of strings")

    for idx, item in enumerate(state["delta"]):
        if not isinstance(item, dict):
            raise ValueError(f"BDO state delta[{idx}] must be an object")
        for key in ("added", "removed", "changed"):
            if key not in item or not isinstance(item[key], list) or not all(
                isinstance(v, str) for v in item[key]
            ):
                raise ValueError(f"BDO state delta[{idx}].{key} must be a list of strings")
        if "impact" not in item or not isinstance(item["impact"], str):
            raise ValueError(f"BDO state delta[{idx}].impact must be a string")
        if "summary" not in item or not isinstance(item["summary"], str):
            raise ValueError(f"BDO state delta[{idx}].summary must be a string")

    if not all(isinstance(v, str) for v in state["memory"]):
        raise ValueError("BDO state memory must be a list of strings")
