"""Source-size native first-line HDMA experiment: three real frames and adversaries."""
import copy
import hashlib
import unittest
from unittest import mock

from tools import qa08_compare_native_prime_multiframe as target


def raster(*, seam=(), changed=None):
    header = target.HEADER
    pixels = bytearray()
    for y in range(target.H):
        for x in range(target.W):
            color = (0, 0, 0) if y in seam else (96, 128, 160)
            if changed == (x, y):
                color = (255, 0, 0)
            pixels.extend((*color, 255))
    return header + bytes(pixels)


CRC = b"".join(f"guest {i:04d}: {i:08X}\n".encode() for i in range(2473))


def source():
    return {
        400: raster(),
        1856: raster(),
        2208: raster(seam=(112, 113)),
    }


class PrimeMultiFrameTests(unittest.TestCase):
    def test_no_other_frame_change_is_reported_without_approving_product(self):
        before = source()
        after = copy.deepcopy(before)
        after[2208] = raster(seam=(111, 112))
        with mock.patch.object(target, "BASELINE_REAL_SHA256",
                               hashlib.sha256(before[2208]).hexdigest()):
            r = target.check(before, after, CRC, CRC)
        self.assertEqual(r["total_source_pixels_compared"], 172032)
        self.assertTrue(r["all_non2208_source_frames_unchanged"])
        self.assertEqual(r["non2208_source_frames_with_visible_differences"], [])
        self.assertEqual([x["changed_source_RGBA_pixels"]
                          for x in r["full_real_PPU_source_frame_dispositions"]],
                         [0, 0, 512])
        self.assertTrue(r["full_real_PPU_source_frame_dispositions"][2][
            "matches_2208_accepted_exact_seam_correction"])
        self.assertFalse(r["native_production_HDMA_correction_authorized"])

    def test_independent_unexpected_frontend_delta_is_preserved_not_masked(self):
        before = source()
        after = copy.deepcopy(before)
        after[400] = raster(changed=(123, 77))
        after[1856] = raster(changed=(47, 202))
        after[2208] = raster(seam=(111, 112))
        with mock.patch.object(target, "BASELINE_REAL_SHA256",
                               hashlib.sha256(before[2208]).hexdigest()):
            result = target.check(before, after, CRC, CRC)
        self.assertEqual(result["non2208_source_frames_with_visible_differences"],
                         [400, 1856])
        self.assertFalse(result["all_non2208_source_frames_unchanged"])
        self.assertEqual(result["full_real_PPU_source_frame_dispositions"][0][
            "changed_output_rows"], [{"y": 77, "count": 1}])

    def test_wrong_source_frame_and_crc_rejected(self):
        b = source()
        a = copy.deepcopy(b)
        a[2208] = raster(seam=(111, 112))
        with mock.patch.object(target, "BASELINE_REAL_SHA256",
                               hashlib.sha256(b[2208]).hexdigest()):
            for bad in [dict(b, **{9999: raster()}),
                        {400: b[400], 2208: b[2208]}]:
                with self.assertRaisesRegex(ValueError, "all three"):
                    target.check(bad, a, CRC, CRC)
            with self.assertRaisesRegex(ValueError, "CRC"):
                target.check(b, a, CRC, CRC + b"x")
            with self.assertRaisesRegex(ValueError, "256x224"):
                t = copy.deepcopy(a)
                t[1856] = t[1856][:-4]
                target.check(b, t, CRC, CRC)

    def test_visual_near_match_does_not_invent_exact_seam(self):
        b = source()
        t = copy.deepcopy(b)
        t[2208] = raster(seam=(111, 112), changed=(20, 150))
        with mock.patch.object(target, "BASELINE_REAL_SHA256",
                               hashlib.sha256(b[2208]).hexdigest()):
            with self.assertRaisesRegex(ValueError, "independently proven seam"):
                target.check(b, t, CRC, CRC)

    def test_known_real_2208_hash_cannot_be_guessed_or_relaxed(self):
        b = source()
        t = copy.deepcopy(b)
        t[2208] = raster(seam=(111, 112))
        with self.assertRaisesRegex(ValueError, "accepted reference"):
            target.check(b, t, CRC, CRC)


if __name__ == "__main__":
    unittest.main()
