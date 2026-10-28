"""Beta-v3 reclassifies only final release signoff; zero manufactured progress."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools import atomic_progress_v2 as v2
from tools import atomic_progress_beta_v3 as v3


class BetaV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads(v3.SCOPE.read_text(encoding="utf-8"))
        cls.inventory = json.loads(v2.INV_PATH.read_text(encoding="utf-8"))
        cls.ledger = json.loads(v2.LEDGER_PATH.read_text(encoding="utf-8"))
        cls.pointer = json.loads(v3.POINTER.read_text(encoding="utf-8"))

    def result(self, scope=None, inv=None, ledger=None, pointer=None):
        return v3.score(scope if scope is not None else self.scope,
                        inv if inv is not None else self.inventory,
                        ledger if ledger is not None else self.ledger,
                        pointer if pointer is not None else self.pointer)

    def test_real_reviewed_snapshot_has_expected_exact_projection(self):
        result = self.result()
        self.assertEqual(result["schema"], "ur-playable-windows-beta-progress/3")
        self.assertEqual(result["source_reviewed_sha"],
                         "88056d491c77cc7bb14ef1635d81892ca0d70305")
        self.assertEqual(result["historical_v2_snapshot"]["bounded_percent"], 53.0)
        self.assertEqual(result["historical_v2_snapshot"]["independently_audited_percent"], 11.0)
        beta = result["beta"]
        self.assertEqual(beta["criteria"], 134)
        self.assertEqual(beta["denominator_units"], 4455)
        self.assertEqual(beta["bounded_verified_units"], 2385)
        self.assertEqual(beta["independently_audited_units"], 495)
        self.assertEqual(beta["bounded_percent"], 53.535)
        self.assertEqual(beta["independently_audited_percent"], 11.111)
        self.assertEqual(beta["excluded_release_only"], ["QA-09"])
        self.assertEqual(beta["by_group"]["FID"]["total"], 45)
        self.assertEqual(beta["by_group"]["QA"]["total"], 9)
        self.assertEqual(result["original_native_events"], {"accepted": 0, "required": 45})
        self.assertEqual(result["release_quality_separate"]["formal_release_gates_passed"], 0)
        self.assertFalse(result["new_engineering_work_claimed"])
        self.assertEqual(result["newly_admitted_criteria_claimed"], 0)
        self.assertTrue(result["denominator_reclassification_only"])

    def test_only_release_signoff_is_excluded(self):
        beta_rows = v3.validate_scope(self.scope, self.inventory["criteria"])
        old = {r["id"] for r in self.inventory["criteria"]}
        projected = {r["id"] for r in beta_rows}
        self.assertEqual(old - projected, {"QA-09"})
        self.assertEqual(len(projected), 134)
        for name in ("QA-02", "QA-03", "QA-04", "QA-05", "QA-06",
                     "QA-07", "QA-08", "QA-10", "WIDE-03", "WIDE-06",
                     "RECOVERY-09", "UX-04", "FID-01", "FID-45"):
            self.assertIn(name, projected)
        self.assertTrue(self.result()["release_quality_separate"]
                        ["three_environments_including_two_physical_pcs_still_release_required"])

    def test_scope_mutations_rejected(self):
        edits = [
            lambda x: x.update(schema="other"),
            lambda x: x.update(version="windows-beta-v2-candidate"),
            lambda x: x.update(base_inventory="docs/progress/fake.json"),
            lambda x: x.update(base_inventory_fingerprint="00000000"),
            lambda x: x.update(included_criterion_count=133),
            lambda x: x.update(fixed_denominator_units=4500),
            lambda x: x.update(projected_fingerprint="00000000"),
            lambda x: x.update(excluded_criteria=[]),
            lambda x: x["excluded_criteria"][0].update(id="QA-04"),
            lambda x: x["excluded_criteria"].append(deepcopy(x["excluded_criteria"][0])),
            lambda x: x.update(excluded_criteria_policy="exclude all QA"),
            lambda x: x.update(release_quality_policy="QA released automatically"),
            lambda x: x.update(independent_review_policy="agent self approval"),
            lambda x: x.update(caution=""),
            lambda x: x.update(extra="unreviewed field"),
        ]
        for edit in edits:
            with self.subTest(edit=repr(edit)):
                scope = deepcopy(self.scope)
                edit(scope)
                with self.assertRaises(ValueError):
                    self.result(scope=scope)

    def test_source_review_pointer_cannot_implicitly_follow_main(self):
        ptr = deepcopy(self.pointer)
        ptr["reviewed_main_sha"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "source"):
            self.result(pointer=ptr)
        ptr = deepcopy(self.pointer)
        ptr["interval"] = "unknown"
        with self.assertRaisesRegex(ValueError, "historical"):
            self.result(pointer=ptr)
        ptr = deepcopy(self.pointer)
        ptr["schema"] = "something-else"
        with self.assertRaises(ValueError):
            self.result(pointer=ptr)
        with self.assertRaises(ValueError):
            v2.require_reviewed_head(self.inventory, "f" * 40)

    def test_cannot_fake_usa_event_or_accept_a_release_gate(self):
        inv = deepcopy(self.inventory)
        inv["criteria"][-1]["status"] = "bounded_verified"
        with self.assertRaises(ValueError):
            self.result(inv=inv)
        inv = deepcopy(self.inventory)
        inv["criteria"][0]["status"] = "bounded_verified"
        inv["criteria"][0]["evidence"] = []
        with self.assertRaises(ValueError):
            self.result(inv=inv)
        inv = deepcopy(self.inventory)
        inv["criteria"][0]["audit_state"] = "independent_reviewed"
        inv["criteria"][0]["audit_receipt"] = "unknown"
        with self.assertRaises(ValueError):
            self.result(inv=inv)

    def test_legacy_v2_and_release_gate_source_untouched(self):
        v2_stats = v2.validate(self.inventory, self.ledger)
        actual = self.result()
        self.assertEqual(v2_stats["bounded_product_coverage_percent"], 53.0)
        self.assertEqual(v2_stats["independently_audited_coverage_percent"], 11.0)
        self.assertEqual(v2_stats["formal_windows_gates_passed"], 0)
        self.assertEqual(actual["release_quality_separate"]["legacy_qa09_status"],
                         "unverified")
        self.assertEqual(self.inventory["frozen_contract_fnv1a32"], "32c62b80")
        self.assertEqual(self.scope["projected_fingerprint"], "c231f49c")
        self.assertEqual(actual["beta"]["bounded_verified_units"],
                         v2_stats["bounded_product_coverage_percent"] * 45)

    def test_report_explicitly_refuses_invented_progress(self):
        md = v3.markdown(self.result())
        for fragment in ("53.535%", "53.000%", "11.111%",
                         "QA-09", "No new engineering points", "0/45",
                         "0/12", "three-machine", "source-reviewed"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, md)


if __name__ == "__main__":
    unittest.main()
