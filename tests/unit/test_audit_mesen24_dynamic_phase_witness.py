"""Stdlib original-source science regression for two fixed 2026 drive laws."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
import zipfile

from tests.unit.test_audit_mesen24_edge_coverage import example as historical_example
from tools.art.audit_mesen24_edge_coverage import TICKS, SHAPES, iou
from tools.art.audit_mesen24_reconstruction_tradeoffs import ARMS, ROLES
from tools.art.audit_mesen24_dynamic_phase_witness import (
    ALL_ARMS, DYNAMIC_ARMS, ROM, TICK, DYNAMIC_GLB_SHA256,
    DYNAMIC_WITNESS_SHA256, WITNESS_MEMBER, WITNESS_SHA256,
    compare_historical_witnesses, load_exact_witness,
)

DATA = (Path(__file__).resolve().parents[2] /
        "analysis/data/racer-original-mesen24-fixed-phase-dynamic-evidence-20261107.json")


def synthetic_pair():
    old = historical_example()
    # Retain every original 24-source-frame identity and the four controls.
    # Add static frame/unique-source-shape scores to the pure edge fixture.
    for role in ROLES:
        for name in ARMS:
            item = old["original_source_per_role"][role]["arms"][name]
            item["source_frame_pooled_alpha_iou"] = (
                .8 if name == "original_source_2d_rotation" else .55)
            item["source_unique_shape_equal_vote_mean_alpha_iou"] = (
                .81 if name == "original_source_2d_rotation" else .56)
    dynamic = copy.deepcopy(old)
    dynamic["schema"] = "UR-ART4K-ORIGINAL-24TICK-REAL-2026-SADDLE-LEAN-GENERALIZATION/3"
    dynamic["current_successful_2026_16_material_GLB_sha256"] = DYNAMIC_GLB_SHA256
    for role in ROLES:
        controls = dynamic["original_source_per_role"][role]["arms"]
        for name in DYNAMIC_ARMS:
            item = copy.deepcopy(controls["axle_root_saddle_plus15"])
            changed = []
            for t in TICKS[:-1]:
                # Synthetic original changes twice on every genuine source edge.
                # Every model phase control now predicts an edge at all 23 ticks.
                tp, fp, fn = ((1, 2, 1) if "hub_cover" in name else (1, 1, 1))
                changed.append({
                    "source_ticks": [t, t + 1], "tp": tp, "fp": fp,
                    "fn": fn, "iou": iou(tp, fp, fn),
                })
            aggregate = [sum(e[key] for e in changed) for key in ("tp", "fp", "fn")]
            item["per_original_chronological_edge"] = changed
            item["source_actual_23_consecutive_edge_change_tp_fp_fn"] = {
                key: value for key, value in zip(("tp", "fp", "fn"), aggregate)}
            item["source_actual_23_consecutive_edge_change_pooled_iou"] = iou(*aggregate)
            item["source_frame_pooled_alpha_iou"] = .61 if "hub_cover" in name else .60
            item["source_unique_shape_equal_vote_mean_alpha_iou"] = (
                .62 if "hub_cover" in name else .60)
            controls[name] = item
    return old, dynamic


class OriginalMesen24PhaseDriveTests(unittest.TestCase):
    def test_two_predeclared_dynamic_controls_both_restore_true_timeline_coverage(self):
        old, dynamic = synthetic_pair()
        report = compare_historical_witnesses(old, dynamic)
        self.assertTrue(report["static_four_arm_baselines_preserved_pixel_exactly"])
        self.assertTrue(report["authentic_1994_original_masks_identical_between_runs"])
        self.assertFalse(report["historical_glb_byte_equality_asserted"])
        self.assertFalse(report["proven_1994_physical_animation"])
        self.assertFalse(report["owner_selected_later_outboard_mirrored_model_tested"])
        for name in (ROM, TICK):
            self.assertTrue(report["fixed_phase_controls_exceed_source_2d_null_edge_iou_both_roles"][name])
            self.assertTrue(report["fixed_phase_controls_keep_saddle_plus15_unique_shape_gain_both_roles"][name])
        for role in ROLES:
            for name in DYNAMIC_ARMS:
                s = report["role_metrics"][role][name]
                self.assertEqual(s["model_predicted_nonempty_change_edges"], 23)
                self.assertEqual(s["original_source_nonempty_change_edges"], 23)
                self.assertEqual(s["source_changed_alpha_pixel_instances"], 46)
        for value in report["experimental_hub_cover_dominates_matched_no_hub_all_metrics_both_roles"].values():
            self.assertFalse(value)

    def test_rejects_original_drift_and_unqualified_dynamic_variant(self):
        edits = (
            ("mismatched source camera", lambda o,d: d.update(source_unchanged_7_6_camera_sha256="1"*64)),
            ("wrong real GLB", lambda o,d: d.update(current_successful_2026_16_material_GLB_sha256="2"*64)),
            ("missing role", lambda o,d: d["original_source_per_role"].pop("red")),
            ("new fitted arm", lambda o,d: d["original_source_per_role"]["blue"]["arms"].update(extra_2026_fit={})),
            ("old baseline changed", lambda o,d: d["original_source_per_role"]["red"]["arms"]["axle_root_saddle_plus15"].update(source_frame_pooled_alpha_iou=.9)),
            ("original source pixel changed", lambda o,d: d["original_source_per_role"]["blue"]["original_24_tick_samples"]["1602"].update(source_2D_alpha_sha256="3"*64)),
            ("missing original chronological edge", lambda o,d: d["original_source_per_role"]["blue"]["arms"][ROM]["per_original_chronological_edge"].pop()),
            ("candidate frozen", lambda o,d: d["original_source_per_role"]["red"]["arms"][ROM].update(
                per_original_chronological_edge=copy.deepcopy(
                    d["original_source_per_role"]["red"]["arms"]["axle_root_saddle_plus15"]["per_original_chronological_edge"]),
                source_actual_23_consecutive_edge_change_tp_fp_fn={
                    "tp": 1, "fp": 1, "fn": 45},
                source_actual_23_consecutive_edge_change_pooled_iou=iou(1, 1, 45))),
            ("mismatched authentic source mask change", lambda o,d: d["original_source_per_role"]["blue"]["arms"][ROM]["per_original_chronological_edge"][0].update(fn=0)),
            ("bad IoU", lambda o,d: d["original_source_per_role"]["red"]["arms"][TICK]["per_original_chronological_edge"][1].update(iou=.9)),
            ("invalid score", lambda o,d: d["original_source_per_role"]["red"]["arms"][ROM].update(source_unique_shape_equal_vote_mean_alpha_iou=math.nan)),
            ("wrong exact static archive", lambda o,d: o.update(current_successful_2026_16_material_GLB_sha256="4"*64)),
        )
        for label, mutate in edits:
            old, dynamic = synthetic_pair()
            mutate(old, dynamic)
            with self.subTest(label=label), self.assertRaises(ValueError):
                compare_historical_witnesses(old, dynamic)

    def test_historical_saved_dynamic_result_keeps_two_roles_and_all_ten_controls(self):
        report = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(report["dynamic_witness_sha256"], DYNAMIC_WITNESS_SHA256)
        self.assertEqual(report["static_witness_sha256"], WITNESS_SHA256)
        self.assertTrue(report["static_four_arm_baselines_preserved_pixel_exactly"])
        self.assertFalse(report["historical_glb_byte_equality_asserted"])
        self.assertFalse(report["owner_selected_later_outboard_mirrored_model_tested"])
        self.assertFalse(report["proven_1994_physical_animation"])
        self.assertFalse(report["shipping_art_approved"])
        expected = {
            "blue": {ROM: (.56757653, .57006528, .13202247, 141, 408, 519),
                     TICK: (.56870778, .5709925, .16134061, 207, 623, 453)},
            "red": {ROM: (.58549568, .58761115, .17943262, 253, 751, 406),
                    TICK: (.58471835, .58663941, .15871833, 213, 683, 446)},
        }
        for role in ROLES:
            self.assertEqual(set(report["role_metrics"][role]), set(ALL_ARMS))
            for arm in DYNAMIC_ARMS:
                self.assertEqual(report["role_metrics"][role][arm]["model_predicted_nonempty_change_edges"], 23)
            for arm, vals in expected[role].items():
                s = report["role_metrics"][role][arm]
                self.assertEqual(
                    (s["chronological_shape_iou"],
                     s["unique_source_shape_equal_vote_iou"],
                     s["original_edge_change_iou"],
                     s["matched_changed_alpha_pixel_instances"],
                     s["false_positive_changed_alpha_pixel_instances"],
                     s["missed_original_changed_alpha_pixel_instances"]), vals)
        self.assertTrue(all(report["fixed_phase_controls_exceed_source_2d_null_edge_iou_both_roles"].values()))
        self.assertTrue(all(report["fixed_phase_controls_keep_saddle_plus15_unique_shape_gain_both_roles"].values()))
        self.assertFalse(any(report["experimental_hub_cover_dominates_matched_no_hub_all_metrics_both_roles"].values()))

    def test_historical_zip_identity_rejects_fabricated_source_archive(self):
        with tempfile.TemporaryDirectory() as root:
            fake=Path(root)/"research.zip"
            with zipfile.ZipFile(fake,"w") as output:
                output.writestr(WITNESS_MEMBER,json.dumps(synthetic_pair()[1]))
            with self.assertRaisesRegex(ValueError,"SHA differs"):
                load_exact_witness(fake,DYNAMIC_WITNESS_SHA256)


if __name__ == "__main__":
    unittest.main()
