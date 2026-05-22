from __future__ import annotations

from datetime import date

from core.templates import fill_once, load_template_code_block


def render_memory_entry(state: dict) -> str:
    objective = state.get("objective", "") or "delivery"
    template = load_template_code_block("memory-entry-template.md")
    template = fill_once(
        template,
        "## YYYY-MM-DD - <feature-or-incident-name>",
        f"## {date.today().isoformat()} - {objective}",
    )
    template = fill_once(template, "- Context:", f"- Context: {objective}")
    template = fill_once(
        template,
        "- Lesson:",
        "- Lesson: Capture one reusable pitfall from the delivery.",
    )
    template = fill_once(
        template,
        "- Actionable rule for future work:",
        "- Actionable rule for future work: Apply the same guardrail next time.",
    )
    template = fill_once(template, "- Evidence:", f"- Evidence: {state.get('handoff_path', '')}")
    return template
