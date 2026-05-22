from __future__ import annotations

from pathlib import Path


def templates_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "templates"


def load_template_code_block(filename: str) -> str:
    text = (templates_dir() / filename).read_text(encoding="utf-8")
    marker = "```markdown\n"
    start = text.find(marker)
    if start == -1:
        raise ValueError(f"template code block not found: {filename}")
    start += len(marker)
    end = text.find("\n```", start)
    if end == -1:
        raise ValueError(f"template code block not closed: {filename}")
    return text[start:end].strip() + "\n"


def fill_once(template: str, target: str, replacement: str) -> str:
    if target not in template:
        return template
    return template.replace(target, replacement, 1)


def list_block(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- "


def checklist_block(items: list[str]) -> str:
    return "\n".join(f"- [ ] {item}" for item in items) if items else "- [ ] "


def replace_section_placeholder(template: str, heading: str, replacement_block: str) -> str:
    lines = template.splitlines()
    for i, line in enumerate(lines):
        if line != heading:
            continue
        start = i + 1
        end = start
        while end < len(lines) and lines[end].lstrip().startswith("-"):
            end += 1
        if end == start:
            continue
        new_lines = lines[: i + 1] + replacement_block.splitlines() + lines[end:]
        return "\n".join(new_lines) + ("\n" if template.endswith("\n") else "")
    return template
