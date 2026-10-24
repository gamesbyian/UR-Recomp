"""Interval progress reports must preserve real before/after and refuse silent status award."""
import copy
import json
import unittest
from pathlib import Path
from tools.progress_interval_v2 import compare

ROOT = Path(__file__).resolve().parents[1]
class ProgressIntervalV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(p):
            return json.loads((ROOT/p).read_text(encoding="utf-8"))
        cls.prev = read("docs/progress/v2-review-checkpoint-20261024T1708.json")
        cls.inv = read("docs/progress/windows-beta-v2-inventory.json")
        cls.ledger = read("docs/RELEASE-QUALITY-LEDGER.json")
        cls.interval = read("docs/progress/v2-review-interval-20261024T1850.json")
        cls.sha = cls.interval["through_main_sha"]
    def score(self, previous=None, inventory=None, ledger=None, interval=None, sha=None):
        return compare(previous if previous is not None else self.prev,
                       inventory if inventory is not None else self.inv,
                       ledger if ledger is not None else self.ledger,
                       interval if interval is not None else self.interval,
                       sha if sha is not None else self.sha)
    def test_current_interval_score_and_distinct_work_mix(self):
        r = self.score()
        self.assertEqual(r["previous_product_percent"],47)
        self.assertEqual(r["current_product_percent"],47)
        self.assertEqual(r["interval_product_delta_points"],0)
        self.assertEqual(r["reviewed_merge_count"],4)
        self.assertEqual(r["merged_work_mix"],{"direct_product":2,"release_risk_reduction":2})
        self.assertEqual(r["accepted_USA_events"],0)
        self.assertEqual(r["passed_release_gates"],0)
        self.assertEqual(r["newly_verified"],[])
    def test_stale_review_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,"STALE"):
            self.score(sha="a"*40)
    def test_new_unreported_criterion_promotion_rejected(self):
        inv=copy.deepcopy(self.inv)
        row=next(c for c in inv["criteria"] if c["id"]=="ONE-03")
        row["status"]="bounded_verified"
        row["audit_state"]="inherited_pr_screening"
        row["evidence"]=["https://github.com/gamesbyian/UR-Recomp/pull/2494"]
        with self.assertRaisesRegex(ValueError,"Undocumented"):
            self.score(inventory=inv)
    def test_declared_promotion_awards_one_point(self):
        inv=copy.deepcopy(self.inv)
        row=next(c for c in inv["criteria"] if c["id"]=="ONE-03")
        row["status"]="bounded_verified"
        row["audit_state"]="inherited_pr_screening"
        row["evidence"]=["https://github.com/gamesbyian/UR-Recomp/pull/2494"]
        interval=copy.deepcopy(self.interval)
        interval["criterion_changes"].append({
            "id":"ONE-03","before":"unverified","after":"bounded_verified",
            "audit_before":"pending","audit_after":"inherited_pr_screening",
            "evidence":["https://github.com/gamesbyian/UR-Recomp/pull/2494"],
            "reason":"Positive fixture: verified hypothetical complete requirement, not a production claim"})
        r=self.score(inventory=inv, interval=interval)
        self.assertEqual(r["interval_product_delta_points"],1.0)
        self.assertEqual(r["newly_verified"],["ONE-03"])
    def test_positive_gate_counter_without_formal_delta_rejected(self):
        ledger=copy.deepcopy(self.ledger)
        next(x for x in ledger["gates"] if x["id"]=="QA-04")["status"]="passed"
        with self.assertRaisesRegex(ValueError,"QA acceptance"):
            self.score(ledger=ledger)
    def test_duplicate_pr_receipt_rejected(self):
        interval=copy.deepcopy(self.interval)
        interval["merge_records"][1]["pr"]=interval["merge_records"][0]["pr"]
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            self.score(interval=interval)
    def test_interval_gap_rejected(self):
        interval=copy.deepcopy(self.interval)
        interval["from_main_sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"Gap or overlap"):
            self.score(interval=interval)
    def test_changed_claim_requires_signed_record(self):
        inv=copy.deepcopy(self.inv)
        row=next(c for c in inv["criteria"] if c["id"]=="ONE-07")
        row["status"]="regressed"
        row["audit_state"]="pending"
        with self.assertRaisesRegex(ValueError,"Undocumented"):
            self.score(inventory=inv)
if __name__=="__main__":
    unittest.main()
