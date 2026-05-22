from __future__ import annotations

import json
import re
from pathlib import Path


TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".yaml",
    ".yml",
}

IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+.*?\bfrom\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    re.compile(r"^\s*export\s+.*?\bfrom\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"from\s+([A-Za-z0-9_./-]+)\s+import\s+", re.MULTILINE),
    re.compile(r"^\s*import\s+([A-Za-z0-9_.,\s]+)", re.MULTILINE),
]


def run_impact_scan(root: Path, targets: list[str]) -> dict:
    normalized_targets = [target.strip() for target in targets if target and target.strip()]
    if not normalized_targets:
        return {
            "targets": [],
            "matched_files": [],
            "summary": "No targets provided for impact scan.",
            "recommended_size": "",
            "notes": ["Provide one or more module, path, or schema keywords to scan."],
        }

    direct_matches: set[str] = set()
    import_matches: set[str] = set()
    text_matches: set[str] = set()

    for path in root.rglob("*"):
        if not path.is_file() or _should_skip(path):
            continue

        relative = str(path.relative_to(root))
        relative_lower = relative.lower()
        lowered_targets = [target.lower() for target in normalized_targets]
        if any(target in relative_lower for target in lowered_targets):
            direct_matches.add(relative)
            continue

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        if _has_import_reference(text, normalized_targets):
            import_matches.add(relative)
            continue

        lowered_text = text.lower()
        if any(target in lowered_text for target in lowered_targets):
            text_matches.add(relative)

    ordered_matches = sorted(direct_matches) + sorted(import_matches - direct_matches) + sorted(
        text_matches - direct_matches - import_matches
    )
    count = len(ordered_matches)
    recommended_size = _recommended_size(count)
    summary = (
        f"Matched {count} file(s): {len(direct_matches)} direct path match(es), "
        f"{len(import_matches)} import/use match(es), {len(text_matches)} text fallback match(es)"
        if count
        else f"No matches found for targets: {', '.join(normalized_targets)}"
    )
    notes = [
        "This scan prefers path matches and import/use references before falling back to plain text matches.",
        "Treat the result as a sizing heuristic, not a complete dependency graph.",
    ]
    return {
        "targets": normalized_targets,
        "matched_files": ordered_matches[:50],
        "summary": summary,
        "recommended_size": recommended_size,
        "notes": notes,
    }


def mine_constraints(root: Path) -> list[str]:
    constraints: list[str] = []

    package_json = root / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            constraints.append("package.json exists but could not be parsed; inspect manually.")
        else:
            package_manager = data.get("packageManager")
            if isinstance(package_manager, str):
                constraints.append(f"Package manager: {package_manager}")
            scripts = data.get("scripts", {})
            if isinstance(scripts, dict):
                for key in ("test", "lint", "typecheck", "build"):
                    value = scripts.get(key)
                    if isinstance(value, str):
                        constraints.append(f"Script {key}: {value}")
            deps = {}
            for key in ("dependencies", "devDependencies"):
                value = data.get(key, {})
                if isinstance(value, dict):
                    deps.update(value)
            for dep in ("react", "vue", "next", "express", "fastapi", "django", "flask"):
                if dep in deps:
                    constraints.append(f"Framework/library detected: {dep}@{deps[dep]}")

    for filename, label in (
        ("tsconfig.json", "TypeScript config present"),
        ("pyproject.toml", "Python project metadata present"),
        ("go.mod", "Go module present"),
        ("Cargo.toml", "Rust cargo manifest present"),
        (".eslintrc", "ESLint config present"),
        (".eslintrc.js", "ESLint config present"),
        (".eslintrc.cjs", "ESLint config present"),
        (".eslintrc.json", "ESLint config present"),
        (".prettierrc", "Prettier config present"),
    ):
        if (root / filename).exists():
            constraints.append(label)

    if not constraints:
        constraints.append("No supported config files detected automatically; mine constraints manually.")
    return constraints


def _has_import_reference(text: str, targets: list[str]) -> bool:
    lowered_targets = [target.lower() for target in targets]
    for pattern in IMPORT_PATTERNS:
        for match in pattern.findall(text):
            if isinstance(match, tuple):
                values = [value for value in match if value]
            else:
                values = [match]
            for value in values:
                normalized = value.strip().lower()
                if any(target in normalized for target in lowered_targets):
                    return True
    return False


def _recommended_size(count: int) -> str:
    if count <= 1:
        return "S"
    if count <= 5:
        return "M"
    if count <= 12:
        return "L"
    return "XL"


def _should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(part in parts for part in {".git", "node_modules", ".next", "dist", "build", "__pycache__"})
