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
        with self.assertRaisesRegex(ValueError,"no exact evidence"):
            coverage.reconcile(self.matrix,e)

    def test_wrong_semantic_route_not_sufficient(self):
        e=copy.deepcopy(self.evidence)
        for row in e["cases"]:
            if row["route"]=="options-p1":
                row["route"]="root-quit"
        with self.assertRaisesRegex(ValueError,"no exact evidence"):
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


if __name__=="__main__":
    unittest.main()
