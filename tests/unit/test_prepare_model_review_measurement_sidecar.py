"""ROM/GLB-free sidecar contract tests; validate an independently scored matrix."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import types
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.art.prepare_model_review_measurement_sidecar import (
    POSES, SCHEMA, sanitized_sidecar, create_sidecar, digest,
)
from tools.art.no_replace_report import publish_text_once


def fake_matrix():
    rows, used = [], []
    for j in range(10):
        size = 4 if j < 2 else 3
        # 4+4+8*3 = 32 independently referenced player/frame IDs.
        frames = []
        for _ in range(size):
            n = len(used)
            player = "p1" if n < 16 else "p2"
            frame = 1205 + n % 16
            used.append((player, frame))
            frames.append({
                "player": player, "guest_frame": frame,
                "representation_id": f"original-{j}-{n}",
                "original_png_sha256": f"{n:064x}",
            })
        scores = {}
        for k, pose in enumerate(POSES):
            scores[pose] = {
                "mask_iou": round(.1 + j*.01 + k*.05, 8),
                "boundary_chamfer_mean_physical_px": round(1.5 - k*.1, 8),
            }
        rows.append({
            "source_binary_mask_sha256": f"{j+400:064x}",
            "registered_original_contact_x2_y2": [67+2*(j%3),76],
            "source_registered_logical_xy_translation": [j%3,0],
            "source_observation_count": len(frames),
            "original_source_observations": frames,
            "unpaired_pose_scores": scores,
            "unpaired_best_fit_pose": "bank",
        })
    means = {
        pose: round(sum(r["unpaired_pose_scores"][pose]["mask_iou"]
                        for r in rows) / 10, 8)
        for pose in POSES
    }
    return {
        "schema": "UR-RACER-UNPAIRED-POSE-SIMILARITY-MATRIX/1",
        "registration_mode": "source-registered",
        "camera_status": "provisional",
        "registered_original_contact_used_without_optimization": True,
        "similarities_are_unpaired_hypotheses_not_source_pose_mapping": True,
        "camera_shared_across_all_comparisons": True,
        "original_1994_3d_camera_recovered": False,
        "independent_pose_family_holdout_tested": False,
        "shipping_art_approved": False,
        "owner_likeness_approved": False,
        "viewer_model_source_commit": "a" * 40,
        "viewer_model_source_scad_sha256": "b"*64,
        "viewer_five_pose_glb_sha256": {pose: f"{k+700:064x}"
                                     for k, pose in enumerate(POSES)},
        "camera_manifest_sha256": "c"*64,
        "original_source_registry_sha256": "d"*64,
        "source_original_rom_sha256": "e"*64,
        "original_frame_observations": 32,
        "unique_original_binary_silhouettes": 10,
        "comparison_count": 50,
        "rows": rows,
        "summary": {
            "equal_source_mask_weighted_mean_iou_by_experimental_pose": means,
            "unpaired_highest_iou_source_mask_count_by_experimental_pose": {
                pose: (10 if pose == "bank" else 0) for pose in POSES
            }
        },
    }


class ModelReviewMeasurementSidecarTests(unittest.TestCase):
    def setUp(self):
        self.matrix = fake_matrix()

    def build(self):
        return sanitized_sidecar(self.matrix, "1"*64, "2"*64)

    def test_exact_verified_data_produces_readonly_sidecar(self):
        data = self.build()
        self.assertEqual(data["schema"], SCHEMA)
        self.assertEqual(data["distinct_original_source_binary_silhouette_count"], 10)
        self.assertEqual(data["experimental_glb_pose_count"], 5)
        self.assertEqual(data["original_frame_observations"], 32)
        self.assertEqual(len(data["source_shape_measurements"]), 10)
        self.assertFalse(data["source_to_experimental_model_pose_mapping_verified"])
        self.assertFalse(data["owner_character_likeness_approved"])
        self.assertFalse(data["viewer_files_modified"])
        self.assertFalse(data["public_website_deployment_claimed"])
        self.assertEqual(data["experimental_pose_highest_iou_counts"]["bank"], 10)
        self.assertTrue(all(
            item["runner_up_iou_experimental_pose"] == "stunt" and
            item["first_minus_second_unpaired_iou_margin"] == .05 and
            item["margin_is_pose_identity_confidence"] is False
            for item in data["source_shape_measurements"]
        ))
        self.assertNotIn("image", str(data))  # image binaries / local URLs never embedded.

    def test_repeated_identical_original_shape_is_rejected(self):
        self.matrix["rows"][1]["source_binary_mask_sha256"] = self.matrix["rows"][0]["source_binary_mask_sha256"]
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.build()

    def test_source_duplicate_frame_forgery_is_rejected(self):
        self.matrix["rows"][1]["original_source_observations"][0] = (
            copy.deepcopy(self.matrix["rows"][0]["original_source_observations"][0])
        )
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.build()

    def test_approval_camera_and_pose_spoofs_fail_closed(self):
        for field in ("shipping_art_approved", "owner_likeness_approved",
                      "original_1994_3d_camera_recovered",
                      "independent_pose_family_holdout_tested"):
            with self.subTest(field=field):
                self.matrix[field] = True
                with self.assertRaisesRegex(ValueError, "provisional"):
                    self.build()
                self.matrix[field] = False
        self.matrix["registration_mode"] = "fixed-witness"
        with self.assertRaisesRegex(ValueError, "provisional"):
            self.build()

    def test_forged_winner_and_summary_are_rejected(self):
        self.matrix["rows"][0]["unpaired_best_fit_pose"] = "wheelie"
        with self.assertRaisesRegex(ValueError, "winner"):
            self.build()
        self.matrix = fake_matrix()
        self.matrix["summary"]["equal_source_mask_weighted_mean_iou_by_experimental_pose"]["bank"] = 0.99
        with self.assertRaisesRegex(ValueError, "summary"):
            self.build()

    def test_incomplete_pose_mask_or_wrong_geometry_measure_is_rejected(self):
        self.matrix["viewer_five_pose_glb_sha256"].pop("stunt")
        with self.assertRaisesRegex(ValueError, "five actual"):
            self.build()
        self.matrix = fake_matrix()
        self.matrix["rows"][0]["unpaired_pose_scores"]["bank"]["mask_iou"] = float("nan")
        with self.assertRaisesRegex(ValueError, "invalid measured"):
            self.build()
        self.matrix = fake_matrix()
        self.matrix["rows"][0]["source_registered_logical_xy_translation"] = [2,0]
        with self.assertRaisesRegex(ValueError, "source anchor"):
            self.build()

    def test_missing_player_frame_or_unverified_sha_rejected(self):
        self.matrix["rows"][0]["original_source_observations"][0]["player"] = "p3"
        with self.assertRaisesRegex(ValueError, "forged"):
            self.build()
        self.matrix = fake_matrix()
        with self.assertRaisesRegex(ValueError, "SHA256"):
            sanitized_sidecar(self.matrix, "invalid-sha", "2"*64)

    def test_sidecar_published_without_replacing_existing(self):
        with tempfile.TemporaryDirectory() as base:
            path = Path(base) / "measured.json"
            text = json.dumps(self.build(), sort_keys=True) + "\n"
            publish_text_once(path, text)
            self.assertEqual(path.read_text(), text)
            with self.assertRaises(FileExistsError):
                publish_text_once(path, "forge\n")
            self.assertEqual(path.read_text(), text)

    def test_mutating_viewer_between_measurement_and_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as base:
            site = Path(base)
            (site/"manifest.json").write_text('{"model":"original"}')
            (site/"sprites.json").write_text('{"sprite":"original"}')
            camera = site/"camera.json"
            camera.write_text('{"camera":"original"}')
            stub = types.ModuleType("tools.art.build_real_viewer_pose_matrix")
            def unstable_compute(path, camera_path, mode):
                (path/"manifest.json").write_text('{"model":"swapped"}')
                result = fake_matrix()
                result["camera_manifest_sha256"] = digest(camera_path.read_bytes())
                return result
            stub.compute = unstable_compute
            with patch.dict(sys.modules, {"tools.art.build_real_viewer_pose_matrix": stub}):
                with self.assertRaisesRegex(ValueError, "changed during measurement"):
                    create_sidecar(site, camera)

    def test_actual_create_sidecar_invokes_measurement_not_untrusted_json(self):
        with tempfile.TemporaryDirectory() as base:
            site = Path(base)
            (site / "manifest.json").write_text('{"model":"fixture"}\n')
            (site / "sprites.json").write_text('{"original":"fixture"}\n')
            (site / "camera.json").write_text('{"camera":"fixture"}\n')
            stub = types.ModuleType("tools.art.build_real_viewer_pose_matrix")
            calls = []
            def fake_compute(path, camera, mode):
                calls.append((path, camera, mode))
                measured = fake_matrix()
                measured["camera_manifest_sha256"] = digest(camera.read_bytes())
                return measured
            stub.compute = fake_compute
            with patch.dict(sys.modules, {"tools.art.build_real_viewer_pose_matrix": stub}):
                result = create_sidecar(site, Path(base)/"camera.json")
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][2], "source-registered")
            self.assertEqual(result["viewer_manifest_sha256"],
                             digest((site/"manifest.json").read_bytes()))
            self.assertEqual(result["viewer_sprite_rail_sha256"],
                             digest((site/"sprites.json").read_bytes()))


if __name__ == "__main__":
    unittest.main()
