"""Original native PPU top slots98/99 require separate source, not a guessed HD rider."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_oneplayer_top_oam_sources import (
    observed_rgb, classify_top_source_pair, assess,
)


class OnePlayerTopOriginalSourcesTests(unittest.TestCase):
    def test_isolated_native_alpha_is_not_authoritative_final_layer_ownership(self):
        orig = bytearray(bytes((43, 66, 88, 0)) * (342 * 224))
        slot = bytearray(bytes((0, 0, 0, 0)) * (342 * 224))
        first = (118 * 342 + 116) * 4
        second = (119 * 342 + 117) * 4
        slot[first:first + 4] = bytes((43, 66, 88, 255))
        slot[second:second + 4] = bytes((245, 20, 60, 255))
        pixels = observed_rgb(bytes(orig), bytes(slot))
        self.assertEqual(pixels["isolated_source_opaque"], 2)
        self.assertEqual(pixels["source_rgb_equal_final_original"], 1)
        self.assertEqual(pixels["source_rgb_different_final_original"], 1)
        self.assertFalse(pixels["final_ppu_owner_proven"])
        slot[:] = bytes(len(slot))
        self.assertEqual(observed_rgb(bytes(orig), bytes(slot))["isolated_source_opaque"], 0)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            observed_rgb(bytes(orig[:-4]), bytes(slot))

    def test_real_plane_pair_overlap_is_not_final_ppu_ownership(self):
        width, height = 342, 224
        finished = bytearray(bytes((0, 0, 0, 255)) * (width * height))
        p1 = bytearray(width * height * 4)
        p2 = bytearray(width * height * 4)

        def paint(plane, x, y, rgb):
            i = (y * width + x) * 4
            plane[i:i + 4] = bytes((*rgb, 255))

        paint(p1, 1, 1, (1, 2, 3))
        paint(finished, 1, 1, (1, 2, 3))
        paint(p2, 2, 2, (4, 5, 6))  # Exclusive emission, not final RGB
        paint(p1, 3, 3, (10, 20, 30))
        paint(p2, 3, 3, (50, 60, 70))
        paint(finished, 3, 3, (10, 20, 30))
        paint(p1, 4, 4, (70, 10, 10))
        paint(p2, 4, 4, (10, 10, 70))  # Neither matches final RGB
        paint(p1, 5, 150, (7, 8, 9))
        paint(p2, 5, 150, (7, 8, 9))
        paint(finished, 5, 150, (7, 8, 9))
        paint(p1, 6, 151, (255, 255, 255))  # Bottom exclusive mismatch

        a = classify_top_source_pair(bytes(finished), bytes(p1), bytes(p2))
        self.assertEqual(a["viewport_split_y"], 112)
        self.assertEqual(a["emitted_slot98_pixels"], 5)
        self.assertEqual(a["emitted_slot99_pixels"], 4)
        self.assertEqual(a["distinct_emitted_coordinates"], 6)
        self.assertEqual(a["total_counts"]["slot98_only"], 2)
        self.assertEqual(a["total_counts"]["slot99_only"], 1)
        self.assertEqual(a["total_counts"]["shared"], 3)
        self.assertEqual(a["total_counts"]["shared_source_rgb_conflict"], 2)
        self.assertEqual(a["total_counts"]["shared_final_matches_98_only"], 1)
        self.assertEqual(a["total_counts"]["shared_final_matches_neither"], 1)
        self.assertEqual(a["total_counts"]["shared_final_matches_both"], 1)
        self.assertEqual(a["total_counts"]["exclusive99_rgb_differs_final"], 1)
        self.assertEqual(a["total_counts"]["exclusive98_rgb_differs_final"], 1)
        self.assertEqual(a["band_counts"]["top"]["shared"], 2)
        self.assertEqual(a["band_counts"]["bottom"]["shared"], 1)
        self.assertEqual(a["bounded_coordinate_examples"]["conflicting_shared"],
                         [[3, 3], [4, 4]])
        self.assertEqual(a["bounded_coordinate_examples"]["shared_matches_neither"],
                         [[4, 4]])
        self.assertFalse(a["final_pixel_ownership_or_HD_admission_proven"])
        self.assertEqual(sum(a["total_counts"][key] for key in
                             ("slot98_only", "slot99_only", "shared", "neither")),
                         width * height)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            classify_top_source_pair(bytes(finished), bytes(p1[:-4]), bytes(p2))
        with self.assertRaisesRegex(ValueError, "dimensions"):
            classify_top_source_pair(bytes(finished[:-4]), bytes(p1), bytes(p2))

    def test_pair_census_all_transparent_is_valid_negative(self):
        blank = bytes(342 * 224 * 4)
        a = classify_top_source_pair(blank, blank, blank)
        self.assertEqual(a["distinct_emitted_coordinates"], 0)
        self.assertEqual(a["total_counts"]["shared"], 0)
        self.assertEqual(a["total_counts"]["neither"], 342 * 224)
        self.assertFalse(a["final_pixel_ownership_or_HD_admission_proven"])

    def test_wrong_original_guest_identity_and_frames_fail_before_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stock, one, four = (root / p for p in ("base.crc", "one.crc", "four.crc"))
            stock.write_bytes(b"00000000\n" * 5447)
            one.write_bytes(stock.read_bytes())
            for probe in (root / "probe98.crc", root / "probe99.crc"):
                probe.write_bytes(stock.read_bytes())
            four.write_bytes(stock.read_bytes()[:-9])
            with self.assertRaisesRegex(ValueError, "CRC"):
                assess(stock, one, four, root, root,
                       root / "slot98.pam", root / "slot99.pam",
                       root / "one.log", root / "four.log", root, root,
                       root / "probe98.crc", root / "probe99.crc")
            four.write_bytes(stock.read_bytes())
            with self.assertRaisesRegex(ValueError, "only guest2208"):
                assess(stock, one, four, root, root,
                       root / "slot98.pam", root / "slot99.pam",
                       root / "one.log", root / "four.log", root, root,
                       root / "probe98.crc", root / "probe99.crc", frame=2224)
            with self.assertRaisesRegex(ValueError, "Missing real native"):
                assess(stock, one, four, root, root,
                       root / "slot98.pam", root / "slot99.pam",
                       root / "one.log", root / "four.log", root, root,
                       root / "probe98.crc", root / "probe99.crc")

    def test_native_workflow_retains_existing_bottom_controls_and_separately_isolates_top(self):
        root = Path(__file__).resolve().parents[2]
        wf = (root / ".github/workflows/baldosa-core-spike.yml").read_text()
        self.assertIn("tools/check_baldosa_oneplayer_top_oam_sources.py", wf)
        self.assertIn("ws342_live_1p_top_slot98_99_source.json", wf)
        self.assertIn('for slot in 98 99; do', wf)
        self.assertIn('UR_RACER_HD_WIDE_SOURCE_FRAME=2208', wf)
        self.assertIn('UR_BALDOSA_WS342_LATE_CAPTURE_AFTER=2200', wf)
        self.assertIn('race_1p_ur_ws342_live_probe_slot$slot', wf)
        self.assertIn('probe98-dir', wf)
        self.assertIn('probe99-dir', wf)
        self.assertIn('tools/check_baldosa_oneplayer_bottom_oam_sources.py', wf)
        # The separate native sources may report empty and must leave final
        # source PPU BG/OBJ priorities and 342-wide HD entirely unchanged.
        self.assertNotIn('UR_RACER_HD_WIDE_REMOVE_DIAGNOSTIC=counterfactual',
                         wf[wf.index('for slot in 98 99; do'):
                            wf.index('tools/check_baldosa_oneplayer_top_oam_sources.py')])


if __name__ == "__main__":
    unittest.main()
