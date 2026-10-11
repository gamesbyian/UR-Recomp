"""Reproducible alpha-only model constraints from authenticated native 1P PPU."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.art.compare_native_1p_silhouettes import compare
from tools.check_baldosa_wide_single_slot_source import (
    HEADER, WIDTH, HEIGHT, read_source,
)


class NativeSilhouetteComparisonTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.files = {
            slot: root / f"ur-baldosa-ws342-obj-slot{slot}-frame002208.pam"
            for slot in (98, 99)
        }
        self.report = root / "ws342_live_1p_top_slot98_99_source.json"
        self.pixels = {slot: bytearray(WIDTH * HEIGHT * 4) for slot in (98, 99)}
        # Different higher silhouette geometry, exact horizontally-translated
        # lower source silhouette on 16 source raster rows 128..143.
        self.paint(98, 101, 127)
        self.paint(99, 54, 126)
        for y in range(128, 144):
            for dx in (0, 1, 2):
                self.paint(98, 101 + dx, y)
                self.paint(99, 51 + dx, y)
        self.flush()

    def paint(self, slot, x, y):
        offset = (y * WIDTH + x) * 4
        self.pixels[slot][offset:offset + 4] = bytes(
            (slot, 10, 70, 255))

    def flush(self):
        records = []
        for slot in (98, 99):
            self.files[slot].write_bytes(HEADER + self.pixels[slot])
            native = read_source(self.files[slot], slot)
            records.append({
                "original_oam_slot": slot,
                "original_1x_and_4x_remained_pixel_identical": True,
                "native_source": native,
                "rgba_sha256": native["source_sha256"],
            })
        self.report.write_text(json.dumps({
            "schema_version": 1,
            "status": "native-1p-paired-top-oam-source-truth",
            "native_guest_frame": 2208,
            "native_original_guest_crc_identical": 5447,
            "native_1x_and_4x_source_frames_identical": 7,
            "independent_original_guest_processes": 5,
            "no_sprite_removal_or_guest_mutation": True,
            "source_slot_emission_accepted": True,
            "individual_final_bg_or_obj_priority_accepted": False,
            "authored_hd_or_wide_replacement_accepted": False,
            "windows_beta_accepted": False,
            "original_top_slot98_and_slot99_sources": records,
        }), encoding="utf-8")

    def test_consecutive_16_rows_match_but_different_upper_rows_do_not(self):
        result = compare(self.files[98], self.files[99], self.report)
        self.assertEqual(result["native_guest_frame"], 2208)
        self.assertEqual(result["longest_contiguous_identical_nonempty_alpha_rows"],
                         [128, 143])
        self.assertEqual(result["longest_identical_row_count"], 16)
        self.assertEqual(result["exactly_matching_source_alpha_rows"], 16)
        self.assertEqual(result["overlapping_occupied_absolute_source_rows"], 16)
        self.assertEqual(result["source_98_opaque_pixels"], 49)
        self.assertEqual(result["source_99_opaque_pixels"], 49)
        self.assertEqual(result["logical_pixel_aspect_ratio"], "7:6")
        self.assertFalse(result["original_3d_model_or_part_identity_proven"])
        self.assertFalse(result["new_art_approved"])
        self.assertFalse(result["final_bg_or_obj_ownership_proven"])

    def test_changing_one_lower_pixel_breaks_exact_row_and_run(self):
        self.pixels[99][(134 * WIDTH + 51) * 4 + 3] = 0
        self.flush()
        result = compare(self.files[98], self.files[99], self.report)
        self.assertEqual(result["exactly_matching_source_alpha_rows"], 15)
        self.assertEqual(result["longest_contiguous_identical_nonempty_alpha_rows"],
                         [135, 143])
        self.assertEqual(result["longest_identical_row_count"], 9)

    def test_palette_difference_alone_does_not_change_alpha_result(self):
        base = compare(self.files[98], self.files[99], self.report)
        for i in range(0, len(self.pixels[99]), 4):
            if self.pixels[99][i + 3]:
                self.pixels[99][i:i + 3] = bytes((22, 201, 41))
        self.flush()
        after = compare(self.files[98], self.files[99], self.report)
        self.assertEqual(base["all_equal_source_alpha_rows"],
                         after["all_equal_source_alpha_rows"])
        self.assertNotEqual(base["source_original_99_rgba_sha256"],
                            after["source_original_99_rgba_sha256"])
        self.assertEqual(base["source_99_alpha_sha256"],
                         after["source_99_alpha_sha256"])

    def test_swapped_source_or_forged_native_report_rejected(self):
        with self.assertRaisesRegex(ValueError, "slot"):
            compare(self.files[99], self.files[98], self.report)
        recorded = json.loads(self.report.read_text())
        recorded["original_top_slot98_and_slot99_sources"][0]["rgba_sha256"] = "0" * 64
        self.report.write_text(json.dumps(recorded))
        with self.assertRaisesRegex(ValueError, "digest"):
            compare(self.files[98], self.files[99], self.report)


if __name__ == "__main__":
    unittest.main()
