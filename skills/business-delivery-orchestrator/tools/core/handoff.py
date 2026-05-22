from __future__ import annotations

from core.templates import fill_once, list_block, load_template_code_block, replace_section_placeholder

def render_handoff(state: dict) -> str:
    template = load_template_code_block("handoff-template.md")
    summary = state.get("verification_summary", {})
    checks = summary.get("checks", [])
    escalation = summary.get("escalation", [])
    latest_delta = state.get("delta", [])[-1] if state.get("delta") else None
    memory = state.get("memory", [])

    changed = []
    if latest_delta:
        changed.extend([f"Changed: {item}" for item in latest_delta.get("changed", [])])
        changed.extend([f"Added: {item}" for item in latest_delta.get("added", [])])
        changed.extend([f"Removed: {item}" for item in latest_delta.get("removed", [])])
        if latest_delta.get("impact"):
            changed.append(f"Impact: {latest_delta['impact']}")
    if not changed:
        changed = ["No delta recorded."]

    lessons = [entry.splitlines()[0] for entry in memory[-2:]] if memory else ["Capture one reusable lesson in MEMORY.md."]

    risks = [f"size={state.get('size', '')}", f"risk={state.get('risk', '')}"]
    next_steps = escalation[:2] if escalation else ["Review residual risks and close the task"]

    if changed:
        template = replace_section_placeholder(template, "Changed:", list_block(changed))
    if checks:
        template = replace_section_placeholder(template, "Verified:", list_block(checks[:4]))
    template = replace_section_placeholder(template, "Lessons Learned (Update MEMORY.md):", list_block(lessons))
    template = replace_section_placeholder(template, "Risks:", list_block(risks))
    if next_steps:
        template = replace_section_placeholder(template, "Next:", list_block(next_steps))
    template = fill_once(
        template,
        "Not verified:\n- ",
        "Not verified:\n- Add concrete repo-specific commands or manual evidence before final delivery",
    )
    return template
