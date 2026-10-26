import copy
import json
import unittest
from pathlib import Path
from tools.remaining_work_forecast import calculate

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/progress"

class RemainingWorkForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = json.loads((DOCS / "remaining-work-prior-v1.json").read_text())
        cls.inventory = json.loads((DOCS / "windows-beta-v2-inventory.json").read_text())
        cls.adjustments = json.loads((DOCS / "remaining-work-adjustments.json").read_text())

    def test_current_count_and_reproducible_bounds(self):
        one = calculate(self.prior, self.inventory, self.adjustments, samples=150, seed=15)
        two = calculate(self.prior, self.inventory, self.adjustments, samples=150, seed=15)
        self.assertEqual(one, two)
        outstanding = {c["id"] for c in self.inventory["criteria"]
                       if c["status"] != "bounded_verified"}
        self.assertEqual(one["product_criteria_remaining"], len(outstanding))
        self.assertEqual(one["unreviewed_provisional_criteria"],
                         sum(c["status"] == "bounded_verified" and
                             c["audit_state"] != "independent_reviewed"
                             for c in self.inventory["criteria"]))
        self.assertLessEqual(one["one_time_shared_tasks_remaining"], len(self.prior["shared"]))
        self.assertEqual(one["external_validation_dependencies_remaining"],
                         len(outstanding & set(self.prior["external_validation"])))
        self.assertLess(one["remaining_effort_p10"], one["remaining_effort_median"])
        self.assertLess(one["remaining_effort_median"], one["remaining_effort_p90"])
        self.assertIsNone(one["forecast_dates"])

    def test_completion_removes_one_marginal_task(self):
        inv = copy.deepcopy(self.inventory)
        base = calculate(self.prior, inv, self.adjustments, samples=200, seed=11)
        row = next((c for c in inv["criteria"] if c["status"] != "bounded_verified"
                    and c["area"] != "FID"), None)
        if row is None:
            self.skipTest("All non-event requirements complete")
        row["status"] = "bounded_verified"
        new = calculate(self.prior, inv, self.adjustments, samples=200, seed=11)
        self.assertEqual(new["product_criteria_remaining"],
                         base["product_criteria_remaining"] - 1)
        self.assertLess(new["expected_relative_work_units"], base["expected_relative_work_units"])

    def test_all_event_completions_remove_shared_parity_once(self):
        inv = copy.deepcopy(self.inventory)
        original = calculate(self.prior, inv, self.adjustments, samples=100, seed=1)
        affected = [row for row in inv["criteria"]
                    if (row["area"] == "FID" or
                        row["id"] in ("ONE-09","ONE-10","TWO-08")) and
                        row["status"] != "bounded_verified"]
        if not affected:
            self.skipTest("Common parity work already fully qualified")
        for row in affected:
            row["status"] = "bounded_verified"
        output = calculate(self.prior, inv, self.adjustments, samples=100, seed=1)
        self.assertEqual(output["one_time_shared_tasks_remaining"],
                         original["one_time_shared_tasks_remaining"] - 1)

    def test_unverified_external_is_never_implicitly_certified(self):
        output = calculate(self.prior, self.inventory, self.adjustments, samples=100)
        expected = sum(c["id"] in set(self.prior["external_validation"])
                       for c in self.inventory["criteria"]
                       if c["status"] != "bounded_verified")
        self.assertEqual(output["external_validation_dependencies_remaining"], expected)
        self.assertIn("no observed agent-hours", output["calibration_status"])

    def test_adjustments_need_source_and_cannot_target_closed(self):
        changes = copy.deepcopy(self.adjustments)
        remaining = next((c["id"] for c in self.inventory["criteria"]
                          if c["status"] != "bounded_verified"), None)
        if remaining is None:
            self.skipTest("Nothing left to estimate")
        changes["changes"].append({"id":remaining,"range":[0.5,1,3],
                                   "reason":"Independent review revised scope"})
        with self.assertRaisesRegex(ValueError, "evidence"):
            calculate(self.prior,self.inventory,changes,samples=100)
        changes["changes"][0]["evidence"]="https://github.com/gamesbyian/UR-Recomp/pull/2640"
        good = calculate(self.prior,self.inventory,changes,samples=100)
        self.assertEqual(good["product_criteria_remaining"],
                         sum(c["status"] != "bounded_verified" for c in self.inventory["criteria"]))
        finished = next((c["id"] for c in self.inventory["criteria"]
                         if c["status"] == "bounded_verified"), None)
        if finished is None:
            self.skipTest("No previously completed requirements")
        changes["changes"][0]["id"]=finished
        with self.assertRaisesRegex(ValueError, "completed"):
            calculate(self.prior,self.inventory,changes,samples=100)

    def test_independent_review_removes_only_audit_debt(self):
        inv = copy.deepcopy(self.inventory)
        row = next((c for c in inv["criteria"]
                    if c["status"] == "bounded_verified" and
                    c["audit_state"] != "independent_reviewed"), None)
        if row is None:
            self.skipTest("Every completed criterion is independently reviewed")
        before = calculate(self.prior, inv, self.adjustments, samples=200, seed=13)
        row["audit_state"] = "independent_reviewed"
        after = calculate(self.prior, inv, self.adjustments, samples=200, seed=13)
        self.assertEqual(after["product_criteria_remaining"], before["product_criteria_remaining"])
        self.assertEqual(after["unreviewed_provisional_criteria"],
                         before["unreviewed_provisional_criteria"] - 1)
        self.assertLess(after["expected_relative_work_units"], before["expected_relative_work_units"])

    def test_frozen_inventory_contract_required(self):
        inv = copy.deepcopy(self.inventory)
        inv["frozen_contract_fnv1a32"] = "bad"
        with self.assertRaisesRegex(ValueError, "contract"):
            calculate(self.prior,inv,self.adjustments,samples=100)

if __name__ == "__main__":
    unittest.main()
