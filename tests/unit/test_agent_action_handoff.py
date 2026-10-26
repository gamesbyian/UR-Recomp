"""Bounded, offline agent handoff contract tests; no release assertions."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import agent_action_handoff as handoff
from tools.release_evidence_brief import briefing

ORIGINAL = Path(__file__).resolve().parents[2]
HEAD = "e" * 40
SINCE = "d" * 40


class AgentActionHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        config_file = ORIGINAL / "analysis/agent-context-lanes.json"
        ledger_file = ORIGINAL / "docs/RELEASE-QUALITY-LEDGER.json"
        (self.root / "analysis").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "analysis/agent-context-lanes.json").write_bytes(config_file.read_bytes())
        (self.root / "docs/RELEASE-QUALITY-LEDGER.json").write_bytes(ledger_file.read_bytes())
        for source in ("WORK-QUEUE.md", "HOURLY-AGENT-LINES.md"):
            (self.root / "docs" / source).write_text("test authority")
        self.patches = [
            patch.object(handoff, "ROOT", self.root),
            patch.object(handoff, "run_git", side_effect=self.fake_git),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def fake_git(self, *args):
        if args[:2] == ("rev-parse", "--verify"):
            return HEAD
        if args[:2] == ("status", "--porcelain"):
            return ""
        if args[:2] == ("branch", "--show-current"):
            return "test/handoff"
        if args[:2] == ("cat-file", "-t"):
            return "commit"
        if args[:2] == ("merge-base", "--is-ancestor"):
            return ""
        if args[:2] == ("diff", "--name-only"):
            return "tools/a.py\nnative/b.cpp\ntools/a.py"
        if args[:1] == ("log",):
            return "1234567\tBounded change"
        raise AssertionError("unexpected Git command: " + repr(args))

    def make_old_brief(self, source=SINCE):
        raw = (self.root / "docs/RELEASE-QUALITY-LEDGER.json").read_bytes()
        result = briefing(json.loads(raw), source_sha=source)
        result["ledger_file_sha256"] = hashlib.sha256(raw).hexdigest()
        return result

    def test_no_implicit_baseline_and_no_assignment(self):
        result = handoff.build_handoff("release-qa")
        self.assertEqual(result["checkout_commit"], HEAD)
        self.assertEqual(result["source_changes"]["state"], "baseline_not_supplied")
        self.assertIsNone(result["brief_delta"])
        self.assertIsNone(result["next_step"]["gate"])
        self.assertEqual(len(result["release"]["eligible_gates"]), 12)
        self.assertFalse(result["release"]["checkout_matches_nominee"])
        self.assertIn("UNKNOWN", handoff.markdown(result))
        self.assertEqual(result["authority"], "read_only_navigation_zero_release_credit")

    def test_explicit_owned_gate_and_real_git_source_delta(self):
        result = handoff.build_handoff("modern-product", gate="QA-02", since=SINCE)
        self.assertEqual(result["next_step"]["gate"], "QA-02")
        self.assertEqual(result["next_step"]["required_layer"], "L4")
        self.assertEqual(result["source_changes"]["changed_path_count"], 2)
        self.assertEqual(result["source_changes"]["changed_paths"], ["native/b.cpp", "tools/a.py"])
        self.assertEqual(len(result["source_changes"]["recent_commits"]), 1)
        self.assertIn("No previous briefing supplied", handoff.markdown(result))

    def test_optional_previous_brief_diagnostic_delta(self):
        before = self.make_old_brief()
        result = handoff.build_handoff(
            "ci", gate="QA-12", since=SINCE, previous_brief=before
        )
        self.assertEqual(result["brief_delta_state"], "diagnostic_only")
        self.assertEqual(result["brief_delta"]["changed_gate_count"], 0)
        self.assertEqual(result["brief_delta"]["after_source"], HEAD)
        self.assertEqual(
            result["brief_delta"]["metadata_changes"]["checked_source_commit"],
            {"before": SINCE, "after": HEAD},
        )
        self.assertNotIn("accepted_gate_count", result["brief_delta"])

    def test_rejects_wrong_lane_gate_and_incorrect_baseline(self):
        with self.assertRaisesRegex(ValueError, "not assigned"):
            handoff.build_handoff("racer-hd", gate="QA-02")
        with self.assertRaisesRegex(ValueError, "requires --since"):
            handoff.build_handoff("ci", previous_brief=self.make_old_brief())
        with self.assertRaisesRegex(ValueError, "match --since"):
            handoff.build_handoff("ci", since=SINCE, previous_brief=self.make_old_brief(source=HEAD))
        with self.assertRaisesRegex(ValueError, "unknown agent lane"):
            handoff.build_handoff("not-a-lane")

    def test_dirty_checkout_refused(self):
        original = handoff.run_git
        def dirty(*args):
            if args[:2] == ("status", "--porcelain"):
                return " M docs/RELEASE-QUALITY-LEDGER.json"
            return original(*args)
        with patch.object(handoff, "run_git", side_effect=dirty):
            with self.assertRaisesRegex(ValueError, "dirty"):
                handoff.build_handoff("release-qa")

    def test_nonancestor_or_malformed_source_refused(self):
        with self.assertRaisesRegex(ValueError, "exact lowercase"):
            handoff.build_handoff("ci", since="main")
        original = handoff.run_git
        def nonancestor(*args):
            if args[:2] == ("merge-base", "--is-ancestor"):
                raise ValueError("Git command failed")
            return original(*args)
        with patch.object(handoff, "run_git", side_effect=nonancestor):
            with self.assertRaises(ValueError):
                handoff.build_handoff("ci", since=SINCE)

    def test_corrupt_ledger_fails_closed_not_partial_success(self):
        (self.root / "docs/RELEASE-QUALITY-LEDGER.json").write_text("{}")
        with self.assertRaises(ValueError):
            handoff.build_handoff("release-qa", gate="QA-01")

    def test_source_data_remains_untouched(self):
        before = (self.root / "docs/RELEASE-QUALITY-LEDGER.json").read_bytes()
        handoff.build_handoff("release-qa", gate="QA-01")
        self.assertEqual((self.root / "docs/RELEASE-QUALITY-LEDGER.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
