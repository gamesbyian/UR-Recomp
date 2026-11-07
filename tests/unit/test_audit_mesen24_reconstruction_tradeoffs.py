"""Stdlib-only tests of historical 48-original-sprite multiobjective evidence."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from tools.art.audit_mesen24_reconstruction_tradeoffs import (
    audit, SCHEMA, HISTORICAL_SOURCE, HISTORICAL_RUN, HISTORICAL_HEAD,
    ROLES, ARMS, METRICS,
)

REPORT = (Path(__file__).resolve().parents[2] /
          "analysis/data/racer-original-mesen24-saddle-temporal-evidence-20261104.json")


def example():
    return json.loads(REPORT.read_text(encoding="utf-8"))


class ExactMesen24AuditTests(unittest.TestCase):
    def test_full_historical_report_preserves_both_real_roles_and_2d_null(self):
        result = audit(example())
        self.assertEqual(result["schema"], "UR-ART4K-MESEN24-MULTIOBJECTIVE-REVIEW/1")
        self.assertEqual(result["distinct_original_binary_shapes"], {"blue": 19, "red": 23})
        self.assertEqual(result["chronological_original_frames_per_role"], 24)
        self.assertEqual(result["actual_original_edges_per_role"], 23)
        self.assertTrue(result["same_authentic_source_all_48_frames"])
        self.assertTrue(result["original_2d_rigid_rotation_beats_all_2026_3d_arms"])
        self.assertFalse(result["owner_preferred_outboard_geometry_tested"])
        self.assertEqual(result["source_identity"], HISTORICAL_SOURCE)
        plus = result["comparisons"]["axle_root_saddle_plus15"]
        self.assertTrue(plus["shape_gain_both_roles"])
        self.assertFalse(plus["chronological_motion_gain_both_roles"])
        self.assertFalse(plus["dominates_neutral_all_roles_and_metrics"])
        self.assertAlmostEqual(
            plus["delta_against_neutral_by_role"]["blue"]["real_23_tick_edge_change_pooled_iou"],
            -0.00261403)
        self.assertAlmostEqual(
            plus["delta_against_neutral_by_role"]["red"]["real_23_tick_edge_change_pooled_iou"],
            -0.00139235)
        self.assertFalse(result["shipping_art_approved"])
        self.assertFalse(result["historical_3d_recovered"])
        self.assertFalse(result["likeness_approved"])

    def test_rejects_missing_substituted_or_mutated_source_provenance(self):
        changes = (
            ("schema", lambda d: d.update(schema="other")),
            ("missing producer", lambda d: d.pop("producer")),
            ("different ROM", lambda d: d["producer"].update(original_source_USA_ROM_sha256="b"*64)),
            ("different phase", lambda d: d["producer"].update(original_pose_report_sha256="c"*64)),
            ("different model", lambda d: d["producer"].update(current_2026_authored_SCAD_sha256="d"*64)),
            ("other valid run", lambda d: d["producer"].update(original_source_run="https://github.com/gamesbyian/UR-Recomp/actions/runs/42")),
            ("other implementation", lambda d: d["producer"].update(exact_tested_implementation_head="e"*40)),
            ("unapproved changed", lambda d: d["producer"].update(original_art_likeness_approved=True)),
            ("3d recovered", lambda d: d["producer"].update(original_1994_physical_3d_model_or_camera_recovered=True)),
        )
        for label, change in changes:
            report = example()
            change(report)
            with self.subTest(label=label), self.assertRaises(ValueError):
                audit(report)

    def test_rejects_role_arm_count_metric_and_hidden_hypothesis_selection(self):
        def mutate(name, d):
            if name == "one role":
                d["reported_per_role"].pop("red")
            elif name == "one missing arm":
                d["reported_per_role"]["blue"].pop("axle_root_saddle_minus15")
            elif name == "extra tuned arms":
                for role in ROLES:
                    d["reported_per_role"][role]["extra_fitted_arm"] = copy.deepcopy(
                        d["reported_per_role"][role]["axle_root_saddle_neutral"])
            elif name == "bad shape count":
                d["reported_per_role"]["red"]["axle_root_saddle_neutral"]["unique_shapes"] = 24
            elif name == "bad type":
                d["reported_per_role"]["blue"]["axle_root_saddle_plus15"][METRICS[0]] = True
            elif name == "nan":
                d["reported_per_role"]["blue"]["axle_root_saddle_plus15"][METRICS[1]] = math.nan
            elif name == "over 100%":
                d["reported_per_role"]["red"]["axle_root_saddle_neutral"][METRICS[2]] = 1.01
            elif name == "missing source 2d null":
                for role in ROLES:
                    d["reported_per_role"][role].pop("original_source_2d_rotation")
        for name in ("one role", "one missing arm", "extra tuned arms", "bad shape count",
                     "bad type", "nan", "over 100%", "missing source 2d null"):
            report = example()
            mutate(name, report)
            with self.subTest(name=name), self.assertRaises(ValueError):
                audit(report)
        with self.assertRaises(ValueError):
            audit(example(), baseline="axle_root_saddle_plus15")

    def test_really_improved_time_and_shape_would_be_recognized(self):
        report = example()
        for role in ROLES:
            candidate = report["reported_per_role"][role]["axle_root_saddle_plus15"]
            neutral = report["reported_per_role"][role]["axle_root_saddle_neutral"]
            for metric in METRICS:
                candidate[metric] = neutral[metric] + 0.01
        result = audit(report)["comparisons"]["axle_root_saddle_plus15"]
        self.assertTrue(result["dominates_neutral_all_roles_and_metrics"])
        self.assertTrue(result["chronological_motion_gain_both_roles"])
        self.assertTrue(result["shape_gain_both_roles"])


if __name__ == "__main__":
    unittest.main()
