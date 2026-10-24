"""Audit recorded GitHub execution witnesses without confusing them with release gates."""
import json
import unittest
from pathlib import Path
from tools.progress_interval_v2 import compare

ROOT = Path(__file__).resolve().parents[1]
def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

class BoundedIndependentReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load("docs/progress/v2-independent-bounded-audit-20261024.json")
        cls.inv = load("docs/progress/windows-beta-v2-inventory.json")
        cls.prev = load("docs/progress/v2-review-checkpoint-20261024T1850.json")
        cls.interval = load("docs/progress/v2-review-interval-20261024T1916.json")
        cls.ledger = load("docs/RELEASE-QUALITY-LEDGER.json")

    def test_two_narrow_source_execution_receipts_promoted(self):
        audit = self.audit
        self.assertEqual({x["id"] for x in audit["changes"]}, {"WIN-03", "ONE-05"})
        for witness in audit["changes"]:
            row = next(x for x in self.inv["criteria"] if x["id"] == witness["id"])
            self.assertEqual(row["status"], "bounded_verified")
            self.assertEqual(row["audit_state"], "independent_reviewed")
            self.assertEqual(row["audit_receipt"], witness["independent_execution"].split("/job/")[0])
            self.assertTrue(witness["scope_limit"].strip())
            self.assertTrue(witness["outcome"])

    def test_no_release_or_product_score_inflation(self):
        result = compare(self.prev, self.inv, self.ledger, self.interval,
                         self.interval["through_main_sha"])
        self.assertEqual(result["current_product_percent"], 47)
        self.assertEqual(result["interval_product_delta_points"], 0)
        self.assertEqual(result["previous_independent_audit_percent"], 0)
        self.assertEqual(result["current_independent_audit_percent"], 2)
        self.assertEqual(result["passed_release_gates"], 0)
        self.assertEqual(result["accepted_USA_events"], 0)
        self.assertEqual(result["other_audit_transitions"], ["WIN-03", "ONE-05"])

    def test_log_specific_sources_are_retained(self):
        values = {x["id"]: x for x in self.audit["changes"]}
        self.assertEqual(values["WIN-03"]["outcome"]["machine_gl"], "refused version=1.1.0")
        self.assertEqual(values["WIN-03"]["outcome"]["forced_gl_1_1"], "refused_unavailable")
        self.assertEqual(values["ONE-05"]["outcome"]["marker"],
                         "UR_PRACTICE_TWO_REPEAT_CYCLES=passed course=0 results=2 repeats=2")

if __name__=="__main__":
    unittest.main()
