"""Adversarial original 2P source-frame selection; synthetic fixtures are not source evidence."""
import unittest

from tools.qa08_rank_original_postgo_motion import (
    assess, check_original_frame, compare_original_frames, W, H,
)

P = bytes((0, 0, 0, 0))
SIZE = W * H * 4


def trio():
    return {frame: bytes(SIZE) for frame in (2191, 2207, 2223)}


class OriginalPostGoMotionTests(unittest.TestCase):
    def test_synthetic_motion_is_not_native_acceptance(self):
        frames = trio()
        changed = bytearray(frames[2191])
        for y, x in ((20, 17), (111, 90), (180, 10)):
            start = 4 * (y * W + x)
            changed[start:start + 4] = bytes((8, 0, 0, 0))
        frames[2223] = bytes(changed)
        result = assess(frames)
        self.assertEqual(result["real_original_full_RGB_pairwise_differences"][-1][
            "total_changed_RGB_pixels"], 3)
        self.assertEqual(result["real_original_full_RGB_pairwise_differences"][-1][
            "top_rows_0_to_110_changed_RGB_pixels"], 1)
        self.assertEqual(result["real_original_full_RGB_pairwise_differences"][-1][
            "split_rows_111_to_112_changed_RGB_pixels"], 1)
        self.assertEqual(result["real_original_full_RGB_pairwise_differences"][-1][
            "bottom_rows_113_to_223_changed_RGB_pixels"], 1)
        self.assertFalse(result["native_host_has_emitted_these_additional_frames"])
        self.assertFalse(result["release_or_renderer_promotion_authorized"])

    def test_full_source_or_format_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "complete"):
            check_original_frame(bytes(SIZE - 1))
        altered = bytearray(SIZE)
        altered[1] = 166  # Valid RGB565 green6 expansion but not zero, accepted.
        check_original_frame(bytes(altered))
        altered[3] = 1
        with self.assertRaisesRegex(ValueError, "RGB565"):
            check_original_frame(bytes(altered))

    def test_original_source_mismatched_frame_set_rejected(self):
        frames = trio()
        frames.pop(2191)
        with self.assertRaisesRegex(ValueError, "exact preselected"):
            assess(frames)

    def test_original_source_colour_channel_rejected(self):
        a = bytes(SIZE)
        b = bytearray(a)
        b[0] = 9
        with self.assertRaisesRegex(ValueError, "blue"):
            compare_original_frames(a, bytes(b))


if __name__ == "__main__":
    unittest.main()
