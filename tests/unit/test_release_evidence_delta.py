"""Release snapshot metadata comparison never authenticates independent evidence."""
import copy
import json
import unittest
from pathlib import Path

from tools.release_evidence_brief import briefing
from tools.release_evidence_delta import compare, markdown

ROOT = Path(__file__).resolve().parents[2]


def packet(source=None):
    ledger = json.loads((ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_text())
    result = briefing(ledger, source_sha=source)
    result["ledger_file_sha256"] = "a" * 64
    return result


class ReleaseEvidenceDeltaTests(unittest.TestCase):
    def test_identical_snapshots_are_empty_and_immutable(self):
        before = packet()
        orig = copy.deepcopy(before)
        result = compare(before, copy.deepcopy(before))
        self.assertEqual(result["changed_gate_count"], 0)
        self.assertTrue(result["same_ledger_bytes"])
        self.assertEqual(before, orig)
        self.assertIn("diagnostic only", markdown(result).lower())

    def test_changed_source_records_gate_blockers_without_promotion(self):
        old = packet()
        new = packet(source="e" * 40)
        result = compare(old, new)
        self.assertEqual(result["changed_gate_count"], 12)
        self.assertEqual(result["after_source"], "e" * 40)
        self.assertIn("blockers", result["gate_changes"][0]["changes"])
        self.assertEqual(result["authority"], "diagnostic_only_no_evidence_or_acceptance_promotion")

    def test_same_counts_changed_ledger_bytes_flag_unexplained(self):
        old = packet()
        new = copy.deepcopy(old)
        new["ledger_file_sha256"] = "b" * 64
        result = compare(old, new)
        self.assertTrue(result["unexplained_ledger_byte_change"])
        self.assertEqual(result["changed_gate_count"], 0)

    def test_status_change_reported_not_accepted(self):
        old = packet()
        new = copy.deepcopy(old)
        new["gates"][0]["status"] = "passed"
        result = compare(old, new)
        self.assertEqual(result["gate_changes"][0]["changes"]["status"],
                         {"before": "in_progress", "after": "passed"})
        self.assertNotIn("accepted_gate_count", result)

    def test_rejects_foreign_schema_incomplete_and_false_authority(self):
        old = packet()
        for key, bad in (("schema", "OTHER"), ("authority", "accepted"),
                         ("ledger_file_sha256", "invalid")):
            new = copy.deepcopy(old)
            new[key] = bad
            with self.assertRaises(ValueError):
                compare(old, new)
        new = copy.deepcopy(old)
        new["gates"].pop()
        with self.assertRaises(ValueError):
            compare(old, new)

    def test_rejects_false_source_match_and_legacy_unknown_claim(self):
        old = packet()
        self.assertIsNone(old["source_matches_ledger"])
        tampered = copy.deepcopy(old)
        tampered["source_matches_ledger"] = True
        with self.assertRaisesRegex(ValueError, "source comparison"):
            compare(old, tampered)
        tampered = packet("e" * 40)
        tampered["source_matches_ledger"] = True
        with self.assertRaisesRegex(ValueError, "source comparison"):
            compare(old, tampered)

    def test_rejects_fake_counts_and_duplicate_ids(self):
        old = packet()
        new = copy.deepcopy(old)
        new["gates"][0]["reference_count"] = True
        with self.assertRaises(ValueError):
            compare(old, new)
        new = copy.deepcopy(old)
        new["gates"][1]["id"] = "QA-01"
        with self.assertRaises(ValueError):
            compare(old, new)


if __name__ == "__main__":
    unittest.main()
