"""ROM-free source-role and score-integrity tests for live 20-frame / five-GLB diagnostics."""
import copy
import json
from pathlib import Path
import unittest

from tools.art.evaluate_original_mesen_live_pose_matrix import (
    POSES, TICKS, verified_roles, assigned_role, silhouette_iou,
    mirror_source_horizontal, summarize_rows,
)


class LiveTwentyUnpairedPoseTests(unittest.TestCase):
    def test_original_historical_fit_withheld_strict_roles_are_never_overwritten(self):
        path = Path(__file__).resolve().parents[2] / (
            "analysis/data/racer-original-strict-tile-disjoint-holdout-20261103.json")
        data = json.loads(path.read_text())
        fit, withheld, strict = verified_roles(data)
        self.assertEqual((len(fit), len(withheld), len(strict)), (16, 19, 6))
        self.assertEqual(assigned_role(next(iter(fit)), (fit, withheld, strict)), "fit")
        self.assertEqual(assigned_role(next(iter(strict)), (fit, withheld, strict)),
                         "strict_withheld")
        self.assertEqual(assigned_role("0"*64, (fit, withheld, strict)),
                         "unclassified_live_source")
        corrupt = copy.deepcopy(data)
        corrupt["fit_original_index_plane_sha256"][0] = next(iter(strict))
        with self.assertRaisesRegex(ValueError, "leakage"):
            verified_roles(corrupt)

    def test_source_red_horizontal_mirror_preserves_alpha_and_source_identity(self):
        raw = bytearray(4096)
        raw[5*64+3] = 1
        raw[5*64+61] = 1
        raw[6*64+2] = 1
        raw = bytes(raw)
        mirrored = mirror_source_horizontal(raw)
        self.assertEqual(mirrored[5*64+60], 1)
        self.assertEqual(mirrored[5*64+2], 1)
        self.assertEqual(mirrored[6*64+61], 1)
        self.assertEqual(mirror_source_horizontal(mirrored), raw)
        self.assertNotEqual(mirrored, raw)
        with self.assertRaisesRegex(ValueError, "binary"):
            mirror_source_horizontal(raw[:-1])
        with self.assertRaisesRegex(ValueError, "binary"):
            mirror_source_horizontal(bytes([2]) + raw[1:])

    def test_binary_silhouette_score_rejects_nonbinary_and_empty(self):
        a = bytes([1, 0, 1, 0]) + bytes(4092)
        b = bytes([1, 1, 0, 0]) + bytes(4092)
        self.assertEqual(silhouette_iou(a, b), 0.33333333)
        for bad in (bytes(4095), bytes([2])+bytes(4095)):
            with self.assertRaisesRegex(ValueError, "binary"):
                silhouette_iou(a, bad)
        with self.assertRaisesRegex(ValueError, "empty"):
            silhouette_iou(bytes(4096), bytes(4096))

    def test_frozen_actual_200_score_receipt_joins_to_uncertain_pose_ranking(self):
        report_path = Path(__file__).resolve().parents[2] / (
            "analysis/data/racer-original-live20-five-real-glb-unpaired-diagnostic-20261103.json")
        d = json.loads(report_path.read_text())
        self.assertEqual(d["source_original_artifact_id"], 13217381754)
        self.assertEqual(d["source_original_zip_sha256"],
                         "709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f")
        self.assertEqual(d["old_frozen_index_plane_roles_among_new_live_sources"], {
            "fit": 1, "withheld": 1, "strict_withheld": 0,
            "unclassified_live_source": 38})
        rows = []
        for r in d["per_original_racer_frame_scores"]:
            rows.append({
                "tick": r["original_mesen_tick"], "racer": r["original_racer"],
                "frozen_source_role": r["frozen_role"],
                "unpaired_iou": r["fixed_camera_iou_by_GLb_pose"],
                "unpaired_iou_winner": r["unique_unpaired_pose_winner"],
                "unpaired_iou_tied_candidates": r["ambiguous_equal_iou_candidates"],
            })
        summary = summarize_rows(rows)
        self.assertEqual(summary["unpaired_iou_winner_counts"],
                         {"upright": 7, "pedal": 3, "wheelie": 0, "stunt": 0, "bank": 29})
        self.assertEqual(summary["ambiguous_exact_iou_tie_count"], 1)
        self.assertEqual(summary["mean_iou_per_real_GLb_pose"],
                         d["mean_iou_by_glb_pose"])
        self.assertEqual([r["frozen_role"] for r in
                          d["per_original_racer_frame_scores"]
                          if r["frozen_role"] != "unclassified_live_source"],
                         ["withheld", "fit"])
        tie = d["ambiguous_exact_iou_ties"]
        self.assertEqual(len(tie), 1)
        self.assertEqual((tie[0]["tick"], tie[0]["racer"]),
                         (1952, "red"))
        self.assertEqual(tie[0]["competing_2026_pose_names"], ["pedal", "bank"])
        for field in ("source_original_3D_pose_labels_recovered",
                      "original_1994_3D_camera_rig_mesh_recovered",
                      "source_to_existing_2026_GLb_pose_mapping_verified",
                      "owner_likeness_approved", "shipping_art_approved"):
            self.assertFalse(d[field])

    def test_frozen_screen_reflection_sensitivity_rejects_winner_overclaim(self):
        base = Path(__file__).resolve().parents[2] / "analysis/data"
        old = json.loads((base / "racer-original-live20-five-real-glb-unpaired-diagnostic-20261103.json").read_text())
        screen = json.loads((base / "racer-original-live20-screen-orientation-sensitivity-20261103.json").read_text())
        self.assertEqual(screen["original_source_zip_sha256"],
                         old["authentic_original_source_zip_sha256"])
        self.assertTrue(screen["original_red_display_reflection_independently_source_screen_authenticated"])
        self.assertFalse(screen["selection_between_held_and_screen_view_by_model_IoU"])
        self.assertEqual(len(screen["red_screen_oriented_fixed_camera_unpaired_20_rows"]),20)
        red = {r["tick"]:r for r in screen["red_screen_oriented_fixed_camera_unpaired_20_rows"]}
        self.assertEqual(set(red),set(TICKS))
        rows=[]
        for r in old["per_original_racer_frame_scores"]:
            if r["original_racer"] == "red":
                observation = red[r["original_mesen_tick"]]
                scores = observation["screen_oriented_iou_by_glb_pose"]
                winner = observation["unpaired_iou_winner"]
                tied = observation["ambiguous_tied_candidates"]
            else:
                scores=r["fixed_camera_iou_by_GLb_pose"]
                winner=r["unique_unpaired_pose_winner"]
                tied=r["ambiguous_equal_iou_candidates"]
            rows.append({"tick":r["original_mesen_tick"],
                         "racer":r["original_racer"],
                         "unpaired_iou":scores,
                         "unpaired_iou_winner":winner,
                         "unpaired_iou_tied_candidates":tied,
                         "frozen_source_role":r["frozen_role"]})
        summary=summarize_rows(rows)
        self.assertEqual(summary["unpaired_iou_winner_counts"],
                         {"upright":17,"pedal":4,"wheelie":0,"stunt":0,"bank":18})
        self.assertEqual(summary["ambiguous_exact_iou_tie_count"],1)
        self.assertEqual(summary["mean_iou_per_real_GLb_pose"],
                         screen["screen_oriented_40_observation_mean_iou_per_2026_GLb_pose"])
        ties=screen["source_original_40_observation_screen_oriented_exact_iou_ties"]
        self.assertEqual(ties,[{"tick":1899,"racer":"red",
                                "tied_candidate_names":["pedal","bank"],
                                "exact_rounded_iou":0.51428571}])
        for field in ("original_1994_3d_camera_rig_pose_names_recovered",
                      "source_to_2026_experimental_glb_pose_mapping_verified",
                      "owner_likeness_approved","shipping_art_approved"):
            self.assertFalse(screen[field])

    def test_exact_20_by_2_source_matrix_counts_and_no_pose_promotion(self):
        rows = []
        for tick in TICKS:
            for racer in ("blue", "red"):
                scores = {p: 0.2 for p in POSES}
                scores["upright"] = 0.4 if racer == "blue" else 0.3
                rows.append({"tick": tick, "racer": racer,
                             "frozen_source_role": "unclassified_live_source",
                             "unpaired_iou": scores, "unpaired_iou_winner": "upright",
                             "unpaired_iou_tied_candidates": []})
        result = summarize_rows(rows)
        self.assertEqual(result["original_2D_observations"], 40)
        self.assertEqual(result["unpaired_iou_winner_counts"]["upright"], 40)
        self.assertFalse(result["authentic_source_1994_pose_labels_verified"])
        tie = copy.deepcopy(rows)
        tie[0]["unpaired_iou"]["bank"] = tie[0]["unpaired_iou"]["upright"]
        tie[0]["unpaired_iou_winner"] = None
        tie[0]["unpaired_iou_tied_candidates"] = ["upright", "bank"]
        summary = summarize_rows(tie)
        self.assertEqual(summary["ambiguous_exact_iou_tie_count"], 1)
        self.assertEqual(summary["unpaired_iou_winner_counts"]["upright"], 39)
        tampered = copy.deepcopy(tie)
        tampered[0]["unpaired_iou_winner"] = "upright"
        with self.assertRaisesRegex(ValueError, "tie"):
            summarize_rows(tampered)
        tampered = copy.deepcopy(rows)
        tampered[1]["unpaired_iou_winner"] = "bank"
        with self.assertRaisesRegex(ValueError, "rank"):
            summarize_rows(tampered)
        tampered = copy.deepcopy(rows)
        tampered[1]["unpaired_iou"]["stunt"] = float("nan")
        with self.assertRaisesRegex(ValueError, "scores"):
            summarize_rows(tampered)
        tampered = copy.deepcopy(rows)
        tampered[2]["tick"] = tampered[1]["tick"]
        with self.assertRaisesRegex(ValueError, "census"):
            summarize_rows(tampered)
        tampered = copy.deepcopy(rows)
        tampered[0]["frozen_source_role"] = "auto-fit"
        with self.assertRaisesRegex(ValueError, "role"):
            summarize_rows(tampered)


if __name__ == "__main__":
    unittest.main()
