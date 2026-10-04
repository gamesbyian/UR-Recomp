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
                        "shipping_art_approved": False,
                        "authored_candidate": {
                            "png": "authored-candidate/a.png",
                            "approval_status": "motion-reviewed",
                            "gameplay_scale_review": {"alpha_iou": 0.75},
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
                        "shipping_art_approved": False,
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
            self.assertIn("Authored at gameplay footprint", html)
            self.assertIn("Live split-screen reference", html)


if __name__ == "__main__":
    unittest.main()
