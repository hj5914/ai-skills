from __future__ import annotations

from core.memory import parse_memory_entry
from core.templates import list_block, load_template_code_block, replace_section_placeholder


def _delta_summary(delta: dict) -> str:
    parts = []
    changed = delta.get("changed", [])[:3]
    added = delta.get("added", [])[:3]
    removed = delta.get("removed", [])[:3]
    if changed:
        parts.append("Changed: " + ", ".join(changed))
    if added:
        parts.append("Added: " + ", ".join(added))
    if removed:
        parts.append("Removed: " + ", ".join(removed))
    impact = delta.get("impact", "")
    if impact:
        parts.append(f"Impact: {impact}")
    summary = delta.get("summary", "")
    if summary:
        parts.insert(0, summary)
    return " | ".join(parts)


def render_handoff(state: dict) -> str:
    template = load_template_code_block("handoff-template.md")
    summary = state.get("verification_summary", {})
    checks = summary.get("checks", [])
    evidence = summary.get("evidence", [])
    gaps = summary.get("gaps", [])
    escalation = summary.get("escalation", [])
    latest_delta = state.get("delta", [])[-1] if state.get("delta") else None
    memory = state.get("memory", [])
    reviews = state.get("reviews", [])

    changed = []
    if latest_delta:
        summary_text = _delta_summary(latest_delta)
        if summary_text:
            changed.append(summary_text)
        else:
            changed.extend([f"Changed: {item}" for item in latest_delta.get("changed", [])[:3]])
            changed.extend([f"Added: {item}" for item in latest_delta.get("added", [])[:3]])
            changed.extend([f"Removed: {item}" for item in latest_delta.get("removed", [])[:3]])
            if latest_delta.get("impact"):
                changed.append(f"Impact: {latest_delta['impact']}")
    if not changed:
        changed = ["No delta recorded."]

    parsed_memory = [parse_memory_entry(entry) for entry in memory[-2:]] if memory else []
    lessons = []
    for parsed in parsed_memory:
        lesson = parsed.get("lesson") or parsed.get("title")
        if lesson:
            lessons.append(lesson)
    if not lessons:
        lessons = ["Capture one reusable lesson in MEMORY.md."]

    risks = [f"size={state.get('size', '')}", f"risk={state.get('risk', '')}"]
    next_steps = escalation[:2] if escalation else ["Review residual risks and close the task"]
    review_notes = []
    for review in reviews[-2:]:
        if not isinstance(review, dict):
            continue
        kind = review.get("kind", "review")
        status = review.get("status", "")
        focus = review.get("focus", "")
        findings = review.get("findings", [])
        note = " | ".join(part for part in [kind, status, focus] if part)
        if findings:
            note = f"{note}: {'; '.join(findings[:2])}" if note else "; ".join(findings[:2])
        if note:
            review_notes.append(note)
    verified_entries = []
    verified_entries.extend(checks[:4])
    verified_entries.extend(evidence[:4])
    verified_entries.extend(review_notes[:4])

    if changed:
        template = replace_section_placeholder(template, "Changed:", list_block(changed))
    if verified_entries:
        template = replace_section_placeholder(template, "Verified:", list_block(verified_entries))
    not_verified = gaps[:2] if gaps else ["No explicit gaps recorded"]
    template = replace_section_placeholder(template, "Not verified:", list_block(not_verified))
    template = replace_section_placeholder(template, "Lessons Learned (Update MEMORY.md):", list_block(lessons))
    template = replace_section_placeholder(template, "Risks:", list_block(risks))
    if next_steps:
        template = replace_section_placeholder(template, "Next:", list_block(next_steps))
    return template
