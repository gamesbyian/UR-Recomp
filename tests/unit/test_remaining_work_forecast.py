import copy
import json
import unittest
from pathlib import Path
from tools.remaining_work_forecast import calculate

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/progress"

class ForecastContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads((DOCS / "remaining-work-prior-v1.json").read_text())
        cls.i = json.loads((DOCS / "windows-beta-v2-inventory.json").read_text())
        cls.a = json.loads((DOCS / "remaining-work-adjustments.json").read_text())

    def test_all_outstanding_and_review_debt_counted(self):
        s = calculate(self.p, self.i, self.a, samples=100)
        self.assertEqual(s["product_criteria_remaining"],
                         sum(x["status"] != "bounded_verified" for x in self.i["criteria"]))
        self.assertEqual(s["unreviewed_provisional_criteria"],
                         sum(x["status"] == "bounded_verified" and
                             x["audit_state"] != "independent_reviewed" for x in self.i["criteria"]))
        self.assertIsNone(s["forecast_dates"])

    def test_new_independent_review_reduces_remaining_effort(self):
        d = copy.deepcopy(self.i)
        pending = next((x for x in d["criteria"] if x["status"] == "bounded_verified"
                        and x["audit_state"] != "independent_reviewed"), None)
        if pending is None:
            self.skipTest("No independent review debt")
        before = calculate(self.p, d, self.a, samples=100)
        pending["audit_state"] = "independent_reviewed"
        after = calculate(self.p, d, self.a, samples=100)
        self.assertEqual(before["product_criteria_remaining"], after["product_criteria_remaining"])
        self.assertLess(after["expected_relative_work_units"], before["expected_relative_work_units"])

if __name__ == "__main__":
    unittest.main()
