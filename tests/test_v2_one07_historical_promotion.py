"""Historical stock Practice rematch promotion remains evidence-linked and versioned."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HistoricalOne07PromotionTests(unittest.TestCase):
    def test_historical_receipt_is_a_single_new_product_point(self):
        p = json.loads((ROOT/"docs/progress/v2-one07-rematch-promotion-20261024.json").read_text())
        self.assertEqual(p["criterion_id"],"ONE-07")
        self.assertEqual(p["prior_screened_coverage_percent"],46)
        self.assertEqual(p["new_screened_coverage_percent"],47)
        self.assertEqual(p["change_percentage_points"],1)
        self.assertEqual(p["before"],"unverified")
        self.assertEqual(p["after"],"bounded_verified")
        self.assertEqual(p["formal_qa_delta"],0)
        self.assertEqual(p["formal_usa_delta"],0)
        self.assertEqual(p["net_change_from_v2_initial_baseline_pp"],-3)
        self.assertEqual(len(p["reviewed_main_sha"]),40)

    def test_retained_pr_and_exact_head_win_native_provenance(self):
        p = json.loads((ROOT/"docs/progress/v2-one07-rematch-promotion-20261024.json").read_text())
        self.assertIn("https://github.com/gamesbyian/UR-Recomp/pull/2494",p["evidence"])
        self.assertIn("https://github.com/gamesbyian/UR-Recomp/actions/runs/40078888170",p["evidence"])
        self.assertIn("https://github.com/gamesbyian/UR-Recomp/actions/runs/40078888094",p["evidence"])
        self.assertEqual(p["audit_state"],"inherited_pr_screening")

if __name__=="__main__":
    unittest.main()
