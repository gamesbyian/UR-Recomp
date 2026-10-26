import copy
import json
import unittest
from pathlib import Path
from tools.remaining_work_forecast import calculate

D = Path(__file__).resolve().parents[2] / "docs/progress"

class ForecastSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads((D / "remaining-work-prior-v1.json").read_text())
        cls.i = json.loads((D / "windows-beta-v2-inventory.json").read_text())
        cls.a = json.loads((D / "remaining-work-adjustments.json").read_text())

    def test_seed_reproducibility(self):
        self.assertEqual(calculate(self.p,self.i,self.a,samples=100,seed=8),
                         calculate(self.p,self.i,self.a,samples=100,seed=8))

    def test_wrong_contract_refused(self):
        x = copy.deepcopy(self.i)
        x["frozen_contract_fnv1a32"] = "wrong"
        with self.assertRaisesRegex(ValueError,"contract"):
            calculate(self.p,x,self.a,samples=100)

    def test_evidence_required_for_adjusting_remaining_work(self):
        a = copy.deepcopy(self.a)
        key = next(c["id"] for c in self.i["criteria"] if c["status"] != "bounded_verified")
        a["changes"] = [{"id":key,"range":[1,2,4],"reason":"Changed after actual source review"}]
        with self.assertRaisesRegex(ValueError,"evidence"):
            calculate(self.p,self.i,a,samples=100)

    def test_shared_parity_depends_on_remaining_items(self):
        d=copy.deepcopy(self.i)
        before=calculate(self.p,d,self.a,samples=100)
        for c in d["criteria"]:
            if c["area"]=="FID" or c["id"] in ("ONE-09","ONE-10","TWO-08"):
                c["status"]="bounded_verified"
        after=calculate(self.p,d,self.a,samples=100)
        self.assertLessEqual(after["one_time_shared_tasks_remaining"],
                             before["one_time_shared_tasks_remaining"])
if __name__=="__main__":
    unittest.main()
