import copy
import json
import unittest
from pathlib import Path

from tools.atomic_progress_v2 import validate

ROOT = Path(__file__).resolve().parents[1]
class AtomicV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads((ROOT / "docs/progress/windows-beta-v2-inventory.json").read_text())
        cls.baseline = json.loads((ROOT / "docs/progress/windows-beta-v2-baseline.json").read_text())
        cls.ledger = json.loads((ROOT / "docs/RELEASE-QUALITY-LEDGER.json").read_text())

    def test_initial_verified_maturity_is_reproducible_and_distinct(self):
        score = validate(self.inventory, self.ledger)
        self.assertEqual(score["total_criteria"], 135)
        self.assertEqual(score["weight_units_total"], 4500)
        self.assertEqual(self.baseline["provisional_coverage_percent"], 50.0)
        self.assertGreaterEqual(score["independently_audited_coverage_percent"], 0)
        self.assertGreaterEqual(score["formal_windows_gates_passed"], 0)
        self.assertGreaterEqual(score["independent_USA_complete_events"], 0)
        self.assertEqual(len(self.baseline["verified_ids"]), 50)
        self.assertTrue(set(self.baseline["verified_ids"]).issubset({c["id"] for c in self.inventory["criteria"]}))

    def test_one_individually_evidenced_criterion_adds_one_point(self):
        inv = copy.deepcopy(self.inventory)
        row = next(x for x in inv["criteria"] if x["id"] == "ONE-03")
        row.pop("audit_receipt", None)
        row["status"] = "unverified"
        row["audit_state"] = "pending"
        row["evidence"] = []
        before = validate(inv, self.ledger)["bounded_product_coverage_percent"]
        row["status"] = "bounded_verified"
        row["audit_state"] = "inherited_pr_screening"
        row["evidence"] = ["https://github.com/gamesbyian/UR-Recomp/pull/1234"]
        self.assertEqual(validate(inv, self.ledger)["bounded_product_coverage_percent"], before + 1.0)

    def test_fidelity_acceptance_awards_only_one_forty_fifth_of_ten_points(self):
        inv = copy.deepcopy(self.inventory)
        ledger = copy.deepcopy(self.ledger)
        for other in inv["criteria"]:
            if other["area"] == "FID":
                other.update(status="unverified", audit_state="pending", evidence=[], course_event_key=None)
                other.pop("audit_receipt", None)
        next(x for x in ledger["gates"] if x["id"] == "QA-01")["coverage"]["complete_event_passes"] = 0
        before = validate(inv, ledger)["bounded_product_coverage_percent"]
        row = next(x for x in inv["criteria"] if x["id"] == "FID-01")
        row.update(status="bounded_verified", audit_state="independent_reviewed",
                   audit_receipt="https://github.com/gamesbyian/UR-Recomp/issues/967",
                   evidence=["https://github.com/gamesbyian/UR-Recomp/issues/967"],
                   course_event_key="test-fixture-event")
        next(x for x in ledger["gates"] if x["id"] == "QA-01")["coverage"]["complete_event_passes"] = 1
        score = validate(inv, ledger)
        self.assertEqual(score["bounded_product_coverage_percent"], round(before + 10 * 100 / 4500, 3))
        self.assertGreaterEqual(score["independently_audited_coverage_percent"], 0.222)

    def test_denominator_and_criterion_rewording_rejected(self):
        inv = copy.deepcopy(self.inventory)
        inv["criteria"][0]["criterion"] += " loosened"
        with self.assertRaisesRegex(ValueError, "Frozen criterion"):
            validate(inv, self.ledger)
        inv = copy.deepcopy(self.inventory)
        inv["criteria"][0]["weight_units"] += 1
        with self.assertRaises(ValueError):
            validate(inv, self.ledger)

    def test_fake_qa_acceptance_rejected(self):
        inv = copy.deepcopy(self.inventory)
        inv["criteria"][-1].pop("audit_receipt", None)
        inv["criteria"][-1].update(status="bounded_verified", audit_state="pending", evidence=[])
        with self.assertRaises(ValueError):
            validate(inv, self.ledger)
        inv = copy.deepcopy(self.inventory)
        ledger = copy.deepcopy(self.ledger)
        qa = next(x for x in ledger["gates"] if x["id"] == "QA-01")
        current = qa["coverage"]["complete_event_passes"]
        qa["coverage"]["complete_event_passes"] = current + 1 if current < 45 else current - 1
        with self.assertRaisesRegex(ValueError, "must exactly match"):
            validate(inv, ledger)

    def test_fidelity_cannot_claim_unsourced_duplicate_event(self):
        inv = copy.deepcopy(self.inventory)
        row = next(x for x in inv["criteria"] if x["id"] == "FID-01")
        row.pop("audit_receipt", None)
        row.update(status="bounded_verified", audit_state="inherited_pr_screening",
                   evidence=["https://github.com/gamesbyian/UR-Recomp/pull/1510"], course_event_key="x")
        with self.assertRaisesRegex(ValueError, "USA course admission"):
            validate(inv, self.ledger)

    def test_unverified_acceptance_flag_rejected(self):
        inv = copy.deepcopy(self.inventory)
        inv["criteria"][0].pop("audit_receipt", None)
        inv["criteria"][0].update(audit_state="independent_reviewed")
        with self.assertRaisesRegex(ValueError,"separate audit receipt"):
            validate(inv, self.ledger)

if __name__ == "__main__":
    unittest.main()
