"""Source-bound acceptance audit: catch stale pointer and unverifiable invented score gains."""
import json
import unittest
from pathlib import Path

from tools.atomic_progress_v2 import validate, require_reviewed_head
from tools.atomic_progress_delta import delta

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"docs/progress"

class ReviewedProgressCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv=json.loads((DIR/"windows-beta-v2-inventory.json").read_text())
        cls.ledger=json.loads((ROOT/"docs/RELEASE-QUALITY-LEDGER.json").read_text())
        cls.baseline=json.loads((DIR/"windows-beta-v2-baseline.json").read_text())
        cls.pointer=json.loads((DIR/"current-v2-review.json").read_text())
        cls.interval=json.loads((DIR/"v2-review-interval-20261026T2253.json").read_text())

    def test_review_pointer_is_pinned_to_same_source(self):
        self.assertEqual(self.pointer["reviewed_main_sha"],self.interval["through_main_sha"])
        require_reviewed_head(self.inv,self.pointer["reviewed_main_sha"])
        self.assertEqual(self.pointer["interval"],"docs/progress/v2-review-interval-20261026T2253.json")

    def test_exact_reviewed_criterion_names_and_weights_are_unchanged(self):
        s=validate(self.inv,self.ledger)
        self.assertEqual(s["bounded_product_coverage_percent"],50)
        self.assertEqual(s["independently_audited_coverage_percent"],8)
        self.assertEqual(s["formal_windows_gates_passed"],0)
        self.assertEqual(s["independent_USA_complete_events"],0)
        self.assertEqual(len(self.inv["criteria"]),135)

    def test_two_earned_ids_are_supported_and_decomposed(self):
        self.assertEqual({x["id"] for x in self.interval["criterion_changes"]},{"ONE-08","ART-01"})
        one=next(x for x in self.inv["criteria"] if x["id"]=="ONE-08")
        art=next(x for x in self.inv["criteria"] if x["id"]=="ART-01")
        self.assertEqual(one["status"],"bounded_verified")
        self.assertEqual(art["audit_state"],"independent_reviewed")
        self.assertIn("/actions/runs/40161080894/job/121072588296",one["audit_receipt"])
        self.assertIn("HD-RACER-CHARACTER-RECONSTRUCTION.md",art["audit_receipt"])
        self.assertEqual(self.interval["score"]["new_work_earned_percentage_points"],1)
        self.assertEqual(self.interval["score"]["retroactive_identification_percentage_points"],1)
        self.assertEqual(self.interval["score"]["gross_delta_percentage_points"],2)

    def test_delta_is_exact_and_preserves_all_prior_baseline(self):
        report=delta(self.inv,self.baseline,self.ledger)
        self.assertEqual(report["current_provisional_coverage_percent"],50)
        self.assertEqual(report["change_percentage_points"],0)  # 50 original v2 baseline
        self.assertIn("ONE-08",report["newly_verified_ids"])
        self.assertIn("ART-01",report["newly_verified_ids"])
        self.assertGreater(len(report["regressed_or_retracted_ids"]),0)

if __name__=="__main__":
    unittest.main()
