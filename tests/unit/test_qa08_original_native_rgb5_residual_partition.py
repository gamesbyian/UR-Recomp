"""Guard source-pinned 1P and 2P original versus compiled Windows residual taxonomy."""
import json
from pathlib import Path
import unittest

DATA = Path(__file__).resolve().parents[2] / "analysis/data/qa08-original-native-rgb5-residual-partition-20261016.json"

class SourceResidualPartition(unittest.TestCase):
    def test_all_samples_and_negative_release_limits(self):
        d = json.loads(DATA.read_text())
        self.assertEqual(d["geometry"], [256,224])
        self.assertIn("no masking", d["pixel_normalization"])
        self.assertIn("never dynamic phase search", d["source_original_callback_for_native_guest"])
        for h in d["source_2014_Snes9x_and_compiled_Windows_ZIP_SHA256"].values():
            self.assertEqual(len(h), 64)
            int(h, 16)
        for key in ("original_native_CPU_instruction_camera_or_field_phase_proven",
                    "effective_PPU_OBJ_BG_window_and_colour_math_proven",
                    "physical_PAR_widescreen_4x_HD_likeness_release_admitted"):
            self.assertFalse(d[key])

    def test_oneplayer_full_frame_error_conservation(self):
        q = json.loads(DATA.read_text())["oneplayer"]
        self.assertEqual((q["sampled_frames"],q["exact_frames"],q["divergent_frames"]),(261,162,99))
        self.assertEqual(q["wrong_RGB5_pixels"],19153)
        self.assertEqual(q["moving_race_wrong_pixels"],0)
        self.assertLessEqual(q["max_wrong_bbox_width"],32)
        self.assertLessEqual(q["max_wrong_bbox_height"],18)
        self.assertEqual(sum(q[k]["pixels"] for k in ("initial_menu","finish_transition","results_and_return")),19153)
        self.assertEqual(sum(q[k]["frames"] for k in ("initial_menu","finish_transition","results_and_return")),99)
        self.assertEqual(sum(q["distinct_bbox_left_edge_counts"].values()),99)
        self.assertEqual(q["finish_transition"]["guests"],[3968,3984,4000])

    def test_two_player_disjoint_source_pixel_error_partition(self):
        q = json.loads(DATA.read_text())["twoplayer"]
        self.assertEqual((q["sampled_frames"],q["exact_frames"],q["divergent_frames"]),(263,203,60))
        self.assertEqual(q["wrong_RGB5_pixels"],385373)
        rest=q["all_other_errors"]
        self.assertEqual(q["original_native_blackout"]["pixels"]+
                         q["original_native_four_gray_CGRAM_phase"]["pixels"]+
                         rest["pixels"],385373)
        icon=rest["results_medal_colours"]
        self.assertEqual(rest["early_menu_cursor"]["pixels"]+
                         rest["finish_isolated_pixels"]["pixels"]+
                         icon["pixels"],rest["pixels"])
        self.assertEqual(icon["pixels"],25*296)
        self.assertEqual(len(icon["nongray_frames_with_identical_mismatch_mask"]),21)
        self.assertEqual(len(set(icon["nongray_frames_with_identical_mismatch_mask"])),21)
        self.assertEqual(icon["nongray_mask_bbox_xyxy"],[202,91,227,153])
        self.assertEqual(icon["additional_four_gray_phase_frames_with_296_residual_pixels"],4)

if __name__ == "__main__":
    unittest.main()
