"""Historical v2 source-executed Windows 2P cold-ownership audit, not physical QA."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class HistoricalTwo07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=json.loads((ROOT/"docs/progress/v2-two07-cold-ownership-20261024.json").read_text())
        cls.prev=json.loads((ROOT/"docs/progress/v2-review-checkpoint-20261024T2008.json").read_text())
        cls.interval=json.loads((ROOT/"docs/progress/v2-review-interval-20261024T2010.json").read_text())
    def test_distinct_profile_cold_restart_earned_exactly_one_point(self):
        a=self.a
        self.assertEqual(a["criterion_id"],"TWO-07")
        self.assertEqual((a["before"],a["after"]),("unverified","bounded_verified"))
        self.assertEqual(a["delta_screened_pp"],1)
        self.assertEqual(a["delta_independently_reviewed_pp"],1)
        self.assertEqual(a["previous_screened_percent"],47)
        self.assertEqual(a["current_screened_percent"],48)
        self.assertEqual(a["previous_independently_reviewed_percent"],5)
        self.assertEqual(a["current_independently_reviewed_percent"],6)
        self.assertEqual(a["qa_release_delta"],0)
        self.assertEqual(a["USA_event_delta"],0)
    def test_qualified_windows_run_and_fixture_limit_explicit(self):
        a=self.a
        self.assertIn("https://github.com/gamesbyian/UR-Recomp/actions/runs/38522739830/job/115716339651",a["evidence"])
        self.assertIn("https://github.com/gamesbyian/UR-Recomp/pull/1510",a["evidence"])
        self.assertIn("fixture", " ".join(a["limits"]).lower())
        self.assertTrue(any("distinct" in x for x in a["qualified_observations"]))
        self.assertEqual(len(a["reviewed_main_sha"]),40)
    def test_interval_explains_prior_source_witness_not_current_qa08_patch(self):
        changes=self.interval["criterion_changes"]
        self.assertEqual([c["id"] for c in changes],["TWO-07"])
        self.assertEqual(self.interval["from_main_sha"],self.prev["at_main_sha"])
        self.assertEqual(self.interval["observed_merge_count"],1)
        self.assertEqual(self.interval["merge_records"][0]["pr"],2526)
        self.assertEqual(self.interval["formal_events_delta"],0)
        self.assertEqual(self.interval["formal_release_gates_delta"],0)

if __name__=="__main__":
    unittest.main()
