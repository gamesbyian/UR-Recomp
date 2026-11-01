"""Source-verified 5x10 unpaired model-pose matrix and honest ranking tests."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.art.build_real_viewer_pose_matrix import (
    POSES, compute, rank_unpaired, translated_binary_mask,
    original_registered_contacts,
)
from tools.art.build_racer_source_pixel_corpus import build as original_corpus, ROOT
from tools.art.render_racer_glb_projection import np, trimesh, Image


def ranking_row(sha, n, best="bank", high=0.8):
    scores = {
        pose: {
            "mask_iou": high if pose == best else 0.2,
            "boundary_chamfer_mean_physical_px": 0.5 if pose == best else 2.0,
        }
        for pose in POSES
    }
    return {
        "source_binary_mask_sha256": sha * 64,
        "source_observation_count": n,
        "unpaired_pose_scores": scores,
        "unpaired_best_fit_pose": best,
    }


class UnpairedPoseRankingTests(unittest.TestCase):
    def test_declared_integer_contact_translation_without_clipping(self):
        source = bytearray(64 * 64)
        source[21*64+27] = 1
        moved = translated_binary_mask(bytes(source), -5, 0)
        self.assertEqual(moved[21*64+22], 1)
        self.assertEqual(sum(moved), 1)
        self.assertEqual(translated_binary_mask(bytes(source), 0, 0), bytes(source))
        with self.assertRaisesRegex(ValueError, "would clip"):
            translated_binary_mask(bytes(source), -30, 0)
        with self.assertRaisesRegex(ValueError, "integer shift"):
            translated_binary_mask(bytes(source), 0.5, 0)

    def test_registration_contacts_are_source_defined_not_fitted(self):
        from tools.art.build_racer_source_pixel_corpus import REGISTRY
        original = original_corpus()
        contacts = original_registered_contacts(
            REGISTRY, original["source_registry_current_sha256"])
        ids = {x["representation_id"] for x in original["observations"]}
        self.assertTrue(ids.issubset(contacts))
        p1 = next(x for x in original["observations"]
                  if x["player"]=="p1" and x["guest_frame"]==1205)
        p2 = next(x for x in original["observations"]
                  if x["player"]=="p2" and x["guest_frame"]==1205)
        self.assertEqual(contacts[p1["representation_id"]], ("p1", (67,76)))
        self.assertEqual(contacts[p2["representation_id"]], ("p2", (57,76)))
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            original_registered_contacts(REGISTRY, "0"*64)

    def test_repeated_frames_do_not_outvote_distinct_source_shapes(self):
        rows = [ranking_row("a", 30, "upright"),
                ranking_row("b", 1, "bank", 0.7)]
        result = rank_unpaired(rows)
        self.assertEqual(result["unpaired_highest_iou_source_mask_count_by_experimental_pose"]["upright"], 1)
        self.assertEqual(result["unpaired_highest_iou_source_mask_count_by_experimental_pose"]["bank"], 1)
        self.assertEqual(result["equal_source_mask_weighted_mean_iou_by_experimental_pose"]["upright"], .5)
        self.assertFalse(result["winner_is_authentic_original_pose_mapping"])
        self.assertTrue(result["not_a_heldout_measurement"])

    def test_duplicate_source_mask_cannot_vote_twice(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            rank_unpaired([ranking_row("a", 20), ranking_row("a", 2)])

    def test_forged_winner_and_incomplete_matrix_rejected(self):
        false_row = ranking_row("a", 1, "upright")
        false_row["unpaired_best_fit_pose"] = "bank"
        with self.assertRaisesRegex(ValueError, "claimed best"):
            rank_unpaired([false_row])
        missing = ranking_row("a", 1)
        del missing["unpaired_pose_scores"]["wheelie"]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            rank_unpaired([missing])

    def test_invalid_iou_and_no_rows_rejected(self):
        with self.assertRaises(ValueError):
            rank_unpaired([])
        broken = ranking_row("a", 1)
        broken["unpaired_pose_scores"]["pedal"]["mask_iou"] = 2.0
        with self.assertRaisesRegex(ValueError, "invalid"):
            rank_unpaired([broken])


@unittest.skipUnless(all(x is not None for x in (np, trimesh, Image)),
                     "optional offline GLB render dependencies absent")
class RealOriginalPixelsSyntheticFiveGlbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.site = Path(self.tmp.name) / "model-review"
        (self.site / "sprites").mkdir(parents=True)
        (self.site / "assets").mkdir()
        original = original_corpus()
        self.refs = []
        for r in original["observations"]:
            source = ROOT / r["source_image"]
            dest = self.site / "sprites" / source.name
            if not dest.exists():
                shutil.copy2(source, dest)
            self.refs.append({
                "player": r["player"], "guest_frame": r["guest_frame"],
                "image": "sprites/" + source.name,
                "sha256": r["png_file_sha256"],
                "representation_id": r["representation_id"],
            })
        sprites = {
            "schema": "ur-racer-original-sprite-reference/1",
            "source_sha256": original["historical_manifest_declared_rom_sha256"],
            "sprite_3d_pose_mapping_verified": False,
            "frames": self.refs,
        }
        (self.site / "sprites.json").write_text(json.dumps(sprites), encoding="utf-8")
        poses = {}
        for i, pose in enumerate(POSES):
            scene = trimesh.Scene()
            for j, part in enumerate(("tire", "rim_and_hub", "fork_and_frame", "pedals", "saddle")):
                mesh = trimesh.creation.box(extents=[.2 + i*.008, .2, .3])
                transform = trimesh.transformations.translation_matrix([j*.07, 0, j*.30])
                scene.add_geometry(mesh, node_name=part, geom_name=part+"__mat", transform=transform)
            path = self.site/"assets"/(pose+".glb")
            path.write_bytes(scene.export(file_type="glb"))
            poses[pose] = {
                "url": "assets/"+pose+".glb",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        manifest = {
            "schema": "ur-racer-model-review/1",
            "source_commit": "a"*40, "source_model_sha256": "b"*64,
            "model_url": poses["upright"]["url"],
            "candidate_sha256": poses["upright"]["sha256"],
            "poses": poses, "likeness_approved": False,
            "source_sprite_pose_registration": False,
        }
        (self.site/"manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_exact_real_original_sprite_rail_and_five_synthetic_glbs(self):
        result = compute(self.site)
        self.assertEqual(result["original_frame_observations"], 32)
        self.assertEqual(result["unique_original_binary_silhouettes"], 10)
        self.assertEqual(result["comparison_count"], 50)
        self.assertEqual(set(result["viewer_five_pose_glb_sha256"]), set(POSES))
        self.assertEqual(len(result["rows"]), 10)
        self.assertEqual(sum(r["source_observation_count"] for r in result["rows"]), 32)
        self.assertTrue(result["similarities_are_unpaired_hypotheses_not_source_pose_mapping"])
        self.assertFalse(result["owner_likeness_approved"])
        self.assertFalse(result["independent_pose_family_holdout_tested"])

    def test_source_semantic_registered_anchors_are_distinct_from_fixed_witness(self):
        fixed = compute(self.site, registration_mode="fixed-witness")
        registered = compute(self.site, registration_mode="source-registered")
        self.assertEqual(registered["comparison_count"], 50)
        self.assertTrue(registered["registered_original_contact_used_without_optimization"])
        self.assertFalse(registered["per_pair_auto_alignment"])
        self.assertFalse(registered["owner_likeness_approved"])
        self.assertEqual(registered["unique_original_binary_silhouettes"], 10)
        by_frame = {r["original_source_observations"][0]["player"]+":"+
                    str(r["original_source_observations"][0]["guest_frame"]): r
                    for r in registered["rows"]}
        self.assertEqual(by_frame["p1:1205"]["source_registered_logical_xy_translation"], [0, 0])
        self.assertEqual(by_frame["p2:1205"]["source_registered_logical_xy_translation"], [-5, 0])
        self.assertNotEqual(
            fixed["summary"]["equal_source_mask_weighted_mean_iou_by_experimental_pose"],
            registered["summary"]["equal_source_mask_weighted_mean_iou_by_experimental_pose"],
        )

    def test_internally_consistent_forged_sprite_is_rejected(self):
        sprite = self.site / self.refs[0]["image"]
        sprite.write_bytes(sprite.read_bytes() + b"tampered")
        changed_sha = hashlib.sha256(sprite.read_bytes()).hexdigest()
        meta = json.loads((self.site/"sprites.json").read_text())
        for frame in meta["frames"]:
            if frame["image"] == self.refs[0]["image"]:
                frame["sha256"] = changed_sha
        (self.site/"sprites.json").write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError, "original-source authenticated"):
            compute(self.site)

    def test_forged_camera_calibration_is_rejected(self):
        from tools.art.audit_real_viewer_glbs import CAMERA
        camera = json.loads(CAMERA.read_text())
        camera["camera_calibration_status"] = "source-calibrated"
        altered = self.site/"forged-camera.json"
        altered.write_text(json.dumps(camera))
        with self.assertRaises(ValueError):
            compute(self.site, altered)


if __name__ == "__main__":
    unittest.main()
