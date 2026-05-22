from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "skills" / "business-delivery-orchestrator" / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from core.handoff import render_handoff
from core.contract import render_contract
from core.memory import parse_memory_entry, render_memory_entry
from core.quiz import build_clarify_quiz, clarify_warning
from core.scan import run_impact_scan
from core.state import default_state, load_state, normalize_state, validate_state
from core.templates import replace_section_placeholder

BDO_SPEC = importlib.util.spec_from_file_location("bdo_cli", TOOLS_DIR / "bdo.py")
assert BDO_SPEC and BDO_SPEC.loader
BDO_MODULE = importlib.util.module_from_spec(BDO_SPEC)
BDO_SPEC.loader.exec_module(BDO_MODULE)
_ensure_contract_allowed = BDO_MODULE._ensure_contract_allowed
_ensure_contract_exists = BDO_MODULE._ensure_contract_exists
_ensure_verification_complete = BDO_MODULE._ensure_verification_complete


class BusinessDeliveryOrchestratorTests(unittest.TestCase):
    def test_normalize_state_backfills_new_fields(self) -> None:
        legacy = {
            "objective": "Demo",
            "size": "M",
            "risk": "medium",
            "phase": "verify",
            "contract_path": "",
            "verification_path": "",
            "handoff_path": "",
            "surfaces": ["ui"],
            "verification_summary": {
                "checks": ["check"],
                "escalation": ["escalate"],
                "stop_conditions": ["stop"],
            },
            "delta": [
                {
                    "added": ["a.py"],
                    "removed": [],
                    "changed": ["b.py"],
                    "impact": "changed api surface",
                }
            ],
            "memory": [],
        }

        normalized = normalize_state(legacy)

        self.assertEqual(normalized["verification_summary"]["evidence"], [])
        self.assertEqual(normalized["verification_summary"]["gaps"], [])
        self.assertEqual(normalized["delta"][0]["summary"], "")
        self.assertEqual(normalized["impact_scan"]["matched_files"], [])
        self.assertEqual(normalized["constraints_detected"], [])
        self.assertEqual(normalized["clarify_quiz"]["questions"], [])

    def test_load_state_normalizes_legacy_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / ".bdo.state.json"
            legacy = default_state()
            legacy["verification_summary"].pop("evidence")
            legacy["verification_summary"].pop("gaps")
            legacy["delta"] = [
                {
                    "added": ["a.py"],
                    "removed": [],
                    "changed": ["b.py"],
                    "impact": "changed api surface",
                }
            ]
            path.write_text(json.dumps(legacy), encoding="utf-8")

            loaded = load_state(path)

        self.assertEqual(loaded["verification_summary"]["evidence"], [])
        self.assertEqual(loaded["verification_summary"]["gaps"], [])
        self.assertEqual(loaded["delta"][0]["summary"], "")
        self.assertEqual(loaded["impact_scan"]["recommended_size"], "")

    def test_validate_state_accepts_payment_and_migration_surfaces(self) -> None:
        state = default_state()
        state["surfaces"] = ["payment", "migration"]

        validate_state(state)

    def test_replace_section_placeholder_replaces_entire_block(self) -> None:
        template = "Changed:\n- old one\n- old two\n\nNext:\n- keep\n"
        rendered = replace_section_placeholder(template, "Changed:", "- new one\n- new two")

        self.assertIn("Changed:\n- new one\n- new two", rendered)
        self.assertNotIn("old one", rendered)
        self.assertIn("Next:\n- keep", rendered)

    def test_render_handoff_uses_evidence_and_no_blank_placeholders(self) -> None:
        state = default_state()
        state["objective"] = "Smoke handoff"
        state["surfaces"] = ["ui", "api"]
        state["delta"] = [
            {
                "added": [],
                "removed": [],
                "changed": ["skills/foo.py"],
                "impact": "ui copy updated",
                "summary": "changed skills/foo.py; ui copy updated",
            }
        ]
        state["verification_summary"] = {
            "checks": ["Inspect final diff"],
            "escalation": ["Verify frontend/backend contract alignment because multiple layers changed"],
            "stop_conditions": [],
            "evidence": ["pytest tests/foo_test.py"],
            "gaps": ["no e2e env"],
        }
        state["reviews"] = [
            {
                "kind": "spec",
                "status": "DONE",
                "focus": "contract alignment",
                "findings": ["No scope drift found"],
                "evidence": ["reviewed contract and diff"],
            }
        ]
        state["memory"] = [
            "## 2026-05-22 - Smoke handoff\n\n- Context: Smoke handoff\n- Lesson: Guard empty states\n- Actionable rule for future work: Always cover loading, empty, error\n- Evidence: pytest tests/foo_test.py"
        ]

        rendered = render_handoff(state)

        self.assertIn("pytest tests/foo_test.py", rendered)
        self.assertIn("no e2e env", rendered)
        self.assertIn("contract alignment", rendered)
        self.assertNotIn("Inspect final diff", rendered)
        self.assertNotIn("\n- \n", rendered)
        self.assertNotIn("Not verified:\n- \n", rendered)

    def test_render_handoff_ignores_incomplete_reviews(self) -> None:
        state = default_state()
        state["verification_summary"] = {
            "checks": ["Inspect final diff"],
            "escalation": [],
            "stop_conditions": [],
            "evidence": ["pytest tests/foo_test.py"],
            "gaps": [],
        }
        state["reviews"] = [
            {
                "kind": "quality",
                "status": "BLOCKED",
                "focus": "edge cases",
                "findings": ["Needs stronger rollback check"],
                "evidence": ["review notes"],
            }
        ]

        rendered = render_handoff(state)

        self.assertIn("pytest tests/foo_test.py", rendered)
        self.assertNotIn("Needs stronger rollback check", rendered)
        self.assertNotIn("quality | BLOCKED", rendered)

    def test_render_memory_entry_derives_defaults_from_state(self) -> None:
        state = default_state()
        state["objective"] = "Smoke memory"
        state["surfaces"] = ["auth"]
        state["delta"] = [
            {
                "added": ["auth.py"],
                "removed": [],
                "changed": ["gate.py"],
                "impact": "tightened auth checks",
                "summary": "tightened auth checks",
            }
        ]

        rendered = render_memory_entry(state)
        parsed = parse_memory_entry(rendered)

        self.assertIn("Permission edges need explicit positive and negative coverage.", rendered)
        self.assertIn("Always verify allow and deny paths together.", rendered)
        self.assertEqual(parsed["context"], "Smoke memory | tightened auth checks")
        self.assertEqual(parsed["title"], f"{date.today().isoformat()} - Smoke memory")

    def test_impact_scan_prefers_import_matches_over_plain_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / "target_module.ts").write_text("export const value = 1;\n", encoding="utf-8")
            (root / "src" / "consumer.ts").write_text(
                "import { value } from './target_module';\nconsole.log(value)\n",
                encoding="utf-8",
            )
            (root / "src" / "notes.md").write_text("target_module is mentioned here\n", encoding="utf-8")

            result = run_impact_scan(root, ["target_module"])

        self.assertEqual(result["matched_files"][0], "src/target_module.ts")
        self.assertIn("src/consumer.ts", result["matched_files"])
        self.assertIn("src/notes.md", result["matched_files"])
        self.assertEqual(result["recommended_size"], "M")

    def test_render_contract_supports_what_and_how_passes(self) -> None:
        what = render_contract(
            objective="Add bulk archive",
            size="L",
            risk="medium",
            mode="what",
            surfaces=["ui", "backend"],
        )
        how = render_contract(
            objective="Add bulk archive",
            size="L",
            risk="medium",
            mode="how",
            surfaces=["ui", "backend"],
            constraints_detected=["Script test: pytest"],
        )

        self.assertIn("Delivery Contract - WHAT", what)
        self.assertIn("Shared behavior is intentionally deferred to the HOW pass.", what)
        self.assertIn("Delivery Contract - HOW", how)
        self.assertIn("Script test: pytest", how)

    def test_clarify_quiz_and_contract_assumptions(self) -> None:
        quiz = build_clarify_quiz(
            objective="Archive completed tasks",
            size="L",
            risk="high",
            surfaces=["ui", "backend", "auth"],
        )
        contract = render_contract(
            objective="Archive completed tasks",
            size="L",
            risk="high",
            mode="full",
            surfaces=["ui", "backend", "auth"],
            clarify_assumptions=["Resolved: reject mixed-status selections"],
        )

        self.assertGreaterEqual(len(quiz["questions"]), 3)
        self.assertIn("Permissions:", "\n".join(quiz["questions"]))
        self.assertIn("Resolved: reject mixed-status selections", contract)

    def test_clarify_warning_triggers_for_large_or_risky_tasks(self) -> None:
        self.assertIn(
            "Consider running `quiz`",
            clarify_warning(size="L", risk="high", surfaces=["ui"], has_quiz=False),
        )

    def test_handoff_requires_spec_and_quality_reviews_for_large_tasks(self) -> None:
        state = default_state()
        state["size"] = "L"
        state["verification_path"] = "bdo.verify.md"
        state["verification_summary"] = {
            "checks": [],
            "escalation": [],
            "stop_conditions": [],
            "evidence": ["pytest tests/foo_test.py"],
            "gaps": [],
        }
        state["reviews"] = [
            {
                "kind": "spec",
                "status": "DONE",
                "focus": "contract alignment",
                "findings": [],
                "evidence": ["checked contract"],
            }
        ]

        with self.assertRaisesRegex(ValueError, "requires completed reviews for: quality"):
            _ensure_verification_complete(state)

    def test_handoff_allows_large_tasks_with_completed_spec_and_quality_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            verification_path = Path(tmpdir) / "bdo.verify.md"
            verification_path.write_text("ok\n", encoding="utf-8")
            state = default_state()
            state["size"] = "XL"
            state["verification_path"] = str(verification_path)
            state["verification_summary"] = {
                "checks": [],
                "escalation": [],
                "stop_conditions": [],
                "evidence": ["pytest tests/foo_test.py"],
                "gaps": [],
            }
            state["reviews"] = [
                {
                    "kind": "spec",
                    "status": "DONE",
                    "focus": "contract alignment",
                    "findings": [],
                    "evidence": ["checked contract"],
                },
                {
                    "kind": "quality",
                    "status": "DONE_WITH_CONCERNS",
                    "focus": "residual risks",
                    "findings": ["Monitor cache invalidation"],
                    "evidence": ["reviewed diff"],
                },
            ]

            _ensure_verification_complete(state)

    def test_sensitive_surfaces_require_full_contract(self) -> None:
        state = default_state()
        state["surfaces"] = ["payment"]

        with self.assertRaisesRegex(ValueError, "require `contract --mode full`"):
            _ensure_contract_allowed(state, "lightweight")

    def test_contract_gate_requires_existing_contract_file(self) -> None:
        state = default_state()
        state["size"] = "M"
        state["contract_path"] = "/tmp/does-not-exist.contract.md"

        with self.assertRaisesRegex(ValueError, "requires an existing contract file"):
            _ensure_contract_exists(state, command="verify")

    def test_handoff_requires_existing_verification_report_file(self) -> None:
        state = default_state()
        state["size"] = "L"
        state["verification_path"] = "/tmp/does-not-exist.verify.md"
        state["verification_summary"] = {
            "checks": [],
            "escalation": [],
            "stop_conditions": [],
            "evidence": ["pytest tests/foo_test.py"],
            "gaps": [],
        }
        state["reviews"] = [
            {
                "kind": "spec",
                "status": "DONE",
                "focus": "contract alignment",
                "findings": [],
                "evidence": ["checked contract"],
            },
            {
                "kind": "quality",
                "status": "DONE",
                "focus": "residual risks",
                "findings": [],
                "evidence": ["reviewed diff"],
            },
        ]

        with self.assertRaisesRegex(ValueError, "requires an existing verification report"):
            _ensure_verification_complete(state)


if __name__ == "__main__":
    unittest.main()
