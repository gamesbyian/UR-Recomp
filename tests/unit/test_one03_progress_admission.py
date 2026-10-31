"""Frozen ONE-03 bounded admission must stay tied to real earned native evidence."""
import copy
import json
import unittest
from pathlib import Path

from tools.atomic_progress_v2 import validate
from tools.progress_interval_v2 import compare

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class One03ProgressAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = read("docs/progress/windows-beta-v2-inventory.json")
        cls.ledger = read("docs/RELEASE-QUALITY-LEDGER.json")
        cls.pointer = read("docs/progress/current-v2-review.json")
        cls.previous = read(cls.pointer["previous"])
        cls.interval = read(cls.pointer["interval"])
        cls.audit = read(cls.inventory["latest_criterion_review_ref"])

    def test_exact_bounded_criterion_and_source_bound_evidence(self):
        one = next(c for c in self.inventory["criteria"] if c["id"] == "ONE-03")
        self.assertEqual(one["criterion"], "Tour Next Event preserves completed results and progression")
        self.assertEqual((one["status"], one["audit_state"]),
                         ("bounded_verified", "independent_reviewed"))
        self.assertEqual(one["audit_receipt"], self.audit["independent_audit_receipt"])
        self.assertEqual(self.audit["reviewed_main_sha"], self.pointer["reviewed_main_sha"])
        self.assertEqual(self.audit["product_producer_sha"],
                         "39120bf875a1e8189e8043095987c57f00251c29")
        self.assertEqual(self.audit["hosted_run"]["url"],
                         "https://github.com/gamesbyian/UR-Recomp/actions/runs/41181847744")
        self.assertEqual(self.audit["hosted_run"]["native_executable_sha256"],
                         "fe138f713516cc6342619a618680d56cdf7bb4754a208305f62d3a9f7f7ccc19")
        record = self.audit["observed_native_product"]["second_saved_urrun"]
        self.assertEqual((record["bytes"], record["input_rows"], record["staged_replay_bytes"]),
                         (4847, 249, 2996))
        self.assertEqual(record["sha256"],
                         "912c17f7fc10bae9b5435994520800122126fdb1613a12b6c73d245c20690f24")
        self.assertTrue(self.audit["observed_native_product"]["saved_and_cold_sram"]["identical"])
        self.assertTrue(any("seeded" in x.lower() for x in self.audit["not_checked"]))
        self.assertTrue(any("Local Runs" in x for x in self.audit["not_checked"]))

    def test_only_one_retroactive_bounded_point_and_no_release_credit(self):
        result = compare(self.previous, self.inventory, self.ledger, self.interval,
                         self.pointer["reviewed_main_sha"])
        self.assertEqual((result["previous_product_percent"], result["current_product_percent"]),
                         (55, 56))
        self.assertEqual(result["current_independent_audit_percent"], 14)
        self.assertEqual(result["newly_verified"], ["ONE-03"])
        self.assertEqual(result["accepted_USA_events"], 0)
        self.assertEqual(result["passed_release_gates"], 0)
        self.assertGreater(result["unclassified_merge_count"], 0)
        self.assertEqual(self.interval["score"]["new_work_earned_percentage_points"], 0)
        self.assertEqual(self.interval["score"]["retroactive_identification_percentage_points"], 1)

    def test_missing_independent_receipt_fails_closed(self):
        broken = copy.deepcopy(self.inventory)
        next(c for c in broken["criteria"] if c["id"] == "ONE-03").pop("audit_receipt")
        with self.assertRaisesRegex(ValueError, "Independent audit"):
            validate(broken, self.ledger)

    def test_fabricated_usa_event_credit_fails_closed(self):
        broken = copy.deepcopy(self.interval)
        broken["formal_events_delta"] = 1
        with self.assertRaisesRegex(ValueError, "Unsubstantiated USA"):
            compare(self.previous, self.inventory, self.ledger, broken,
                    self.pointer["reviewed_main_sha"])


if __name__ == "__main__":
    unittest.main()
