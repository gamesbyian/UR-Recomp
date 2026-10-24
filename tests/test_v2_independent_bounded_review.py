"""Audit recorded GitHub execution witnesses without confusing them with release gates."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

class BoundedIndependentReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load("docs/progress/v2-independent-bounded-audit-20261024.json")

    def test_two_narrow_source_execution_receipts_promoted(self):
        audit = self.audit
        self.assertEqual({x["id"] for x in audit["changes"]}, {"WIN-03", "ONE-05"})
        for witness in audit["changes"]:
            self.assertIn("/job/", witness["independent_execution"])
            self.assertEqual(witness["audit_state"], "independent_reviewed")
            self.assertTrue(witness["scope_limit"].strip())
            self.assertTrue(witness["outcome"])

    def test_historical_audit_never_claimed_release_or_new_feature_points(self):
        self.assertEqual(self.audit["before"]["bounded_coverage_percent"], 47)
        self.assertEqual(self.audit["after"]["bounded_coverage_percent"], 47)
        self.assertEqual(self.audit["before"]["independently_audited_percent"], 0)
        self.assertEqual(self.audit["after"]["independently_audited_percent"], 2)
        self.assertEqual(self.audit["after"]["USA_events"], 0)
        self.assertEqual(self.audit["after"]["Windows_gates"], 0)

    def test_log_specific_sources_are_retained(self):
        values = {x["id"]: x for x in self.audit["changes"]}
        self.assertEqual(values["WIN-03"]["outcome"]["machine_gl"], "refused version=1.1.0")
        self.assertEqual(values["WIN-03"]["outcome"]["forced_gl_1_1"], "refused_unavailable")
        self.assertEqual(values["ONE-05"]["outcome"]["marker"],
                         "UR_PRACTICE_TWO_REPEAT_CYCLES=passed course=0 results=2 repeats=2")

if __name__=="__main__":
    unittest.main()
