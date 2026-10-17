"""Fail closed on the earliest original/native 1P+2P cursor source receipt."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "analysis/data/qa08-early-cursor-crossmode-source-20261016.json"

class EarlyCursorSourceTest(unittest.TestCase):
    def test_pinned_full_RGB5_1p_2p_source_disposition(self):
        data = json.loads(DATA.read_text())
        self.assertEqual(data["source_pairs_verified_per_mode"], 25)
        self.assertEqual(data["unmasked_pixel_count_per_source_frame"], 256 * 224)
        self.assertEqual(data["pixels_compared_1p_plus_2p"], 2 * 25 * 256 * 224)
        self.assertEqual(data["real_capture_frame_guests"], [1280, 1664, 16])
        self.assertTrue(data["no_cropping_masking_shifting_recoloring_or_inferred_frames"])
        self.assertEqual(data["authentic_original_video_frame_registration"],
                         "original_callback=Windows_guest-1; no frame search")
        for mode, total, first, bbox in (
            ("oneplayer", 1050, 254, [54, 193, 85, 210]),
            ("twoplayer", 4487, 245, [32, 65, 63, 80]),
        ):
            witness = data[mode]
            counts = witness["wrong_pixel_counts_by_native_guest_frame"]
            self.assertEqual(len(counts), 25)
            self.assertEqual(counts[0], first)
            self.assertEqual(sum(counts), total)
            self.assertEqual(witness["total_wrong_RGB5_pixels_in_bounded_window"], total)
            self.assertEqual(witness["first_divergent_native_guest"], 1280)
            self.assertEqual(witness["first_divergent_bounding_box_xyxy"], bbox)
            self.assertEqual(counts[-1], 0)
        self.assertEqual(data["most_frequent_exact_original_to_native_color_substitution"][
            "original_RGB5_expanded"], [90, 74, 82])
        self.assertEqual(data["most_frequent_exact_original_to_native_color_substitution"][
            "compiled_Windows_RGBA_rgb"], [90, 66, 74])
        self.assertEqual(data["most_frequent_exact_original_to_native_color_substitution"][
            "occurrences_1p"], 480)
        self.assertEqual(data["most_frequent_exact_original_to_native_color_substitution"][
            "occurrences_2p"], 3035)
        for hash_value in data["source_ZIP_sha256"].values():
            self.assertEqual(len(hash_value), 64)
            int(hash_value, 16)
        self.assertFalse(data["original_native_CGRAM_palette_words_math_flags_and_effective_sprite_priority_proven"])
        self.assertFalse(data["source_colour_remap_or_renderer_fix_admitted"])
        self.assertFalse(data["unrelated_SNESRecomp_global_change_admitted"])
        self.assertFalse(data["qa08_qa10_release_and_HD_racer_likeness_accepted"])

if __name__ == "__main__":
    unittest.main()
