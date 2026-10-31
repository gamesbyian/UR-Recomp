"""Live report cannot turn unreviewed merges into unearned score credit."""
import json
import unittest
from pathlib import Path
from tools.live_progress import summarize

ROOT = Path(__file__).resolve().parents[2]

class LiveProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.i=json.loads((ROOT/"docs/progress/windows-beta-v2-inventory.json").read_text())
        cls.l=json.loads((ROOT/"docs/RELEASE-QUALITY-LEDGER.json").read_text())

    def test_current_head_and_pending_merges_preserve_exact_verified_score(self):
        sha=self.i["source_sha"]
        a=summarize(self.i,self.l,sha,sha,0)
        b=summarize(self.i,self.l,sha,"f"*40,76)
        self.assertTrue(a["review_covers_current_head"])
        self.assertFalse(b["review_covers_current_head"])
        self.assertEqual(b["verified_bounded_coverage_percent"],
                         a["verified_bounded_coverage_percent"])
        self.assertEqual(b["unreviewed_commits"],76)
        self.assertEqual(a["current_completion_estimate_percent"],
                         a["verified_bounded_coverage_percent"])
        self.assertIsNone(b["current_completion_estimate_percent"])
        self.assertTrue(b["last_accepted_score_is_not_current_estimate"])

    def test_stale_scoring_never_changes_release_gates_or_usa_events(self):
        sha=self.i["source_sha"]
        v=summarize(self.i,self.l,sha,"e"*40,500)
        self.assertEqual(v["release_gates_passed"],0)
        self.assertEqual(v["accepted_USA_events"],0)
        self.assertEqual(v["unverified_criteria_count"],
                         len([c for c in self.i["criteria"] if c["status"]!="bounded_verified"]))

if __name__ == "__main__":
    unittest.main()
