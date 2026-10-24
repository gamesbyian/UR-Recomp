import copy
import json
import unittest
from pathlib import Path
from tools.atomic_progress_delta import delta

ROOT=Path(__file__).resolve().parents[1]
class V2DeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv=json.loads((ROOT/"docs/progress/windows-beta-v2-inventory.json").read_text())
        cls.baseline=json.loads((ROOT/"docs/progress/windows-beta-v2-baseline.json").read_text())
        cls.ledger=json.loads((ROOT/"docs/RELEASE-QUALITY-LEDGER.json").read_text())
    def test_start_of_measurement_has_zero_point_delta(self):
        s=delta(self.inv,self.baseline,self.ledger)
        self.assertEqual(s["change_percentage_points"],0)
        self.assertEqual(s["current_provisional_coverage_percent"],50)
    def test_new_item_produces_measurable_gain(self):
        inv=copy.deepcopy(self.inv)
        c=next(x for x in inv["criteria"] if x["id"]=="ONE-03")
        c.update(status="bounded_verified",audit_state="inherited_pr_screening",
                 evidence=["https://github.com/gamesbyian/UR-Recomp/pull/1510"])
        s=delta(inv,self.baseline,self.ledger)
        self.assertEqual(s["change_percentage_points"],1)
        self.assertEqual(s["newly_verified_ids"],["ONE-03"])
    def test_retracted_item_is_negative(self):
        inv=copy.deepcopy(self.inv)
        c=next(x for x in inv["criteria"] if x["id"]=="ONE-01")
        c.update(status="regressed",audit_state="pending",evidence=[])
        s=delta(inv,self.baseline,self.ledger)
        self.assertEqual(s["change_percentage_points"],-1)
        self.assertEqual(s["regressed_or_retracted_ids"],["ONE-01"])
    def test_rewritten_baseline_refused(self):
        base=copy.deepcopy(self.baseline)
        base["provisional_coverage_percent"]=99
        with self.assertRaisesRegex(ValueError,"rewritten"):
            delta(self.inv,base,self.ledger)
if __name__=="__main__":
    unittest.main()
