import pathlib
import unittest

from tools.check_racer_hd_wide_visual_parity import compare_series


def make_series(rows):
    """(frame, state label, image digest) -> screenshot records."""
    result = {}
    for frame, label, digest in rows:
        # Eight independently compared state coordinates. The P1 companion
        # is the discriminator at the accepted 0541/0540 witness.
        state = (
            "0x0541" if label == "witness" else f"0x{0x0540 + frame % 4:04X}",
            "0x0540",
            "0x0D2D" if label == "witness" else f"0x{0x0D00 + frame:04X}",
            "0x0000", 0, 0, "0x0001", "0x0000",
        )
        result[frame] = {"state": state, "sha256": {digest}}
    return result


class NativeWidePixelParityTests(unittest.TestCase):
    def test_equal_present_frames_match_without_shift(self):
        a = make_series([(frame, "witness" if frame == 15 else "ordinary",
                          f"sha-{frame}") for frame in range(10, 20)])
        b = make_series([(frame, "witness" if frame == 15 else "ordinary",
                          f"sha-{frame}") for frame in range(10, 20)])
        report = compare_series(a, b)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["selected_guest_frame_offset"], 0)
        self.assertEqual(report["pixel_exact_matched_frames"], 10)

    def test_two_frame_presentation_offset_has_exact_raster_parity(self):
        a = make_series([(frame, "witness" if frame == 15 else "ordinary",
                          f"sha-{frame}") for frame in range(10, 22)])
        b = {
            frame - 2: item
            for frame, item in a.items()
        }
        report = compare_series(a, b)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["selected_guest_frame_offset"], -2)
        self.assertEqual(report["different_image_frames"], 0)

    def test_same_state_with_corrupted_pixel_digest_is_rejected(self):
        a = make_series([(frame, "witness" if frame == 15 else "ordinary",
                          f"sha-{frame}") for frame in range(10, 20)])
        b = make_series([(frame, "witness" if frame == 15 else "ordinary",
                          f"sha-{frame}") for frame in range(10, 20)])
        b[17]["sha256"] = {"changed"}
        report = compare_series(a, b)
        self.assertFalse(report["ok"])
        self.assertEqual(report["different_image_frames"], 1)
        self.assertEqual(report["pixel_exact_matched_frames"], 9)

    def test_unaligned_states_are_not_compared_by_image_similarity(self):
        a = make_series([(frame, "witness" if frame == 15 else "ordinary",
                          f"sha-{frame}") for frame in range(10, 20)])
        b = make_series([(frame, "witness" if frame == 15 else "ordinary",
                          f"sha-{frame}") for frame in range(10, 20)])
        for row in b.values():
            row["state"] = ("unrelated",) * 8
        with self.assertRaisesRegex(ValueError, "semantic-aligned"):
            compare_series(a, b)

    def test_tie_in_semantic_offset_refuses_guessing(self):
        state = ("same",) * 8
        a = {frame: {"state": state, "sha256": {"sha"}} for frame in range(10, 20)}
        b = {frame: {"state": state, "sha256": {"sha"}} for frame in range(10, 20)}
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            compare_series(a, b)

    def test_matching_without_approved_racer_witness_fails(self):
        a = make_series([(frame, "ordinary", f"sha-{frame}")
                         for frame in range(10, 20)])
        report = compare_series(a, dict(a))
        self.assertFalse(report["ok"])
        self.assertFalse(report["registration_witness_0541_0540_0d2d"])


if __name__ == "__main__":
    unittest.main()
