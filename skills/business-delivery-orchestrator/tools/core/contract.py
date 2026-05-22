from __future__ import annotations

from core.templates import (
    fill_once,
    list_block,
    load_template_code_block,
    replace_section_placeholder,
)

def render_contract(*, objective: str, size: str, risk: str, mode: str) -> str:
    if mode == "full" or size in {"L", "XL"}:
        template = load_template_code_block("full-delivery-contract-template.md")
        template = fill_once(template, "Goal:\n- ", f"Goal:\n- {objective or ''}")
        template = replace_section_placeholder(
            template, "Risks and assumptions:", list_block([f"size={size}", f"risk={risk}"])
        )
        return template
    template = load_template_code_block("lightweight-contract-template.md")
    template = fill_once(template, "Goal:\n- ", f"Goal:\n- {objective or ''}")
    template = replace_section_placeholder(
        template, "Assumptions:", list_block([f"size={size}", f"risk={risk}"])
    )
    return template
