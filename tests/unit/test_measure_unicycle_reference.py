"""Proofs for image-hash-bound projected likeness proportions, not shipping art."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from tools.art.measure_unicycle_reference import measure, SCHEMA


def synthetic_png(width=160, height=120):
    """Create a valid *synthetic* PNG; never retain redistributed original art."""
    def chunk(name, data):
        return (struct.pack(">I", len(data)) + name + data +
                struct.pack(">I", zlib.crc32(name + data) & 0xffffffff))
    rgba = bytes([0, 0, 0, 0])
    rows = (b"\x00" + rgba * width) * height
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) +
            chunk(b"IEND", b""))


class ReferenceLandmarkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = synthetic_png()
        (self.root / "synthetic.png").write_bytes(self.data)
        self.record = {
            "id": "synthetic-side-not-an-original-reference",
            "source": {
                "url": "https://example.org/illustrative-source",
                "kind": "artist-blockout",
                "creator_or_credit": "test fixture",
                "region_or_version": "synthetic",
                "capture_context": "generated clean source / arbitrary coordinates",
                "rights_notes": "self-created synthetic test; no real character art",
            },
            "image": {
                "path": "synthetic.png",
                "sha256": hashlib.sha256(self.data).hexdigest(),
            },
            "view": {
                "angle": "side",
                "pose": "synthetic neutral",
                "pixel_aspect": "square",
                "crop_and_rescale_history": "none; generated 160x120 source",
            },
            "annotator": "test harness",
            "landmarks": {
                "wheel_left": [50, 70],
                "wheel_right": [110, 70],
                "wheel_top": [80, 40],
                "wheel_bottom": [80, 100],
                "saddle_left": [65, 15],
                "saddle_right": [95, 15],
                "saddle_top": [80, 10],
                "saddle_bottom": [80, 25],
                "crown_left": [70, 35],
                "crown_right": [90, 35],
                "fork_left": [72, 55],
                "fork_right": [88, 55],
                "axle": [80, 70],
                "pedal_center": [95, 75],
            },
        }

    def run_manifest(self, views=None):
        path = self.root / "views.json"
        path.write_text(json.dumps({
            "schema": SCHEMA,
            "views": [self.record] if views is None else views,
        }), encoding="utf-8")
        return measure(path)

    def test_ratios_are_projected_perspective_bound_and_not_approval(self):
        report = self.run_manifest()
        self.assertEqual(report["view_count"], 1)
        rec = report["views"][0]
        self.assertEqual(rec["image_sha256"], self.record["image"]["sha256"])
        self.assertEqual(rec["source_kind"], "artist-blockout")
        r = rec["projected_ratios"]
        self.assertEqual(r["wheel_width_over_wheel_height"], 1)
        self.assertEqual(r["saddle_width_over_wheel_diameter"], 0.5)
        self.assertEqual(r["saddle_height_over_wheel_diameter"], 0.25)
        self.assertEqual(r["saddle_top_minus_wheel_top_over_wheel_diameter"], -0.5)
        self.assertEqual(r["pedal_horizontal_offset_over_wheel_diameter"], 0.25)
        self.assertEqual(r["crown_width_over_wheel_diameter"], 0.333333)
        self.assertEqual(r["fork_spread_over_wheel_diameter"], 0.266667)
        self.assertFalse(report["three_dimensional_character_proportions_proven"])
        self.assertFalse(report["current_character_likeness_approved"])
        self.assertFalse(report["shipping_art_approved"])
        self.assertNotIn("synthetic.png", json.dumps(report))

    def test_pixel_aspect_distinguishes_rom_sample_and_square_pixels(self):
        self.record["view"]["pixel_aspect"] = "snes_7_6"
        rec = self.run_manifest()["views"][0]
        self.assertEqual(rec["projected_ratios"]["wheel_width_over_wheel_height"], 1.166667)
        self.assertEqual(rec["projected_ratios"]["saddle_width_over_wheel_diameter"], 0.583333)
        self.assertEqual(rec["projected_ratios"]["saddle_height_over_wheel_diameter"], 0.25)

    def test_occluded_features_report_null_and_explanation(self):
        for key in ("crown_left", "crown_right", "fork_left", "fork_right",
                    "axle", "pedal_center"):
            del self.record["landmarks"][key]
        self.record["unmeasurable"] = {
            "crown": "hidden behind saddle", "fork": "hidden",
            "axle": "not rendered", "pedal": "not rendered",
        }
        rec = self.run_manifest()["views"][0]
        self.assertIsNone(rec["projected_ratios"]["fork_spread_over_wheel_diameter"])
        self.assertIsNone(rec["projected_ratios"]["pedal_horizontal_offset_over_wheel_diameter"])
        del self.record["unmeasurable"]["axle"]
        with self.assertRaisesRegex(ValueError, "explain why"):
            self.run_manifest()

    def test_partial_feature_and_false_visibility_reason_fail_closed(self):
        del self.record["landmarks"]["fork_right"]
        with self.assertRaisesRegex(ValueError, "partial fork"):
            self.run_manifest()
        self.record["landmarks"]["fork_right"] = [88, 55]
        self.record["unmeasurable"] = {"fork": "not visible"}
        with self.assertRaisesRegex(ValueError, "mark fork or explain"):
            self.run_manifest()

    def test_hash_swap_source_url_and_local_path_traversal_rejected(self):
        self.record["image"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            self.run_manifest()
        self.record["image"]["sha256"] = hashlib.sha256(self.data).hexdigest()
        self.record["source"]["url"] = "http://example.org/fake"
        with self.assertRaisesRegex(ValueError, "public HTTPS"):
            self.run_manifest()
        self.record["source"]["url"] = "https://example.org/original"
        self.record["image"]["path"] = "../another-scan.png"
        with self.assertRaisesRegex(ValueError, "traversal"):
            self.run_manifest()

    def test_invalid_landmarks_and_duplicate_views_rejected(self):
        before = deepcopy(self.record)
        for coord in ([999, 20], [float("nan"), 20], [True, 12]):
            self.record["landmarks"]["wheel_left"] = coord
            with self.subTest(coord=coord), self.assertRaises(ValueError):
                self.run_manifest()
        self.record = deepcopy(before)
        self.record["landmarks"]["wheel_left"] = [120, 60]
        with self.assertRaisesRegex(ValueError, "inverted wheel"):
            self.run_manifest()
        self.record = deepcopy(before)
        self.record["landmarks"]["wheel_top"] = [80, 100]
        with self.assertRaisesRegex(ValueError, "inverted wheel"):
            self.run_manifest()
        self.record = deepcopy(before)
        with self.assertRaisesRegex(ValueError, "duplicate reference IDs"):
            self.run_manifest([self.record, deepcopy(self.record)])

    def test_multiple_reference_angles_retained_not_falsely_reconciled(self):
        second = deepcopy(self.record)
        second["id"] = "synthetic-three-quarter"
        second["view"]["angle"] = "three-quarter"
        second["view"]["pose"] = "expressive"
        report = self.run_manifest([self.record, second])
        self.assertEqual(report["view_count"], 2)
        self.assertEqual([v["view_angle"] for v in report["views"]],
                         ["side", "three-quarter"])
        self.assertFalse(report["three_dimensional_character_proportions_proven"])


if __name__ == "__main__":
    unittest.main()
