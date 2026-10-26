"""Read-only release briefing contracts; no acceptance granted."""
import copy
import json
import unittest
from pathlib import Path
from tools.release_evidence_brief import briefing, markdown

ROOT = Path(__file__).resolve().parents[2]


class ReleaseEvidenceBriefTests(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads((ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_text())
        self.original = copy.deepcopy(self.ledger)

    def test_real_twelve_gate_inventory_and_no_mutation(self):
        result = briefing(self.ledger)
        self.assertEqual(len(result["gates"]), 12)
        self.assertEqual(result["accepted_gate_count"], 0)
        self.assertEqual(result["authority"], "diagnostic_only_no_acceptance_promotion")
        self.assertEqual(self.ledger, self.original)
        self.assertIn("read-only", markdown(result).lower())

    def test_missing_source_is_explicitly_unknown_not_a_match(self):
        result = briefing(self.ledger)
        self.assertIsNone(result["checked_source_commit"])
        self.assertIsNone(result["source_matches_ledger"])
        self.assertTrue(all("requested_source_not_checked" in row["blockers"]
                            for row in result["gates"]))
        self.assertIn("Source comparison: UNKNOWN", markdown(result))
        self.assertNotIn("Source comparison: MATCH", markdown(result))
        self.assertEqual(result["accepted_gate_count"], 0)

    def test_verified_nominee_source_is_a_match(self):
        source = self.ledger["candidate"]["commit_sha"]
        result = briefing(self.ledger, source_sha=source)
        self.assertIs(result["source_matches_ledger"], True)
        self.assertNotIn("requested_source_not_checked", result["gates"][0]["blockers"])
        self.assertNotIn("requested_source_differs_from_nominated_candidate",
                         result["gates"][0]["blockers"])
        self.assertIn("Source comparison: MATCH", markdown(result))

    def test_wrong_source_marks_every_gate_without_awarding_credit(self):
        result = briefing(self.ledger, source_sha="e" * 40)
        self.assertIs(result["source_matches_ledger"], False)
        self.assertIn("Source comparison: MISMATCH", markdown(result))
        self.assertTrue(all("requested_source_differs_from_nominated_candidate" in x["blockers"]
                            for x in result["gates"]))

    def test_reject_missing_gate_and_malformed_source(self):
        self.ledger["gates"].pop()
        with self.assertRaisesRegex(ValueError, "gate inventory"):
            briefing(self.ledger)
        with self.assertRaises(ValueError):
            briefing(self.original, source_sha="main")

    def test_witness_count_is_not_assumed_validity(self):
        gate = self.ledger["gates"][0]
        gate["witnesses"] = [{"claimed": "not verified"}]
        result = briefing(self.ledger)
        self.assertEqual(result["accepted_gate_count"], 0)
        self.assertEqual(result["gates"][0]["witness_count"], 1)
        self.assertIn("gate_not_accepted", result["gates"][0]["blockers"])


if __name__ == "__main__":
    unittest.main()
