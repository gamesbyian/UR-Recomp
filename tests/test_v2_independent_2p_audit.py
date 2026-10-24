"""Independent 2P native Win32 source-run review, not full original parity or QA."""
import json
import unittest
from pathlib import Path
from tools.progress_interval_v2 import compare

ROOT=Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

class IndependentTwoPlayerEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=load("docs/progress/v2-independent-2p-audit-20261024.json")
        cls.previous=load("docs/progress/v2-review-checkpoint-20261024T1916.json")
        cls.interval=load("docs/progress/v2-review-interval-20261024T1924.json")
        cls.inventory=load("docs/progress/windows-beta-v2-inventory.json")
        cls.ledger=load("docs/RELEASE-QUALITY-LEDGER.json")

    def test_original_win32_three_distinct_source_witnesses(self):
        self.assertEqual({x["id"] for x in self.audit["changes"]},
                         {"TWO-01","TWO-02","TWO-03"})
        for item in self.audit["changes"]:
            self.assertIn("/actions/runs/38522739830/job/115716339651",
                          item["independent_execution"])
            self.assertTrue(item["scope_limit"])
            self.assertTrue(item["outcome"])

    def test_independent_review_changes_only_audit_score(self):
        result=compare(self.previous,self.inventory,self.ledger,
                       self.interval,self.interval["through_main_sha"])
        self.assertEqual(result["previous_product_percent"],47)
        self.assertEqual(result["current_product_percent"],47)
        self.assertEqual(result["interval_product_delta_points"],0)
        self.assertEqual(result["previous_independent_audit_percent"],2)
        self.assertEqual(result["current_independent_audit_percent"],5)
        self.assertEqual(set(result["other_audit_transitions"]),
                         {"TWO-01","TWO-02","TWO-03"})
        self.assertEqual(result["passed_release_gates"],0)
        self.assertEqual(result["accepted_USA_events"],0)

    def test_historical_2p_producer_does_not_claim_physical_pads(self):
        audited=self.audit
        self.assertEqual(audited["before"]["bounded_coverage_percent"],
                         audited["after"]["bounded_coverage_percent"])
        self.assertEqual(audited["after"]["independently_audited_percent"],5)
        self.assertEqual(audited["after"]["Windows_gates"],0)
        self.assertEqual(audited["after"]["USA_events"],0)
        self.assertFalse("physical" in audited["review_method"].lower() and
                         "accepted" in audited["review_method"].lower())

if __name__=="__main__":
    unittest.main()
