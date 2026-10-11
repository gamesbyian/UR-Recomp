"""Adversarial genuine live-1P original physical 4K mode/SSA provenance."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_1p_physical_4k_mode_binding import (
    verify, ORIGINAL_1P_SOURCE_SHA, ORIGINAL_1P_4X_SHA,
    ORIGINAL_2P_SOURCE_SHA, ORIGINAL_2P_PHYSICAL_SHA, FRAME,
    PHYSICAL_LINE, PRESENT,
)


class NativeLiveOnePlayer4kModeBindingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.report = root / "native-physical.json"
        self.log = root / "native-host.log"
        self.data = {
            "schema_version": 1,
            "status": "exact-native-capture-pixel-parity",
            "frame": FRAME,
            "source_ppu_size": [342, 224],
            "native_density_size": [1368, 896],
            "physical_capture_size": [3840, 2160],
            "output_viewport": [0, 0, 3840, 2160],
            "original_pixel_aspect": [7, 6],
            "wide_horizontal_fit": [512, 513],
            "sdl2_software_nearest_fixed_point_bits": 16,
            "native_density_and_output_distinct": True,
            "full_height_224_rows_preserved": True,
            "opaque_sdl_drawable_alpha_expected": 255,
            "original_ppu_alpha_is_not_output_opacity": True,
            "rgba_source_sha256": ORIGINAL_1P_SOURCE_SHA,
            "rgba_density_sha256": ORIGINAL_1P_4X_SHA,
            "rgba_capture_sha256": "3" * 64,
        }
        self.host = ("UR_BALDOSA_WS342_LIVE_MODE frame=550 mode=1 "
                     "guest_race=3C frontend=3C\n" +
                     PRESENT + "\n" + PHYSICAL_LINE + "\n")
        self.flush()

    def flush(self):
        self.report.write_text(json.dumps(self.data), encoding="utf-8")
        self.log.write_text(self.host, encoding="utf-8")

    def test_independent_correct_oneplayer_pixels_and_log_pass(self):
        out = verify(self.report, self.log)
        self.assertEqual(out["status"],
                         "accepted-live-1p-same-guest-original-physical-4k-provenance")
        self.assertEqual(out["live_oneplayer_mode_activated_at_guest_frame"], 550)
        self.assertEqual(out["independently_accepted_original_oneplayer_source_sha256"],
                         ORIGINAL_1P_SOURCE_SHA)
        self.assertFalse(out["physical_pixels_rechecked_by_this_report"])
        self.assertFalse(out["hd_art_or_modern_display_mode_admitted"])

    def test_twoplayer_same_guest_original_source_is_rejected(self):
        self.data["rgba_source_sha256"] = ORIGINAL_2P_SOURCE_SHA
        self.flush()
        with self.assertRaisesRegex(ValueError, "live 1P pixels"):
            verify(self.report, self.log)

    def test_internally_scaled_same_mode_but_wrong_source_is_rejected(self):
        self.data["rgba_source_sha256"] = "a" * 64
        self.flush()
        with self.assertRaisesRegex(ValueError, "live 1P pixels"):
            verify(self.report, self.log)

    def test_wrong_4x_density_original_source_rejected(self):
        self.data["rgba_density_sha256"] = "a" * 64
        self.flush()
        with self.assertRaisesRegex(ValueError, "live 1P pixels"):
            verify(self.report, self.log)

    def test_fake_physical_same_as_internal_texture_rejected(self):
        self.data["rgba_capture_sha256"] = ORIGINAL_1P_4X_SHA
        self.flush()
        with self.assertRaisesRegex(ValueError, "wrong mode"):
            verify(self.report, self.log)

    def test_twoplayer_physical_image_cannot_be_substituted(self):
        self.data["rgba_capture_sha256"] = ORIGINAL_2P_PHYSICAL_SHA
        self.flush()
        with self.assertRaisesRegex(ValueError, "wrong mode"):
            verify(self.report, self.log)

    def test_centered_original_viewport_cannot_pass_for_widened_1p(self):
        self.data["output_viewport"] = [480, 0, 2880, 2160]
        self.flush()
        with self.assertRaisesRegex(ValueError, "geometry/parity"):
            verify(self.report, self.log)

    def test_missing_actual_sdl_readpixels_marker_rejected(self):
        self.host = self.host.replace(PHYSICAL_LINE, "")
        self.flush()
        with self.assertRaisesRegex(ValueError, "actual full drawable"):
            verify(self.report, self.log)

    def test_repeated_sdl_capture_is_not_a_single_authentic_frame(self):
        self.host += PHYSICAL_LINE + "\n"
        self.flush()
        with self.assertRaisesRegex(ValueError, "actual full drawable"):
            verify(self.report, self.log)

    def test_wrong_or_missing_live_oneplayer_state_is_rejected(self):
        self.host = self.host.replace("mode=1", "mode=2")
        self.flush()
        with self.assertRaisesRegex(ValueError, "live 1P mode"):
            verify(self.report, self.log)

    def test_original_guest_frame_not_same_as_readback_frame_rejected(self):
        self.data["frame"] = 1872
        self.flush()
        with self.assertRaisesRegex(ValueError, "geometry/parity"):
            verify(self.report, self.log)

    def test_fake_partial_or_wrong_format_capture_hash_rejected(self):
        self.data["rgba_capture_sha256"] = "not-a-sha"
        self.flush()
        with self.assertRaisesRegex(ValueError, "wrong mode"):
            verify(self.report, self.log)

    def test_rejected_native_4k_readback_cannot_pass(self):
        self.host += (
            "UR_BALDOSA_PHYSICAL_4K_CAPTURE_REJECT frame=2208 "
            "reason=not-real-4k-drawable output=1368x896\n"
        )
        self.flush()
        with self.assertRaisesRegex(ValueError, "was rejected"):
            verify(self.report, self.log)


if __name__ == "__main__":
    unittest.main()
