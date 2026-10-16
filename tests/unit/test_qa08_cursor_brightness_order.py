"""Adversarial and mathematical guards for source-pinned QA-08 cursor colour order."""
import copy
import json
from pathlib import Path
import unittest
from tools import qa08_cursor_brightness_order as target

ROOT = Path(__file__).resolve().parents[2]


class QA08CursorBrightnessOrderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.early = json.loads((ROOT / "analysis/data/qa08-early-cursor-crossmode-source-20261016.json").read_text())
        cls.toolchain = json.loads((ROOT / "tools/toolchain.json").read_text())

    def test_precise_colour_discriminator(self):
        got = target.analyze(self.early, self.toolchain)
        self.assertEqual(got["pinned_Snes9x_palette_first_RGB8_counterfactual"], [90, 74, 82])
        self.assertEqual(got["pinned_native_half_first_RGB8_counterfactual"], [90, 66, 74])
        self.assertEqual(got["source_original_subscreen_CGRAM_word"], "1889")
        for key in ("correctly_registered_original_original_effective_BG1_and_OBJ_pixel_layers_proven",
                    "physical_SNES_color_math_order_proven", "renderer_code_change_authorized",
                    "all_cursor_pixels_explained", "all_transition_or_result_pixels_explained",
                    "QA08_QA10_HD_art_or_release_acceptance"):
            self.assertIs(got[key], False, key)

    def test_full_brightness_and_black_cannot_discriminate_order(self):
        for level in (0, 15):
            self.assertEqual(
                target.brighten_before_blend(target.RAW_MAIN_RGB5, target.RAW_SUB_RGB5, level),
                target.blend_before_brightness(target.RAW_MAIN_RGB5, target.RAW_SUB_RGB5, level))

    def test_bad_colour_or_source_pin_fails_closed(self):
        broken = copy.deepcopy(self.early)
        broken["most_frequent_exact_original_to_native_color_substitution"]["original_RGB5_expanded"][1] -= 8
        with self.assertRaisesRegex(ValueError, "image-colour"):
            target.analyze(broken, self.toolchain)
        broken = copy.deepcopy(self.toolchain)
        next(t for t in broken["tools"] if t.get("id") == "snes9x-libretro")["revision"] = "unverified"
        with self.assertRaisesRegex(ValueError, "source pin"):
            target.analyze(self.early, broken)

    def test_invalid_math_input_rejected(self):
        for args in ((32, 14), (14, 16), (-1, 14)):
            with self.assertRaises(ValueError):
                target.brighten(*args)
        with self.assertRaises(ValueError):
            target.brighten_before_blend((1,), (2,), 14)


if __name__ == "__main__":
    unittest.main()
