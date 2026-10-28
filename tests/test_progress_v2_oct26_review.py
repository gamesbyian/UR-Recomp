"""Source-bound v2 acceptance: preserve historical October 26 audit and current reviewed interval."""
import json
import unittest
from pathlib import Path

from tools.atomic_progress_v2 import validate, require_reviewed_head
from tools.atomic_progress_delta import delta

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs/progress"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ReviewedProgressCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = read("docs/progress/windows-beta-v2-inventory.json")
        cls.ledger = read("docs/RELEASE-QUALITY-LEDGER.json")
        cls.baseline = read("docs/progress/windows-beta-v2-baseline.json")
        cls.pointer = read("docs/progress/current-v2-review.json")
        cls.interval = read(cls.pointer["interval"])
        cls.previous = read(cls.pointer["previous"])
        cls.historical_oct26 = read("docs/progress/v2-review-interval-20261026T2253.json")
        cls.historical_recovery = read("docs/progress/v2-review-interval-20261028T0010.json")

    def test_review_pointer_is_pinned_to_same_source(self):
        self.assertEqual(self.pointer["reviewed_main_sha"], self.interval["through_main_sha"])
        require_reviewed_head(self.inv, self.pointer["reviewed_main_sha"])
        self.assertEqual(self.pointer["previous"], "docs/progress/v2-review-checkpoint-20261028T0010.json")
        self.assertEqual(self.previous["at_main_sha"], self.interval["from_main_sha"])
        self.assertEqual(len(self.previous["criteria"]), 135)
        # Inventory latest-review links must match the independently reviewed pointer.
        self.assertEqual(self.inv["latest_review_interval"], self.pointer["interval"])
        audit = read(self.inv["latest_criterion_review_ref"])
        self.assertEqual(audit["criterion_id"], "TWO-05")
        self.assertEqual(audit["reviewed_main_sha"], self.pointer["reviewed_main_sha"])
        self.assertEqual(audit["independent_audit_receipt"],
                         next(c for c in self.inv["criteria"] if c["id"] == "TWO-05")["audit_receipt"])

    def test_frozen_criterion_contract_and_release_gates_unchanged(self):
        s = validate(self.inv, self.ledger)
        self.assertEqual(s["bounded_product_coverage_percent"], 52)
        self.assertEqual(s["independently_audited_coverage_percent"], 10)
        self.assertEqual(s["formal_windows_gates_passed"], 0)
        self.assertEqual(s["independent_USA_complete_events"], 0)
        self.assertEqual(len(self.inv["criteria"]), 135)

    def test_oct26_earned_ids_remain_historical_and_recovery_is_distinct(self):
        self.assertEqual({x["id"] for x in self.historical_oct26["criterion_changes"]},
                         {"ONE-08", "ART-01"})
        one = next(x for x in self.inv["criteria"] if x["id"] == "ONE-08")
        art = next(x for x in self.inv["criteria"] if x["id"] == "ART-01")
        self.assertEqual(one["status"], "bounded_verified")
        self.assertEqual(art["audit_state"], "independent_reviewed")
        self.assertIn("/actions/runs/40161080894/job/121072588296", one["audit_receipt"])
        self.assertIn("HD-RACER-CHARACTER-RECONSTRUCTION.md", art["audit_receipt"])
        self.assertEqual(self.historical_oct26["score"]["new_work_earned_percentage_points"], 1)
        self.assertEqual(self.historical_oct26["score"]["retroactive_identification_percentage_points"], 1)
        self.assertEqual({x["id"] for x in self.historical_recovery["criterion_changes"]}, {"RECOVERY-10"})
        self.assertEqual({x["id"] for x in self.interval["criterion_changes"]}, {"TWO-05"})
        recovery = next(x for x in self.inv["criteria"] if x["id"] == "RECOVERY-10")
        self.assertEqual(recovery["status"], "bounded_verified")
        self.assertEqual(recovery["audit_state"], "independent_reviewed")
        two = next(x for x in self.inv["criteria"] if x["id"] == "TWO-05")
        self.assertEqual((two["status"], two["audit_state"]), ("bounded_verified", "independent_reviewed"))
        self.assertIn("6460996972", two["audit_receipt"])
        self.assertIn("6455893041", recovery["audit_receipt"])
        self.assertEqual(self.interval["score"]["new_work_earned_percentage_points"], 0)
        self.assertEqual(self.interval["score"]["retroactive_identification_percentage_points"], 1)
        self.assertEqual(self.previous["at_main_sha"], "afbf60fdb670e561b8ea2a2f882cd7277973b29b")

    def test_delta_preserves_baseline_and_reports_only_actual_change(self):
        report = delta(self.inv, self.baseline, self.ledger)
        self.assertEqual(report["current_provisional_coverage_percent"], 52)
        self.assertEqual(report["change_percentage_points"], 2)
        for key in ("ONE-08", "ART-01", "RECOVERY-10", "TWO-05"):
            self.assertIn(key, report["newly_verified_ids"])
        self.assertGreater(len(report["regressed_or_retracted_ids"]), 0)


if __name__ == "__main__":
    unittest.main()
