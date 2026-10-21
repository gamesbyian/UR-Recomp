"""Fail-closed acceptance *coverage* inventory; synthetic tampering cannot approve art."""
import copy
import json
from pathlib import Path
import unittest

from tools import qa_modern_visual_case_coverage as coverage


class ModernVisualCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix=json.loads(Path("analysis/modern-visual-acceptance-matrix.json").read_text())
        cls.evidence=json.loads(Path("analysis/evidence/modern-visual-integrated-final-sdl-21cases-20261021.json").read_text())

    def test_real_21_capture_cohort_yields_no_formal_approval(self):
        r=coverage.reconcile(self.matrix,self.evidence)
        self.assertEqual(r["required_cases"],25)
        self.assertEqual(r["exact_geometry_route_technical_candidates"],5)
        self.assertEqual(r["related_partial_evidence_only"],9)
        self.assertEqual(r["remaining_without_corresponding_case_evidence"],11)
        self.assertEqual(r["formal_visual_accepted"],0)
        self.assertEqual(r["release_gate_credit"],0)
        self.assertTrue(all(not row["formal_visual_accepted"] and
                            not row["human_approved"] and
                            not row["hardware_approved"]
                            for row in r["cases"]))

    def test_wrong_native_capture_geometry_must_not_be_credit(self):
        e=copy.deepcopy(self.evidence)
        for row in e["cases"]:
            if row["route"]=="root-quit" and row["output"]=="1024x768":
                row["output"]="1280x720"
        with self.assertRaisesRegex(ValueError,"frozen native capture"):
            coverage.reconcile(self.matrix,e)

    def test_wrong_semantic_route_not_sufficient(self):
        e=copy.deepcopy(self.evidence)
        for row in e["cases"]:
            if row["route"]=="options-p1":
                row["route"]="root-quit"
        with self.assertRaisesRegex(ValueError,"frozen native capture"):
            coverage.reconcile(self.matrix,e)

    def test_failed_original_png_byte_identity_rejected(self):
        e=copy.deepcopy(self.evidence)
        e["cases"][0]["actual_native_P7_png_RGBA_byte_equal"]=False
        with self.assertRaisesRegex(ValueError,"qualified 21-case"):
            coverage.reconcile(self.matrix,e)

    def test_malformed_or_truncated_matrix_is_refused(self):
        m=copy.deepcopy(self.matrix)
        m["cases"].pop()
        with self.assertRaisesRegex(ValueError,"25 canonical"):
            coverage.reconcile(m,self.evidence)

    def test_source_approval_cannot_be_inferred_from_capture_volume(self):
        r=coverage.reconcile(self.matrix,self.evidence)
        for item in r["cases"]:
            self.assertEqual(item["release_gate_credit"],0)
            self.assertFalse(item["formal_visual_accepted"])
        self.assertFalse(r["physical_device_approved"])


    def test_unqualified_source_or_executable_binding_is_rejected(self):
        for flag in ("source_sha_exact", "exe_sha_exact"):
            with self.subTest(flag=flag):
                e=copy.deepcopy(self.evidence)
                e["cases"][0][flag]=False
                with self.assertRaisesRegex(ValueError,"source/PE-bound"):
                    coverage.reconcile(self.matrix,e)
            with self.subTest(flag=flag+" missing"):
                e=copy.deepcopy(self.evidence)
                del e["cases"][0][flag]
                with self.assertRaisesRegex(ValueError,"source/PE-bound"):
                    coverage.reconcile(self.matrix,e)

    def test_non_candidate_capture_route_and_geometry_are_frozen(self):
        # Swapping Authentic, noncandidate keyboard and title receipts must
        # never be hidden by the five headline acceptance candidates.
        for index, key, wrong in ((2, "route", "records-keyboard"),
                                  (5, "output", "1024x768"),
                                  (7, "route", "root-quit")):
            with self.subTest(index=index, key=key):
                e=copy.deepcopy(self.evidence)
                e["cases"][index][key]=wrong
                with self.assertRaisesRegex(ValueError,"frozen native capture"):
                    coverage.reconcile(self.matrix,e)

    def test_original_capture_ids_cannot_be_duplicated(self):
        e=copy.deepcopy(self.evidence)
        # Duplicate a noncandidate route so the five technical candidates
        # would still have passed the previous geometry/route-only reconciler.
        e["cases"][4]["id"]=e["cases"][5]["id"]
        with self.assertRaisesRegex(ValueError,"duplicate or missing"):
            coverage.reconcile(self.matrix,e)

    def test_historical_run_cannot_be_relabeled_as_another_binary(self):
        for key,value in (
            ("merge_checkout_sha", "0"*40),
            ("win32_conclusion", "failure"),
            ("id", 1),
        ):
            with self.subTest(key=key):
                e=copy.deepcopy(self.evidence)
                e["run"][key]=value
                with self.assertRaisesRegex(ValueError,"source/PE/run identity"):
                    coverage.reconcile(self.matrix,e)
        e=copy.deepcopy(self.evidence)
        e["run"]["executable"]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"source/PE/run identity"):
            coverage.reconcile(self.matrix,e)

    def test_approval_or_log_count_overclaim_rejected(self):
        for key,value in (
            ("actual_human_visual_signoffs",1),
            ("release_gate_credit",1),
            ("successful_process_logs",20),
            ("original_native_capture_receipts",20),
        ):
            with self.subTest(key=key):
                e=copy.deepcopy(self.evidence)
                e["counts"][key]=value
                with self.assertRaisesRegex(ValueError,"count/approval mismatch"):
                    coverage.reconcile(self.matrix,e)

    def test_unknown_25th_matrix_case_cannot_silently_replace_real_case(self):
        m=copy.deepcopy(self.matrix)
        # Previously 25 distinct IDs plus the five CASE_MAP IDs sufficed.
        # Removing a missing-evidence case went unnoticed.
        m["cases"][-1]["id"]="invented-layout-approval"
        with self.assertRaisesRegex(ValueError,"25 canonical"):
            coverage.reconcile(m,self.evidence)

    def test_uncredited_matrix_input_state_and_pixels_stay_frozen(self):
        # The older five geometry candidates were already protected. These
        # uncovered cases must not quietly change their QA requirements
        # merely because no screenshot currently satisfies them.
        for cid, key, incorrect in (
            ("title-wide-keyboard", "input", "pad-p1"),
            ("root-wide-4k-virtual", "pixels", [1920, 1080]),
            ("root-keyboard", "input", "pad-p1"),
            ("root-disabled", "state", "normal"),
            ("profile-switch-existing", "aspect", "16:9"),
            ("multiplayer-p2-owner", "input", "pad-p1"),
            ("practice-locked", "state", "unlocked"),
            ("options-refused", "input", "pad-p1"),
            ("records-earned-1p", "state", "no-records"),
            ("records-earned-2p", "input", "pad-p2"),
            ("transition-back-release", "state", "released"),
            ("authentic-title-stock", "mode", "modern"),
            ("authentic-stock-wide", "mode", "modern"),
            ("focus-loss-modal", "state", "normal"),
        ):
            with self.subTest(cid=cid, key=key):
                m = copy.deepcopy(self.matrix)
                case = next(x for x in m["cases"] if x["id"] == cid)
                case[key] = incorrect
                with self.assertRaisesRegex(ValueError, "protected visual matrix"):
                    coverage.reconcile(m, self.evidence)

    def test_uncredited_matrix_missing_fields_rejected(self):
        for cid, field in (("multiplayer-p2-owner", "input"),
                           ("root-wide-4k-virtual", "pixels"),
                           ("authentic-stock-wide", "mode")):
            with self.subTest(cid=cid, field=field):
                m = copy.deepcopy(self.matrix)
                case = next(x for x in m["cases"] if x["id"] == cid)
                del case[field]
                with self.assertRaisesRegex(ValueError, "protected visual matrix"):
                    coverage.reconcile(m, self.evidence)

    def test_candidate_ownership_and_state_cannot_be_rewritten(self):
        for key,value in (("input","keyboard"),("state","p1-p2-named"),
                          ("mode","authentic"),("aspect","4:3")):
            with self.subTest(key=key):
                m=copy.deepcopy(self.matrix)
                target=next(x for x in m["cases"] if x["id"]=="root-wide-720")
                target[key]=value
                with self.assertRaisesRegex(ValueError,"matrix state/owner"):
                    coverage.reconcile(m,self.evidence)


if __name__=="__main__":
    unittest.main()
