"""Offline QA-08 original/Windows RGB5 verifier: assert strict fail-closed paths."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa08_verify_windows_four_scene_source as qa  # noqa: E402


class OriginalSourceRgb5Test(unittest.TestCase):
    def test_g6_to_g5_is_only_original_conversion(self):
        raw = bytearray(qa.PX * 4)
        raw[0:4] = bytes([0x21, 0xA7, 0xFF, 0x00])
        rgb = qa.decode_original(bytes(raw))
        green5 = (0xA7 >> 3)
        self.assertEqual(rgb[:3], bytes([0xFF, ((green5 << 3) | (green5 >> 2)), 0x21]))
        self.assertEqual(rgb[3:6], bytes([0,0,0]))
        with self.assertRaises(ValueError):
            qa.decode_original(bytes(raw[:-1]))

    def test_p7_is_actual_full_native_source_without_scale(self):
        pixels = bytearray(qa.PX * 4)
        pixels[:4] = bytes([1, 2, 3, 255])
        rgb = qa.decode_p7(qa.PAM_HEADER + pixels)
        self.assertEqual(rgb[:3], bytes([1, 2, 3]))
        self.assertEqual(len(rgb), qa.PX * 3)
        for bad in (
            qa.PAM_HEADER + pixels[:-1],
            qa.PAM_HEADER.replace(b"WIDTH 256", b"WIDTH 216") + pixels,
        ):
            with self.assertRaises(ValueError):
                qa.decode_p7(bad)

    def test_mismatches_exactly_by_pixel_and_source_row(self):
        ref = bytearray(qa.PX*3)
        stock = bytearray(ref)
        new = bytearray(ref)
        stock[(111*256+0)*3] = 0xFF
        stock[(113*256+255)*3] = 0xFF
        result = qa.compare_rgb(ref, stock, new)
        self.assertEqual(result["previous_wrong"], 2)
        self.assertEqual(result["corrected_wrong"], 0)
        self.assertEqual(result["corrected_source_changed_pixels"], 2)
        self.assertEqual(result["source_changed_rows"], {111: 1, 113: 1})
        new[(111*256+1)*3] = 0xFF
        bad = qa.compare_rgb(ref, stock, new)
        self.assertEqual(bad["corrected_wrong"], 1)
        self.assertNotEqual(bad["source_changed_rows"], {111: 1, 113: 1})
        with self.assertRaises(ValueError):
            qa.compare_rgb(ref[:-1], stock, new)

    def test_original_artifact_identity_cannot_be_assumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.zip"
            path.write_bytes(b"fake screenshot.zip")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                qa.open_exact(path, "windows")

    def test_historical_four_scene_2p_control_remains_not_release_gate(self):
        import json
        data = json.loads((ROOT / "analysis/data/"
              "qa08-real-original-native-postgo-3frame-rgb5-parity-20261014.json"
              ).read_text(encoding="utf-8"))
        self.assertEqual([x["native_guest"] for x in data["verified_frame_pairs"]],
                         [2192,2208,2224])
        for row in data["verified_frame_pairs"]:
            self.assertEqual(row["wrong_normalized_original_RGB5_pixels"]["stock"], 512)
            self.assertEqual(row["wrong_normalized_original_RGB5_pixels"]["global"], 0)
        self.assertEqual(data["contrast_countdown_native1856_original1855_wrong"]["stock"], 971)
        self.assertEqual(data["contrast_countdown_native1856_original1855_wrong"]["global"], 0)
        self.assertFalse(data["production_renderer_correction_authorized"])


if __name__ == "__main__":
    unittest.main()
