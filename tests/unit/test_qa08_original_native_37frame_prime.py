"""Adversarial exact 37-frame original/native video and capture-only source hook."""
from pathlib import Path
import tempfile
import unittest

from tools.qa08_patch_native_original_37frame_source import patch, patch_host
from tools.qa08_compare_original_native_37frame_prime import (
    W, H, NATIVE_SIZE, compare, native_frames, ORIGINAL_START,
)


def original_pixel_buffer():
    # Synthetic SNES RGB565 expansion: original G6=166 -> native G5=165.
    return bytes((165, 166, 132, 0)) * (W * H)


def native_pixel_buffer():
    return bytes((132, 165, 165, 255)) * (W * H)


def synthetic():
    original = [(frame, original_pixel_buffer(), f"synthetic-frame-{frame}")
                for frame in range(ORIGINAL_START, ORIGINAL_START + 37)]
    pairs = {fr + 1: (native_pixel_buffer(), f"candidate-{fr+1}")
             for fr, _, _ in original}
    return original, pairs


CRC = b"0xA091EF13\n" * 50 + b"0x0AAB8FFE\n" * 2423


class MultiFrameOriginalSourceTests(unittest.TestCase):
    def test_only_capture_branch_changes_disposable_cpp(self):
        source = (Path(__file__).resolve().parents[2] /
                  "tools/baldosa_native_racer_presentation.cpp").read_text()
        altered = patch(source)
        self.assertIn("UR_QA08_AUTHENTIC_37FRAME_SOURCE_CAPTURE", altered)
        self.assertIn('std::strcmp(qa08_window, "source-window-37")', altered)
        self.assertIn("g_frame >= 2189u && g_frame <= 2225u", altered)
        self.assertEqual(altered.count('"ur-baldosa-original-source"'),
                         source.count('"ur-baldosa-original-source"'))
        with self.assertRaisesRegex(ValueError, "already present"):
            patch(altered)
        with self.assertRaisesRegex(ValueError, "changed"):
            patch(source.replace('    const char* live = ', '    const char* other = '))

    def test_completed_simulation_host_hook_is_pinned_and_preserves_draw(self):
        host = (
            "static const SnesDesktopHostGame kGameHost = {\n"
            "    .begin_sim_frame    = &ur_baldosa_hd_begin_sim_frame,\n"
            "    .draw_frame         = &ur_baldosa_hd_draw_frame,\n"
            "};\n"
        )
        changed = patch_host(host)
        self.assertIn(".end_sim_frame      = &ur_qa08_original_source_37_end_sim_frame,", changed)
        self.assertIn(".draw_frame         = &ur_baldosa_hd_draw_frame,", changed)
        self.assertEqual(changed.count("UR_QA08_AUTHENTIC_37FRAME_SOURCE_CAPTURE"), 1)
        with self.assertRaisesRegex(ValueError, "already present"):
            patch_host(changed)
        with self.assertRaisesRegex(ValueError, "ABI changed"):
            patch_host(host.replace("begin_sim_frame", "before_run_frame"))

    def test_thirty_seven_true_source_pairs_and_repeated_guest_CRCs(self):
        original, baseline = synthetic()
        native = dict(baseline)
        report = compare(original, baseline, native, CRC, CRC)
        self.assertEqual(report["frames_compared_exact"], 37)
        self.assertEqual(report["original_vs_consumed_prime_RGB5_full_matching_frame_count"], 37)
        self.assertTrue(report["original_vs_consumed_prime_all_37_source_pixels_exact"])
        self.assertFalse(report["upstream_cross_game_HDMA_first_line_compatibility_proven"])
        self.assertEqual(report["comparisons"][0]["native_guest_frame"], 2189)
        self.assertEqual(report["comparisons"][-1]["native_guest_frame"], 2225)

    def test_one_colour_pixel_on_one_guest_frame_is_not_waived(self):
        original, baseline = synthetic()
        changed = dict(baseline)
        pix = bytearray(changed[2193][0])
        pix[0] ^= 1
        changed[2193] = (bytes(pix), "altered-source")
        report = compare(original, baseline, changed, CRC, CRC)
        self.assertEqual(report["original_vs_consumed_prime_RGB5_full_matching_frame_count"], 36)
        self.assertEqual(report["status"], "source-37frame-original-native-counterexamples-retained")
        row = next(r for r in report["comparisons"] if r["native_guest_frame"] == 2193)
        self.assertEqual(row["experimental_vs_unmodified_native_exact_changed_RGBA_source_pixels"], 1)

    def test_missing_crc_or_missing_frame_never_earns_37_frame_credit(self):
        original, baseline = synthetic()
        for bad in (b"", CRC[:-1], b"0x1234FFFF\n" * 2473):
            with self.subTest(length=len(bad)):
                with self.assertRaisesRegex(ValueError, "incomplete or divergent"):
                    compare(original, baseline, baseline, CRC, bad)
        short = dict(baseline)
        del short[2190]
        with self.assertRaisesRegex(ValueError, "incomplete or divergent"):
            compare(original, short, baseline, CRC, CRC)

    def test_native_source_filename_and_P7_exact_size_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            for frame in range(2189, 2226):
                (directory / f"ur-baldosa-original-source-{frame:06d}.pam").write_bytes(
                    NATIVE_SIZE + native_pixel_buffer())
            # The baseline SHA pin intentionally rejects synthetic files.
            with self.assertRaisesRegex(ValueError, "SHA-accepted"):
                native_frames(directory, "unchanged")
            self.assertEqual(len(native_frames(directory, "experiment")), 37)
            (directory / "ur-baldosa-original-source-002190.pam").write_bytes(
                NATIVE_SIZE + native_pixel_buffer()[:-1])
            with self.assertRaisesRegex(ValueError, "not true"):
                native_frames(directory, "experiment")


if __name__ == "__main__":
    unittest.main()
