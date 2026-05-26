from __future__ import annotations

from datetime import date
import re

from core.templates import fill_once, load_template_code_block


def render_memory_entry(
    state: dict,
    *,
    context: str | None = None,
    lesson: str | None = None,
    rule: str | None = None,
    evidence: str | None = None,
) -> str:
    objective = state.get("objective", "") or "delivery"
    latest_delta = state.get("delta", [])[-1] if state.get("delta") else {}
    verification = state.get("verification_summary", {})
    summary = latest_delta.get("summary") or _summarize_delta(latest_delta) or objective
    context_text = context or f"{objective} | {summary}"
    lesson_text = lesson or _default_lesson(state, latest_delta, verification)
    rule_text = rule or _default_rule(state, latest_delta, verification)
    evidence_text = evidence or _default_evidence(state, verification)
    template = load_template_code_block("memory-entry-template.md")
    template = fill_once(
        template,
        "## YYYY-MM-DD - <feature-or-incident-name>",
        f"## {date.today().isoformat()} - {objective}",
    )
    template = fill_once(template, "- Context:", f"- Context: {context_text}")
    template = fill_once(template, "- Lesson:", f"- Lesson: {lesson_text}")
    template = fill_once(template, "- Actionable rule for future work:", f"- Actionable rule for future work: {rule_text}")
    template = fill_once(template, "- Evidence:", f"- Evidence: {evidence_text}")
    return template


def parse_memory_entry(entry: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in entry.splitlines():
        if line.startswith("- Context:"):
            result["context"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Lesson:"):
            result["lesson"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Actionable rule for future work:"):
            result["rule"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Evidence:"):
            result["evidence"] = line.split(":", 1)[1].strip()
    if entry.strip():
        result.setdefault("title", entry.splitlines()[0].lstrip("# ").strip())
    return result


def split_memory_entries(document: str) -> list[str]:
    text = document.strip()
    if not text:
        return []
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    return [part.strip() for part in parts if part.strip()]


def dedupe_memory_entries(entries: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        signature = memory_entry_signature(entry)
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(entry.strip())
    return deduped


def memory_entry_signature(entry: str) -> str:
    parsed = parse_memory_entry(entry)
    lesson = _normalize_signature_field(parsed.get("lesson", ""))
    rule = _normalize_signature_field(parsed.get("rule", ""))
    if lesson or rule:
        return "|".join(part for part in (lesson, rule) if part)
    context = _normalize_signature_field(parsed.get("context", ""))
    return context or _normalize_signature_field(entry)


def _normalize_signature_field(value: str) -> str:
    return " ".join(value.lower().split())


def _summarize_delta(delta: dict) -> str:
    if not isinstance(delta, dict):
        return ""
    parts = []
    if delta.get("changed"):
        parts.append("changed " + ", ".join(delta["changed"][:2]))
    if delta.get("added"):
        parts.append("added " + ", ".join(delta["added"][:2]))
    if delta.get("removed"):
        parts.append("removed " + ", ".join(delta["removed"][:2]))
    if delta.get("impact"):
        parts.append(delta["impact"])
    return "; ".join(parts)


def _default_lesson(state: dict, delta: dict, verification: dict) -> str:
    gaps = verification.get("gaps", []) if isinstance(verification, dict) else []
    if gaps:
        return gaps[0]
    surfaces = state.get("surfaces", [])
    if "auth" in surfaces:
        return "Permission edges need explicit positive and negative coverage."
    if "data" in surfaces:
        return "Data changes need rollback and compatibility checks before delivery."
    if "ui" in surfaces:
        return "UI changes need loading, empty, and error states treated as first-class cases."
    summary = _summarize_delta(delta)
    return summary or "Capture one reusable pitfall from the delivery."


def _default_rule(state: dict, delta: dict, verification: dict) -> str:
    surfaces = set(state.get("surfaces", []))
    if "auth" in surfaces:
        return "Always verify allow and deny paths together."
    if "data" in surfaces:
        return "Always pair the change with a rollback or dry-run check."
    if "performance" in surfaces:
        return "Always add a complexity or benchmark note before merging."
    evidence = verification.get("evidence", []) if isinstance(verification, dict) else []
    if evidence:
        return "Record the exact command or manual evidence that proves the change."
    return "Apply the same guardrail next time."


def _default_evidence(state: dict, verification: dict) -> str:
    evidence = verification.get("evidence", []) if isinstance(verification, dict) else []
    if evidence:
        return "; ".join(evidence[:2])
    handoff_path = state.get("handoff_path", "")
    if handoff_path:
        return handoff_path
    return "Add concrete verification evidence here."
