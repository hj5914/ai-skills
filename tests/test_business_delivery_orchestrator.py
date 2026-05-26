from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
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
from core.verify import render_verify

BDO_SPEC = importlib.util.spec_from_file_location("bdo_cli", TOOLS_DIR / "bdo.py")
assert BDO_SPEC and BDO_SPEC.loader
BDO_MODULE = importlib.util.module_from_spec(BDO_SPEC)
BDO_SPEC.loader.exec_module(BDO_MODULE)
_ensure_contract_allowed = BDO_MODULE._ensure_contract_allowed
_ensure_phase_transition_allowed = BDO_MODULE._ensure_phase_transition_allowed
_ensure_contract_exists = BDO_MODULE._ensure_contract_exists
_ensure_verification_complete = BDO_MODULE._ensure_verification_complete
_invalidate_downstream_artifacts_if_contract_changed = BDO_MODULE._invalidate_downstream_artifacts_if_contract_changed
_invalidate_handoff_if_upstream_changed = BDO_MODULE._invalidate_handoff_if_upstream_changed
_verify_warning = BDO_MODULE._verify_warning
build_resume_summary = BDO_MODULE.build_resume_summary
_build_blocked_recovery = BDO_MODULE._build_blocked_recovery
build_parser = BDO_MODULE.build_parser
cmd_classify = BDO_MODULE.cmd_classify
cmd_contract_what = BDO_MODULE.cmd_contract_what


class BusinessDeliveryOrchestratorTests(unittest.TestCase):
    def _run_cli_func_silently(self, func, args) -> None:
        with redirect_stdout(io.StringIO()):
            func(args)

    def _run_cli_func_json(self, func, args) -> dict:
        buf = io.StringIO()
        with redirect_stdout(buf):
            func(args)
        return json.loads(buf.getvalue())

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
        self.assertEqual(normalized["verification_summary"]["runtime_evidence"], [])
        self.assertEqual(normalized["verification_summary"]["gaps"], [])
        self.assertEqual(normalized["delta"][0]["summary"], "")
        self.assertEqual(normalized["delta"][0]["follow_ups"], [])
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
        self.assertEqual(loaded["verification_summary"]["runtime_evidence"], [])
        self.assertEqual(loaded["verification_summary"]["gaps"], [])
        self.assertEqual(loaded["delta"][0]["summary"], "")
        self.assertEqual(loaded["delta"][0]["follow_ups"], [])
        self.assertEqual(loaded["impact_scan"]["recommended_size"], "")
        self.assertEqual(loaded["contract_stage"], "")

    def test_validate_state_accepts_payment_and_migration_surfaces(self) -> None:
        state = default_state()
        state["surfaces"] = ["payment", "migration"]

        validate_state(state)

    def test_classify_preserves_existing_surfaces_when_not_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".bdo.state.json"
            state = default_state()
            state["surfaces"] = ["auth", "data"]
            BDO_MODULE.save_state(state_path, state)
            parser = build_parser()
            args = parser.parse_args(["--state", str(state_path), "classify", "--size", "L", "--risk", "high"])

            self._run_cli_func_silently(cmd_classify, args)
            updated = load_state(state_path)

        self.assertEqual(updated["surfaces"], ["auth", "data"])

    def test_classify_can_explicitly_clear_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".bdo.state.json"
            state = default_state()
            state["surfaces"] = ["payment"]
            BDO_MODULE.save_state(state_path, state)
            parser = build_parser()
            args = parser.parse_args(
                ["--state", str(state_path), "classify", "--size", "M", "--risk", "medium", "--clear-surfaces"]
            )

            self._run_cli_func_silently(cmd_classify, args)
            updated = load_state(state_path)

        self.assertEqual(updated["surfaces"], [])

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
                "follow_ups": ["Investigate legacy default password handling separately"],
            }
        ]
        state["verification_summary"] = {
            "checks": ["Inspect final diff"],
            "escalation": ["Verify frontend/backend contract alignment because multiple layers changed"],
            "stop_conditions": [],
            "evidence": ["pytest tests/foo_test.py"],
            "runtime_evidence": ["curl -i http://localhost:3000/login returned 200 and set-cookie"],
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
        self.assertIn("curl -i http://localhost:3000/login returned 200 and set-cookie", rendered)
        self.assertIn("no e2e env", rendered)
        self.assertIn("contract alignment", rendered)
        self.assertIn("Investigate legacy default password handling separately", rendered)
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
            "runtime_evidence": [],
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

    def test_render_handoff_adds_runtime_config_gap_when_runtime_evidence_is_missing(self) -> None:
        state = default_state()
        state["surfaces"] = ["config", "backend", "auth"]
        state["verification_summary"] = {
            "checks": ["Inspect final diff"],
            "escalation": [],
            "stop_conditions": [],
            "evidence": ["pnpm build"],
            "runtime_evidence": [],
            "gaps": [],
        }

        rendered = render_handoff(state)

        self.assertIn("Runtime configuration was not verified", rendered)
        self.assertIn("environment-variable availability is still unproven", rendered)

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

    def test_verification_summary_adds_sensitive_auth_flow_checks(self) -> None:
        summary = BDO_MODULE.build_verification_summary(
            {
                "size": "L",
                "risk": "high",
                "surfaces": ["auth", "backend", "ui", "config"],
            }
        )

        checks = "\n".join(summary["checks"])
        self.assertIn("login/session happy-path and denial-path", checks)
        self.assertIn("sameSite and secure expectations", checks)
        self.assertIn("CORS or origin settings", checks)
        self.assertIn("representative runtime or end-to-end flow", checks)
        self.assertIn("deployment-like configuration", checks)

    def test_render_verify_separates_runtime_evidence(self) -> None:
        state = default_state()
        state["verification_summary"] = {
            "checks": ["Inspect final diff"],
            "escalation": [],
            "stop_conditions": [],
            "evidence": ["pnpm build"],
            "runtime_evidence": ["curl -i http://localhost:3000/health returned 200"],
            "gaps": ["manual UI flow not run"],
        }

        rendered = render_verify(state)

        self.assertIn("Runtime evidence collected:", rendered)
        self.assertIn("pnpm build", rendered)
        self.assertIn("curl -i http://localhost:3000/health returned 200", rendered)
        self.assertIn("Build or typecheck success is not enough", rendered)

    def test_verify_warning_flags_config_runtime_gap(self) -> None:
        state = default_state()
        state["surfaces"] = ["config", "backend", "auth"]

        warning = _verify_warning(state, runtime_evidence=[])

        self.assertIn("verified without runtime evidence", warning)

    def test_verify_cli_emits_warning_when_config_runtime_evidence_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".bdo.state.json"
            contract_path = Path(tmpdir) / "bdo.contract.md"
            contract_path.write_text("contract\n", encoding="utf-8")
            state = default_state()
            state["size"] = "M"
            state["contract_path"] = str(contract_path)
            state["contract_stage"] = "lightweight"
            state["surfaces"] = ["config", "backend", "auth"]
            BDO_MODULE.save_state(state_path, state)
            parser = build_parser()
            args = parser.parse_args(
                ["--state", str(state_path), "--json", "verify", "--evidence", "pnpm build"]
            )

            payload = self._run_cli_func_json(BDO_MODULE.cmd_verify, args)

        self.assertIn("warning", payload["data"])
        self.assertIn("verified without runtime evidence", payload["data"]["warning"])

    def test_full_contract_verification_plan_mentions_runtime_flow(self) -> None:
        contract = render_contract(
            objective="Harden login flow",
            size="L",
            risk="high",
            mode="full",
            surfaces=["auth", "backend", "ui", "config"],
        )

        self.assertIn(
            "start the affected service with deployment-like configuration, confirm required env or config keys are present, and record one startup or health-path check",
            contract,
        )

    def test_impact_scan_separates_code_test_and_doc_text_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "docs").mkdir()
            (root / "src" / "consumer.ts").write_text("const targetFlag = true;\n", encoding="utf-8")
            (root / "tests" / "consumer.test.ts").write_text("expect(targetFlag).toBe(true)\n", encoding="utf-8")
            (root / "docs" / "consumer.md").write_text("targetFlag rollout note\n", encoding="utf-8")

            result = run_impact_scan(root, ["targetFlag"])

        self.assertIn("1 code text fallback match(es)", result["summary"])
        self.assertIn("1 test text fallback match(es)", result["summary"])
        self.assertIn("1 doc text fallback match(es)", result["summary"])
        self.assertEqual(result["recommended_size"], "S")

    def test_impact_scan_bumps_size_for_sensitive_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "migrations").mkdir()
            (root / "migrations" / "001_add_payment.sql").write_text("-- payment migration\n", encoding="utf-8")

            result = run_impact_scan(root, ["payment"])

        self.assertEqual(result["recommended_size"], "M")
        self.assertIn("Sensitive keyword bump applied for:", result["notes"][-1])
        self.assertIn("payment", result["notes"][-1])
        self.assertIn("migration", result["notes"][-1])

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
        self.assertIn("Verification plan:", how)
        self.assertIn("- Unit: focus on direct logic changes and boundary cases", how)
        self.assertIn("- E2E/manual:", how)

    def test_contract_assumptions_are_deduplicated(self) -> None:
        contract = render_contract(
            objective="Add bulk archive",
            size="L",
            risk="medium",
            mode="full",
            surfaces=["ui", "backend"],
            clarify_assumptions=[
                "size=L",
                "risk=medium",
                "surfaces=ui, backend",
                "Resolved: reject mixed-status selections",
            ],
        )

        self.assertEqual(contract.count("- size=L"), 1)
        self.assertEqual(contract.count("- risk=medium"), 1)
        self.assertEqual(contract.count("- surfaces=ui, backend"), 1)
        self.assertIn("Resolved: reject mixed-status selections", contract)

    def test_contract_what_updates_state_for_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".bdo.state.json"
            output_path = Path(tmpdir) / "bdo.contract.what.md"
            state = default_state()
            state["objective"] = "Add bulk archive"
            state["size"] = "L"
            BDO_MODULE.save_state(state_path, state)
            parser = build_parser()
            args = parser.parse_args(["--state", str(state_path), "contract-what", "--output", str(output_path)])

            self._run_cli_func_silently(cmd_contract_what, args)
            updated = load_state(state_path)

        self.assertEqual(updated["phase"], "contract")
        self.assertEqual(updated["contract_path"], str(output_path))
        self.assertEqual(updated["contract_stage"], "what")

    def test_contract_gate_rejects_what_only_contract_for_large_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.what.md"
            contract_path.write_text("what\n", encoding="utf-8")
            state = default_state()
            state["size"] = "L"
            state["contract_path"] = str(contract_path)
            state["contract_stage"] = "what"

            with self.assertRaisesRegex(ValueError, "requires a HOW or full contract"):
                _ensure_contract_exists(state, command="verify")

    def test_contract_change_invalidates_downstream_verification_and_reviews(self) -> None:
        state = default_state()
        state["contract_path"] = "bdo.contract.md"
        state["contract_stage"] = "full"
        state["verification_path"] = "bdo.verify.md"
        state["handoff_path"] = "bdo.handoff.md"
        state["verification_summary"] = {
            "checks": ["Inspect final diff"],
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

        _invalidate_downstream_artifacts_if_contract_changed(
            state,
            previous_contract=("bdo.contract.md", "full"),
            current_contract=("bdo.contract.how.md", "how"),
        )

        self.assertEqual(state["verification_path"], "")
        self.assertEqual(state["handoff_path"], "")
        self.assertEqual(state["reviews"], [])
        self.assertEqual(state["verification_summary"]["evidence"], [])

    def test_same_contract_does_not_invalidate_downstream_artifacts(self) -> None:
        state = default_state()
        state["contract_path"] = "bdo.contract.md"
        state["contract_stage"] = "full"
        state["verification_path"] = "bdo.verify.md"
        state["handoff_path"] = "bdo.handoff.md"
        state["verification_summary"] = {
            "checks": [],
            "escalation": [],
            "stop_conditions": [],
            "evidence": ["pytest tests/foo_test.py"],
            "gaps": [],
        }

        _invalidate_downstream_artifacts_if_contract_changed(
            state,
            previous_contract=("bdo.contract.md", "full"),
            current_contract=("bdo.contract.md", "full"),
        )

        self.assertEqual(state["verification_path"], "bdo.verify.md")
        self.assertEqual(state["handoff_path"], "bdo.handoff.md")
        self.assertEqual(state["verification_summary"]["evidence"], ["pytest tests/foo_test.py"])

    def test_upstream_change_invalidates_existing_handoff(self) -> None:
        state = default_state()
        state["handoff_path"] = "bdo.handoff.md"

        _invalidate_handoff_if_upstream_changed(state)

        self.assertEqual(state["handoff_path"], "")

    def test_phase_verify_requires_contract_for_medium_task(self) -> None:
        state = default_state()
        state["size"] = "M"

        with self.assertRaisesRegex(ValueError, "phase verify requires a contract"):
            _ensure_phase_transition_allowed(state, "verify")

    def test_phase_implement_requires_existing_contract_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state = default_state()
            state["size"] = "M"
            state["contract_path"] = str(Path(tmpdir) / "bdo.contract.md")

            with self.assertRaisesRegex(ValueError, "requires an existing contract file"):
                _ensure_phase_transition_allowed(state, "implement")

    def test_phase_verify_rejects_what_only_contract_for_large_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.what.md"
            contract_path.write_text("what\n", encoding="utf-8")
            state = default_state()
            state["size"] = "L"
            state["contract_path"] = str(contract_path)
            state["contract_stage"] = "what"

            with self.assertRaisesRegex(ValueError, "requires a HOW or full contract"):
                _ensure_phase_transition_allowed(state, "verify")

    def test_phase_deliver_requires_verification_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.md"
            contract_path.write_text("contract\n", encoding="utf-8")
            state = default_state()
            state["size"] = "M"
            state["contract_path"] = str(contract_path)

            with self.assertRaisesRegex(ValueError, "phase deliver requires a verification report"):
                _ensure_phase_transition_allowed(state, "deliver")

    def test_phase_deliver_requires_existing_verification_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.md"
            contract_path.write_text("contract\n", encoding="utf-8")
            state = default_state()
            state["size"] = "M"
            state["contract_path"] = str(contract_path)
            state["verification_path"] = str(Path(tmpdir) / "bdo.verify.md")

            with self.assertRaisesRegex(ValueError, "requires an existing verification report"):
                _ensure_phase_transition_allowed(state, "deliver")

    def test_resume_summary_requests_how_after_what_for_large_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.what.md"
            contract_path.write_text("what\n", encoding="utf-8")
            state = default_state()
            state["objective"] = "Add bulk archive"
            state["size"] = "L"
            state["phase"] = "contract"
            state["contract_path"] = str(contract_path)
            state["contract_stage"] = "what"

            summary = build_resume_summary(state)

        self.assertIn("paused at WHAT", summary["blockers"][0])
        self.assertEqual(summary["next_step"], "Complete the HOW pass before verification.")
        self.assertEqual(summary["suggested_command"], "contract-how")

    def test_resume_summary_detects_missing_verification_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.md"
            contract_path.write_text("contract\n", encoding="utf-8")
            state = default_state()
            state["objective"] = "Add bulk archive"
            state["size"] = "M"
            state["phase"] = "verify"
            state["contract_path"] = str(contract_path)
            state["contract_stage"] = "lightweight"
            state["verification_path"] = "/tmp/does-not-exist.verify.md"

            summary = build_resume_summary(state)

        self.assertIn("Missing verification artifact", summary["blockers"][0])
        self.assertEqual(summary["next_step"], "Regenerate the missing verification report before handoff.")
        self.assertEqual(summary["suggested_command"], "verify --evidence \"...\"")

    def test_resume_summary_points_to_handoff_when_verification_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.md"
            verification_path = Path(tmpdir) / "bdo.verify.md"
            contract_path.write_text("contract\n", encoding="utf-8")
            verification_path.write_text("verify\n", encoding="utf-8")
            state = default_state()
            state["objective"] = "Add bulk archive"
            state["size"] = "M"
            state["phase"] = "verify"
            state["contract_path"] = str(contract_path)
            state["contract_stage"] = "lightweight"
            state["verification_path"] = str(verification_path)

            summary = build_resume_summary(state)

        self.assertEqual(summary["blockers"], [])
        self.assertEqual(summary["next_step"], "Generate the handoff artifact to complete delivery.")
        self.assertEqual(summary["suggested_command"], "handoff")

    def test_resume_summary_flags_phase_without_contract(self) -> None:
        state = default_state()
        state["objective"] = "Add bulk archive"
        state["size"] = "M"
        state["phase"] = "verify"

        summary = build_resume_summary(state)

        self.assertIn("Phase/state mismatch: verification or delivery is recorded without a contract.", summary["blockers"])
        self.assertEqual(summary["next_step"], "Regenerate the required contract before trusting verify or delivery state.")
        self.assertEqual(summary["suggested_command"], "contract --mode lightweight")

    def test_resume_summary_flags_missing_lxl_reviews_after_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "bdo.contract.how.md"
            verification_path = Path(tmpdir) / "bdo.verify.md"
            contract_path.write_text("contract\n", encoding="utf-8")
            verification_path.write_text("verify\n", encoding="utf-8")
            state = default_state()
            state["objective"] = "Add bulk archive"
            state["size"] = "L"
            state["phase"] = "verify"
            state["contract_path"] = str(contract_path)
            state["contract_stage"] = "how"
            state["verification_path"] = str(verification_path)
            state["reviews"] = [
                {
                    "kind": "spec",
                    "status": "DONE",
                    "focus": "contract alignment",
                    "findings": [],
                    "evidence": ["checked contract"],
                }
            ]

            summary = build_resume_summary(state)

        self.assertIn("Missing completed L/XL reviews: quality.", summary["blockers"])
        self.assertEqual(summary["next_step"], "Record the missing completed reviews before handoff: quality.")
        self.assertEqual(summary["suggested_command"], "review --kind spec|quality --status DONE")

    def test_blocked_recovery_requests_more_context(self) -> None:
        state = default_state()
        state["reviews"] = [
            {
                "kind": "quality",
                "status": "NEEDS_CONTEXT",
                "focus": "missing credential",
                "findings": ["Need access token for regression environment"],
                "evidence": [],
            }
        ]

        recovery = _build_blocked_recovery(state)

        self.assertEqual(recovery["mode"], "provide_context")
        self.assertIn("needs more context", recovery["blocker"])
        self.assertEqual(recovery["suggested_command"], 'quiz --assumption "..."')

    def test_blocked_recovery_escalates_plan_when_review_mentions_contract(self) -> None:
        state = default_state()
        state["contract_stage"] = "what"
        state["reviews"] = [
            {
                "kind": "spec",
                "status": "BLOCKED",
                "focus": "contract mismatch",
                "findings": ["Plan is wrong for the current contract"],
                "evidence": [],
            }
        ]

        recovery = _build_blocked_recovery(state)

        self.assertEqual(recovery["mode"], "escalate_plan")
        self.assertEqual(recovery["suggested_command"], "contract-how")

    def test_blocked_recovery_collapses_to_single_agent_for_small_task(self) -> None:
        state = default_state()
        state["size"] = "M"
        state["reviews"] = [
            {
                "kind": "quality",
                "status": "BLOCKED",
                "focus": "low confidence",
                "findings": ["Another delegated pass is not justified"],
                "evidence": [],
            }
        ]

        recovery = _build_blocked_recovery(state)

        self.assertEqual(recovery["mode"], "collapse_to_single_agent")
        self.assertEqual(recovery["suggested_command"], "phase implement")

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

    def test_clarify_warning_flags_possible_multi_delivery_scope(self) -> None:
        warning = clarify_warning(size="L", risk="medium", surfaces=["ui", "backend", "auth"], has_quiz=False)

        self.assertIn("one delivery or several independent fixes", warning)

    def test_handoff_requires_spec_and_quality_reviews_for_large_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            verification_path = Path(tmpdir) / "bdo.verify.md"
            verification_path.write_text("ok\n", encoding="utf-8")
            state = default_state()
            state["size"] = "L"
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
