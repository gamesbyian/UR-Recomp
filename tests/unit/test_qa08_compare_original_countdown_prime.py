"""QA-08 independent original 17-frame countdown and anchored native source pairing."""
from io import BytesIO
import zipfile
import unittest
from unittest.mock import patch

from tools import qa08_compare_original_countdown_prime as target


def source_rgb565():
    return bytes((165, 166, 132, 0)) * (256 * 224)


def native_rgb5():
    return bytes((132, 165, 165, 0)) * (256 * 224)


def witness():
    v = native_rgb5()
    return {
        "stock": v, "global_prime": v,
        "stock_p7_sha256": target.BASELINE_SHA,
        "global_prime_p7_sha256": target.TRIAL_SHA,
    }


def zipped():
    out = BytesIO()
    p7 = target.P7_HEADER + native_rgb5()
    with zipfile.ZipFile(out, "w") as z:
        for root in (target.BASE_PREFIX, target.TRIAL_PREFIX):
            z.writestr(f"{root}/ur-baldosa-original-source-001856.pam", p7)
        crc = b"".join(f"{i:04d}:{i:08x}\n".encode() for i in range(2473))
        z.writestr("qa08-counterfactual/baseline/fd/crc.txt", crc)
        z.writestr("qa08-counterfactual/experiment/fd/crc.txt", crc)
    return out.getvalue(), p7


class OriginalCountdownNativePrimeTests(unittest.TestCase):
    def test_source_17_full_images_no_fake_phase_promotion(self):
        frames = {f: source_rgb565() for f in target.WINDOW}
        result = target.compare(frames, witness())
        self.assertEqual(len(result["results"]), 17)
        self.assertEqual(result["prespecified_original_callback_for_native_guest1856"], 1855)
        self.assertFalse(result["original_guest_state_and_source_PPU_event_phase_equivalence_proven"])
        self.assertFalse(result["original_hardware_raster_or_global_prime_correctness_proven"])
        self.assertEqual(result["prespecified_phase_global_prime_minus_stock_matching_pixels"], 0)
        self.assertEqual(result["ranked_native_source_comparisons"]["stock"]["best_original_callback"], 1848)

    def test_real_source_differences_are_counted_at_fixed_phase(self):
        frames = {f: source_rgb565() for f in target.WINDOW}
        b = bytearray(native_rgb5())
        b[0] = 0
        v = witness()
        v["stock"] = bytes(b)
        result = target.compare(frames, v)
        self.assertEqual(result["prespecified_phase_global_prime_minus_stock_matching_pixels"], 1)
        self.assertTrue(result["does_prespecified_global_prime_match_more_original_pixels"])
        selected = result["results"][1855 - target.WINDOW[0]]
        self.assertEqual(selected["stock_different_pixels"], 1)
        self.assertEqual(selected["global_prime_different_pixels"], 0)

    def test_forged_frame_count_and_pixel_format_fail_closed(self):
        source = {f: source_rgb565() for f in target.WINDOW}
        for incorrect in ({**source, 1866: source_rgb565()},
                          {f: v for f, v in source.items() if f != 1850}):
            with self.assertRaisesRegex(ValueError, "exactly 17"):
                target.compare(incorrect, witness())
        broken = dict(source)
        broken[1855] = broken[1855][:-4]
        with self.assertRaisesRegex(ValueError, "truncated"):
            target.compare(broken, witness())
        broken = dict(source)
        pixels = bytearray(broken[1855])
        pixels[1] = 167
        broken[1855] = bytes(pixels)
        with self.assertRaisesRegex(ValueError, "RGB565"):
            target.compare(broken, witness())

    def test_native_archive_requires_real_executable_sha_and_P7(self):
        blob, p7 = zipped()
        with self.assertRaisesRegex(ValueError, "ZIP SHA"):
            target.native(blob)
        with patch.object(target, "BASELINE_SHA", target.sha(p7)), patch.object(
                target, "TRIAL_SHA", target.sha(p7)):
            values = target.native(blob, strict_archive=False)
            self.assertEqual(len(values["stock"]), 256 * 224 * 4)
            self.assertEqual(values["stock"], values["global_prime"])
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            target.native(b"no archive", strict_archive=False)


if __name__ == "__main__":
    unittest.main()
