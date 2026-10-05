import json
import tempfile
import unittest
from pathlib import Path

from tools.build_racer_hd_review_packet import (
    build_review_manifest,
    build_review_packet,
)


class RacerHdReviewPacketTest(unittest.TestCase):
    def dossier(self):
        return {
            "family": "ordinary-racer",
            "temporal_window": {"start": 1, "end": 2, "frame_count": 2},
            "representations": [
                {
                    "representation_id": "a",
                    "stock_evidence": {
                        "png": "stock/a.png",
                        "nearest_4x_png": "nearest-4x/a.png",
                    },
                    "art_review": {
                        "authored_candidate": {
                            "png": "authored-candidate/a.png",
                            "approval_status": "motion-reviewed",
                            "gameplay_scale_review": {
                                "alpha_iou": 0.75,
                                "stock_only_pixel_count": 1,
                                "candidate_only_pixel_count": 1,
                                "stock_only_pixels": [[2, 3]],
                                "candidate_only_pixels": [[4, 5]],
                            },
                        },
                    },
                },
                {
                    "representation_id": "b",
                    "stock_evidence": {
                        "png": "stock/b.png",
                        "nearest_4x_png": "nearest-4x/b.png",
                    },
                    "art_review": {
                        "authored_candidate": {
                            "png": "authored-candidate/b.png",
                            "approval_status": "motion-reviewed reuse",
                            "gameplay_scale_review": {"alpha_iou": 0.75},
                        },
                    },
                },
            ],
        }

    def equivalence(self):
        return {
            "semantic_representation_count": 2,
            "unique_stock_pose_count": 1,
            "pose_groups": [
                {
                    "pose_id": "p1-pose-001",
                    "player": "p1",
                    "stock_rgba_sha256": "stock",
                    "representation_ids": ["a", "b"],
                    "semantic_frame_ids": ["0x1"],
                    "observed_frames": [1, 2],
                    "authored_source_representation_id": "a",
                    "authored_asset_rgba_sha256": "art",
                    "needs_authored_asset": False,
                    "authored_asset_conflict": False,
                },
            ],
            "worklist": {
                "authored_pose_count": 1,
                "unauthored_pose_count": 0,
                "conflicting_authored_pose_count": 0,
            },
        }

    def test_review_manifest_uses_unique_pose_not_semantic_guard_count(self):
        manifest = build_review_manifest(self.dossier(), self.equivalence())
        self.assertEqual(manifest["semantic_representation_count"], 2)
        self.assertEqual(manifest["unique_pose_count"], 1)
        self.assertEqual(manifest["authored_pose_count"], 1)
        self.assertEqual(manifest["unauthored_pose_count"], 0)
        self.assertEqual(len(manifest["poses"]), 1)
        pose = manifest["poses"][0]
        self.assertEqual(pose["representation_ids"], ["a", "b"])
        self.assertEqual(pose["authored_png"], "authored-candidate/a.png")
        self.assertEqual(pose["gameplay_scale_review"]["alpha_iou"], 0.75)

    def test_packet_shipping_status_comes_from_hash_bound_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier = root / "manifest.json"
            equivalence = root / "equivalence.json"
            readiness = root / "readiness.json"
            dossier.write_text(json.dumps(self.dossier()))
            equivalence.write_text(json.dumps(self.equivalence()))
            readiness.write_text(json.dumps({
                "shipping_ready": True,
                "unique_pose_count": 1,
                "counts": {
                    "approved": 1,
                    "needs_refinement": 0,
                    "rejected": 0,
                    "unreviewed": 0,
                    "changed_since_review": 0,
                    "unauthored": 0,
                    "authored_conflicts": 0,
                },
                "poses": [{
                    "pose_id": "p1-pose-001",
                    "review_status": "approved",
                    "shipping_art_approved": True,
                    "blocker_codes": [],
                    "reviewed_authored_rgba_sha256": "art",
                }],
            }))

            out = root / "review"
            manifest = build_review_packet(
                dossier,
                equivalence,
                out,
                readiness_path=readiness,
            )
            pose = manifest["poses"][0]
            self.assertEqual(pose["shipping_review_status"], "approved")
            self.assertTrue(pose["shipping_art_approved"])
            self.assertEqual(pose["shipping_blocker_codes"], [])
            self.assertEqual(pose["reviewed_authored_rgba_sha256"], "art")
            self.assertTrue(manifest["shipping_readiness"]["shipping_ready"])

    def test_packet_copies_baseline_assets_for_before_after_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_root = root / "current"
            baseline_root = root / "baseline-source"
            current_root.mkdir()
            baseline_root.mkdir()

            dossier = current_root / "manifest.json"
            equivalence = current_root / "equivalence.json"
            baseline_dossier = baseline_root / "manifest.json"
            baseline_equivalence = baseline_root / "equivalence.json"

            current = self.dossier()
            before = self.dossier()
            current["representations"][0]["art_review"]["authored_candidate"]["png"] = (
                "authored-candidate/a.png"
            )
            before["representations"][0]["art_review"]["authored_candidate"]["png"] = (
                "authored-candidate/a.png"
            )
            current["representations"][0]["art_review"]["authored_candidate"][
                "rgba_sha256"
            ] = "current"
            before["representations"][0]["art_review"]["authored_candidate"][
                "rgba_sha256"
            ] = "before"

            current_eq = self.equivalence()
            baseline_eq = self.equivalence()
            current_eq["pose_groups"][0]["authored_asset_rgba_sha256"] = "current"
            baseline_eq["pose_groups"][0]["authored_asset_rgba_sha256"] = "before"

            dossier.write_text(json.dumps(current))
            equivalence.write_text(json.dumps(current_eq))
            baseline_dossier.write_text(json.dumps(before))
            baseline_equivalence.write_text(json.dumps(baseline_eq))
            source_png = baseline_root / "authored-candidate" / "a.png"
            source_png.parent.mkdir()
            source_png.write_bytes(b"baseline-png")

            out = root / "review"
            manifest = build_review_packet(
                dossier,
                equivalence,
                out,
                baseline_dossier_path=baseline_dossier,
                baseline_equivalence_path=baseline_equivalence,
            )

            self.assertEqual(
                manifest["baseline_comparison"]["changed_authored_pose_count"], 1
            )
            self.assertEqual(
                manifest["baseline_comparison"]["copied_authored_png_count"], 1
            )
            self.assertTrue(
                (out / "baseline" / "p1-pose-001.png").is_file()
            )
            html = (out / "index.html").read_text()
            self.assertIn("Before · authored 4× inspection", html)
            self.assertIn("After · gameplay footprint", html)

    def test_packet_renders_live_frames_at_known_native_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier = root / "manifest.json"
            equivalence = root / "equivalence.json"
            dossier.write_text(json.dumps(self.dossier()))
            equivalence.write_text(json.dumps(self.equivalence()))

            original = root / "original.ppm"
            hd = root / "hd.ppm"
            original.write_bytes(
                b"P6\n256 224\n255\n" + bytes([1, 2, 3]) * (256 * 224)
            )
            hd.write_bytes(
                b"P6\n1024 896\n255\n" + bytes([4, 5, 6]) * (1024 * 896)
            )

            out = root / "review"
            manifest = build_review_packet(
                dossier, equivalence, out, original, hd
            )

            self.assertEqual(
                manifest["live_reference"]["original_dimensions"], [256, 224]
            )
            self.assertEqual(
                manifest["live_reference"]["hd_dimensions"], [1024, 896]
            )
            self.assertTrue((out / "live-original.png").is_file())
            self.assertTrue((out / "live-hd.png").is_file())
            html = (out / "index.html").read_text()
            self.assertIn("2 exact guards → 1 unique poses", html)
            self.assertIn("After · gameplay footprint", html)
            self.assertIn("Live split-screen reference", html)
            self.assertIn("Alpha mismatch", html)
            self.assertIn('x="2" y="3"', html)
            self.assertIn('x="4" y="5"', html)


if __name__ == "__main__":
    unittest.main()
