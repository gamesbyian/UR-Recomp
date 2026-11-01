"""Fast, ROM-free tests for leakage-free wheel hypothesis holdout evaluation."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[2] / "tools/art/evaluate_original_racer_wheel_holdout.py"
spec = importlib.util.spec_from_file_location("art4k_wheel_holdout", MODULE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def shapes():
    return {
        tool.FIRST: {"a"*64, "b"*64},
        "third-family": {"c"*64, "d"*64},
        "third-family-duplicate": {"d"*64, "e"*64},
        "other-family": {"f"*64},
        "first-family-duplicate": {"b"*64, "g"*64},
    }


class OriginalHoldoutTests(unittest.TestCase):
    def test_shared_original_binary_shapes_cannot_cross_holdout(self):
        result = tool.split_family_components(shapes())
        self.assertEqual(result["fit_connected_windows"],
                         ["first-1205-1220", "first-family-duplicate"])
        self.assertEqual(result["withheld_connected_window_components"],
                         [["other-family"], ["third-family", "third-family-duplicate"]])
        self.assertEqual(result["independent_holdout_mask_count"], 4)
        self.assertEqual(set(result["fit_binary_shas"]), {"a"*64, "b"*64, "g"*64})
        self.assertFalse(set(result["fit_binary_shas"]) &
                         set(result["withheld_binary_shas"]))

    def test_no_fake_holdout_from_repeated_frames(self):
        only_duplicates = {
            tool.FIRST: {"a"*64},
            "second": {"a"*64},
            "third": {"a"*64},
        }
        result = tool.split_family_components(only_duplicates)
        self.assertEqual(result["independent_holdout_mask_count"], 0)
        self.assertEqual(result["fit_connected_windows"], sorted(only_duplicates))

    def test_invalid_window_or_missing_first_fails(self):
        for case in (
            {tool.FIRST: {"a"*64}},
            {"other": {"a"*64}, "second": {"b"*64}},
            {tool.FIRST: set(), "other": {"b"*64}},
            {tool.FIRST: {"a"}, "other": {"b"*64}},
        ):
            with self.subTest(case=case), self.assertRaises(ValueError):
                tool.split_family_components(case)

    def test_half_pixel_anchor_is_exact_at_four_x(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("optional NumPy not installed")
        mask = np.zeros((256, 256), dtype=np.uint8)
        mask[38:43, 38:43] = 1
        baseline = tool.translated_4x_source_mask(mask, tool.BASE_ANCHOR)
        # A +1 step in x2 units is a HALF logical pixel, i.e. two 4x
        # samples, not one rounded full pixel.
        x2 = tool.translated_4x_source_mask(
            mask, (tool.BASE_ANCHOR[0]+1, tool.BASE_ANCHOR[1]))
        self.assertNotEqual(baseline, x2)
        self.assertEqual(len(x2), 4096)
        self.assertTrue(any(x2))
        self.assertEqual(sum(tool.translated_4x_source_mask(
            mask, (tool.BASE_ANCHOR[0]+2, tool.BASE_ANCHOR[1]))), 1)

    def test_source_registered_clipping_is_rejected(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("optional NumPy not installed")
        mask = np.zeros((256, 256), dtype=np.uint8)
        mask[3:7, 1:5] = 1
        with self.assertRaisesRegex(ValueError, "clip"):
            tool.translated_4x_source_mask(
                mask, (tool.BASE_ANCHOR[0]-1, tool.BASE_ANCHOR[1]))
        with self.assertRaises(ValueError):
            tool.translated_4x_source_mask(
                np.zeros((64, 64), dtype=np.uint8), tool.BASE_ANCHOR)


if __name__ == "__main__":
    unittest.main()
