"""Source-hash-backed projected character motion; no shipping art acceptance."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from tools.art.audit_unicycle_pose_sequence import audit
from tools.art.measure_unicycle_reference import SCHEMA


def png(width=160, height=120):
    def chunk(name, data):
        return (struct.pack(">I", len(data)) + name + data +
                struct.pack(">I", zlib.crc32(name + data) & 0xffffffff))
    rows = (b"\x00" + bytes((0, 0, 0, 0)) * width) * height
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class ProjectedRacerMotionAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = png()
        (self.root / "source.png").write_bytes(self.original)
        self.view = {
            "id": "same-camera-frame0",
            "source": {
                "url": "https://example.org/own-synthetic-racer",
                "kind": "artist-blockout",
                "creator_or_credit": "synthetic unit test",
                "region_or_version": "synthetic",
                "capture_context": "no original game content",
                "rights_notes": "entirely self-generated pixels",
            },
            "image": {
                "path": "source.png",
                "sha256": hashlib.sha256(self.original).hexdigest(),
            },
            "view": {
                "angle": "side",
                "pose": "neutral",
                "pixel_aspect": "square",
                "crop_and_rescale_history": "source 160x120 no crop",
            },
            "annotator": "test",
            "landmarks": {
                "wheel_left": [50, 80], "wheel_right": [110, 80],
                "wheel_top": [80, 45], "wheel_bottom": [80, 105],
                "saddle_left": [65, 20], "saddle_right": [95, 20],
                "saddle_top": [80, 15], "saddle_bottom": [80, 25],
                "crown_left": [72, 40], "crown_right": [88, 40],
                "fork_left": [72, 55], "fork_right": [88, 55],
                "axle": [80, 80], "pedal_center": [90, 75],
            },
        }
        self.second = deepcopy(self.view)
        self.second["id"] = "same-camera-frame1"
        self.second["view"]["pose"] = "turning"
        self.second["landmarks"]["saddle_left"] = [70, 20]
        self.second["landmarks"]["saddle_right"] = [100, 20]
        self.second["landmarks"]["saddle_top"] = [85, 15]
        self.second["landmarks"]["saddle_bottom"] = [85, 25]
        self.sequence = {
            "id": "test-sequence",
            "camera_mode": "declared-fixed",
            "camera_notes": "synthetic test source has unchanged camera/crop",
            "frames": [
                {"reference_id": self.view["id"], "time_ms": 0},
                {"reference_id": self.second["id"], "time_ms": 50},
            ],
        }

    def run_manifest(self):
        manifest = self.root / "measure.json"
        manifest.write_text(json.dumps({
            "schema": SCHEMA,
            "views": [self.view, self.second],
            "sequences": [self.sequence],
        }), encoding="utf-8")
        return audit(manifest)

    def test_source_bound_registered_motion_reports_real_projected_change(self):
        result = self.run_manifest()
        self.assertEqual(result["validated_source_view_count"], 2)
        self.assertEqual(result["sequence_count"], 1)
        r = result["sequences"][0]
        self.assertEqual(r["frame_count"], 2)
        self.assertTrue(r["source_tags_consistent_for_fixed_projection"])
        self.assertEqual(r["adjacent_projected_changes"][0]["elapsed_ms"], 50)
        self.assertEqual(
            r["adjacent_projected_changes"][0]["projected_metric_deltas"]
            ["saddle_center_x_from_wheel_center_over_diameter"], 0.083333)
        self.assertEqual(
            r["metric_spans_over_sequence"]
            ["saddle_center_x_from_wheel_center_over_diameter"], 0.083333)
        self.assertFalse(r["fixed_physical_3d_camera_independently_proven"])
        self.assertFalse(result["shipping_art_approved"])
        self.assertFalse(result["original_character_likeness_approved"])
        self.assertNotIn("source.png", json.dumps(result))

    def test_real_pixel_aspect_changes_normalized_horizontal_pose_metric(self):
        self.view["view"]["pixel_aspect"] = "snes_7_6"
        self.second["view"]["pixel_aspect"] = "snes_7_6"
        r = self.run_manifest()["sequences"][0]
        self.assertEqual(
            r["metric_spans_over_sequence"]
            ["saddle_center_x_from_wheel_center_over_diameter"], 0.097222)

    def test_fixed_camera_rejects_mismatched_crop_and_angle(self):
        self.second["view"]["angle"] = "three-quarter"
        with self.assertRaisesRegex(ValueError, "fixed projection"):
            self.run_manifest()
        self.second["view"]["angle"] = "side"
        self.second["view"]["crop_and_rescale_history"] = "different crop"
        with self.assertRaisesRegex(ValueError, "fixed projection"):
            self.run_manifest()

    def test_uncertain_camera_preserves_measurements_without_pretending_alignment(self):
        self.sequence["camera_mode"] = "unverified-or-moving"
        self.second["view"]["angle"] = "three-quarter"
        r = self.run_manifest()["sequences"][0]
        self.assertFalse(r["source_tags_consistent_for_fixed_projection"])
        self.assertFalse(r["fixed_physical_3d_camera_independently_proven"])
        self.assertEqual(len(r["adjacent_projected_changes"]), 1)

    def test_frame_time_order_duplicate_missing_reference_and_bool_fail_closed(self):
        self.sequence["frames"][1]["time_ms"] = 0
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            self.run_manifest()
        self.sequence["frames"][1]["time_ms"] = True
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            self.run_manifest()
        self.sequence["frames"][1]["time_ms"] = 50
        self.sequence["frames"][1]["reference_id"] = self.view["id"]
        with self.assertRaisesRegex(ValueError, "duplicate frame reference"):
            self.run_manifest()
        self.sequence["frames"][1]["reference_id"] = "unmeasured"
        with self.assertRaisesRegex(ValueError, "reference absent"):
            self.run_manifest()

    def test_mixed_source_and_pixel_aspect_rejected(self):
        self.second["source"]["region_or_version"] = "a different source"
        with self.assertRaisesRegex(ValueError, "mixed source identity"):
            self.run_manifest()
        self.second["source"]["region_or_version"] = "synthetic"
        self.second["view"]["pixel_aspect"] = "snes_7_6"
        with self.assertRaisesRegex(ValueError, "mixed source identity"):
            self.run_manifest()

    def test_swapped_png_or_fake_hash_rejected_before_motion_report(self):
        self.second["image"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            self.run_manifest()
        self.second["image"]["sha256"] = hashlib.sha256(self.original).hexdigest()
        (self.root / "source.png").write_bytes(png(168, 120))
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            self.run_manifest()

    def test_no_implicit_motion_or_artistic_approval_without_sequence(self):
        self.sequence["frames"] = self.sequence["frames"][:1]
        with self.assertRaisesRegex(ValueError, "at least two"):
            self.run_manifest()
        self.sequence["frames"] = [
            {"reference_id": self.view["id"], "time_ms": 0},
            {"reference_id": self.second["id"], "time_ms": 50},
        ]
        self.sequence["camera_mode"] = "automatically-proven"
        with self.assertRaisesRegex(ValueError, "camera mode must be explicit"):
            self.run_manifest()


if __name__ == "__main__":
    unittest.main()
