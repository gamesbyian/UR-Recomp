"""Historical v2 screening reconciliation must not block subsequent real progress."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class InitialV2ScreeningAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((ROOT/"docs/progress/v2-screening-audit-20261024.json").read_text(encoding="utf-8"))
        cls.baseline = json.loads((ROOT/"docs/progress/windows-beta-v2-baseline.json").read_text(encoding="utf-8"))

    def test_complete_original_fifty_claim_audit(self):
        audit = self.audit
        rows = audit["rows"]
        self.assertEqual(audit["total_original_screened"], 50)
        self.assertEqual(len(rows), 50)
        self.assertEqual({x["id"] for x in rows}, set(self.baseline["verified_ids"]))
        self.assertEqual(len({x["id"] for x in rows}), 50)
        self.assertEqual(audit["withdrawn_ids"],
                         [x["id"] for x in rows if x["result"] == "withheld"])
        self.assertEqual(audit["relinked_ids"],
                         [x["id"] for x in rows if x["result"] == "source_relinked"])
        self.assertEqual(audit["retained_ids"],
                         [x["id"] for x in rows if x["result"] == "screened_retained"])

    def test_negative_score_is_explicit(self):
        self.assertEqual(set(self.audit["withdrawn_ids"]),
                         {"MENU-01", "UX-04", "DATA-05", "TWO-05"})
        self.assertEqual(self.audit["original_score_percent"], 50)
        self.assertEqual(self.audit["current_screened_score_percent"], 46)
        self.assertEqual(self.audit["delta_pp"], -4)
        self.assertEqual(self.audit["independently_audited_score_percent"], 0)

    def test_correction_receipts_and_reopening_rationale(self):
        for row in self.audit["rows"]:
            self.assertTrue(row["original_evidence"])
            self.assertIsInstance(row["reason"], str)
            self.assertTrue(row["reason"].strip())
            if row["result"] == "withheld":
                self.assertEqual(row["new_status"], "unverified")
                self.assertEqual(row["review_evidence"], [])
            else:
                self.assertEqual(row["new_status"], "bounded_verified")
                self.assertTrue(row["review_evidence"])

if __name__ == "__main__":
    unittest.main()
