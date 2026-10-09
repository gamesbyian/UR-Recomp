"""Real 342-wide cross-density image-oracle regression tests."""
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_wide_density_parity import (
    HEADER1, HEADER4, LOGICAL_HEIGHT, LOGICAL_WIDTH, assess, capture_files
)
from tools.baldosa_ws24_presentation_report import restore_logical_nearest


def logical_frame(shade: int) -> bytes:
    return bytes(
        channel
        for y in range(LOGICAL_HEIGHT)
        for x in range(LOGICAL_WIDTH)
        for channel in (x & 255, y & 255, shade, 255)
    )


def expand_four(logical: bytes) -> bytes:
    out = bytearray()
    for y in range(LOGICAL_HEIGHT):
        src = logical[y * LOGICAL_WIDTH * 4:(y + 1) * LOGICAL_WIDTH * 4]
        row = b"".join(src[x * 4:x * 4 + 4] * 4
                       for x in range(LOGICAL_WIDTH))
        for _ in range(4):
            out.extend(row)
    return bytes(out)


class BaldosaWideNativeParityTests(unittest.TestCase):
    def test_real_capture_headers_and_same_frame_exactness(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            one, four = root / "one", root / "four"
            one.mkdir()
            four.mkdir()
            for frame, shade in ((1808, 10), (1856, 20), (1888, 30)):
                original = logical_frame(shade)
                rendered = expand_four(original)
                filename = f"ur-baldosa-ws342-{frame:06d}.pam"
                (one / filename).write_bytes(HEADER1 + original)
                (four / filename).write_bytes(HEADER4 + rendered)
            lhs = capture_files(one, 1)
            rhs = capture_files(four, 4)
            good = assess(lhs, rhs, min_shared_frames=2)
            self.assertEqual(good["status"], "passed")
            self.assertEqual(good["exact_image_pairs"], 3)
            self.assertEqual(good["shared_guest_frames"], 3)
            self.assertTrue(all(x["all_4x4_blocks_exact"] for x in good["compared_frames"]))

            # A completely uniform wrong 4x logical pixel evades nearest
            # block-only validation but must fail against the native 1x source.
            bad = bytearray(rhs[1856])
            for y in range(4):
                for x in range(4):
                    at = (y * LOGICAL_WIDTH * 4 + x) * 4
                    bad[at:at + 4] = bytes((222, 77, 99, 255))
            recovered, exact = restore_logical_nearest(
                bad, LOGICAL_WIDTH, LOGICAL_HEIGHT, 4)
            self.assertTrue(exact)
            self.assertNotEqual(recovered, lhs[1856])
            bad_out = assess(lhs, {**rhs, 1856: bytes(bad)}, min_shared_frames=2)
            self.assertEqual(bad_out["status"], "unproven")
            self.assertFalse(bad_out["compared_frames"][1]["all_logical_pixels_identical"])
            self.assertTrue(bad_out["compared_frames"][1]["all_4x4_blocks_exact"])

            # One altered physical subpixel violates both nearest expansion
            # and cross-density parity.
            bad[4] ^= 1
            subpixel = assess(lhs, {**rhs, 1856: bytes(bad)}, min_shared_frames=2)
            self.assertEqual(subpixel["status"], "unproven")
            self.assertFalse(subpixel["compared_frames"][1]["all_4x4_blocks_exact"])

            # The same image from the wrong guest frame earns no alignment.
            self.assertEqual(assess(lhs, {2020: rhs[1808]},
                                    min_shared_frames=2)["status"], "unproven")
            with self.assertRaises(ValueError):
                assess(lhs, rhs, min_shared_frames=1)

            bad_name = one / "ur-baldosa-ws342-unknown.pam"
            bad_name.write_bytes(HEADER1 + logical_frame(0))
            with self.assertRaisesRegex(ValueError, "Malformed"):
                capture_files(one, 1)
            bad_name.unlink()
            file = four / "ur-baldosa-ws342-001808.pam"
            file.write_bytes(HEADER1 + lhs[1808])
            with self.assertRaisesRegex(ValueError, "Invalid native 4x"):
                capture_files(four, 4)


if __name__ == "__main__":
    unittest.main()
