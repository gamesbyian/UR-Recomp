import copy
import json
import unittest
from pathlib import Path
from tools.progress_receipt_ledger import apply_receipts

ROOT = Path(__file__).resolve().parents[2]
class IncrementalReceiptsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv=json.loads((ROOT/"docs/progress/windows-beta-v2-inventory.json").read_text())
        cls.ledger=json.loads((ROOT/"docs/RELEASE-QUALITY-LEDGER.json").read_text())
    def receipt(self, ident):
        return dict(schema="ur-progress-receipt/1", criterion_id=ident,
                    independent_reviewer="reviewer-other-than-author",
                    kind="new_implementation", rationale="Original exact evidence adjudicated",
                    evidence=["https://github.com/gamesbyian/UR-Recomp/pull/2893"],
                    audit_receipt="https://github.com/gamesbyian/UR-Recomp/actions/runs/41149867355")
    def test_unrelated_urls_and_claimed_reviewer_never_award_credit(self):
        before=self.inv
        target=next(x["id"] for x in before["criteria"]
                    if x["status"]=="unverified" and x["area"] not in ("FID",))
        result, pending=apply_receipts(before,self.ledger,[self.receipt(target)])
        self.assertEqual(len(pending),1)
        self.assertEqual(pending[0]["admission_status"],"pending_independent_review")
        from tools.atomic_progress_v2 import validate
        self.assertEqual(validate(result,self.ledger)["bounded_product_coverage_percent"],
                         validate(before,self.ledger)["bounded_product_coverage_percent"])
        self.assertEqual(validate(result,self.ledger)["formal_windows_gates_passed"],0)
        self.assertEqual(next(c for c in result["criteria"] if c["id"]==target)["status"],"unverified")
        self.assertEqual(before,result)
    def test_duplicate_and_unevidenced_rejected(self):
        target=next(c["id"] for c in self.inv["criteria"] if c["status"]=="unverified")
        x=self.receipt(target)
        with self.assertRaisesRegex(ValueError,"duplicate"):
            apply_receipts(self.inv,self.ledger,[x,x])
        x["evidence"]=[]
        with self.assertRaisesRegex(ValueError,"evidence"):
            apply_receipts(self.inv,self.ledger,[x])
    def test_no_duplicate_existing_and_no_fake_usa(self):
        existing=next(c["id"] for c in self.inv["criteria"] if c["status"]=="bounded_verified")
        usa=next(c["id"] for c in self.inv["criteria"] if c["area"]=="FID")
        with self.assertRaisesRegex(ValueError,"already verified"):
            apply_receipts(self.inv,self.ledger,[self.receipt(existing)])
        with self.assertRaisesRegex(ValueError,"USA complete-event"):
            apply_receipts(self.inv,self.ledger,[self.receipt(usa)])
if __name__ == "__main__":
    unittest.main()
