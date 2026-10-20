"""Adversarial tests for genuine native title/root PAM receipt admission.

These synthetic bytes are *negative-path fixtures only*; success requires an
actual pinned Windows EXE and source-correct artwork, never fixture screenshots.
"""
import tempfile
import unittest
from pathlib import Path

from tools.capture_baldosa_modern_title_win32 import (
    read_pam, retail_art_digest, fnv_pixels, validate_native_capture,
    EXPECTED_RETAIL_BGR_FNV,
)


def pam(width: int, height: int, pixels: bytes) -> bytes:
    return (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
            "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode() + pixels


class ModernTitleNativeCaptureTests(unittest.TestCase):
    def test_bad_header_and_dimensions_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "capture.pam"
            path.write_bytes(b"invalid")
            with self.assertRaisesRegex(ValueError, "not an actual"):
                read_pam(path)
            path.write_bytes(pam(342, 224, b""))
            with self.assertRaisesRegex(ValueError, "geometry"):
                read_pam(path)
            path.write_bytes(pam(256, 224, bytes(256 * 224 * 4)))
            with self.assertRaisesRegex(ValueError, "geometry"):
                read_pam(path)
            path.write_bytes(pam(342, 224, bytes(342 * 224 * 4)))
            self.assertEqual(read_pam(path)[:2], (342, 224))

    def test_digest_guards_reject_reconstructed_fake_stock_art(self):
        self.assertEqual(fnv_pixels(b""), 1469598103934665603)
        raster = bytes(342 * 224 * 4)
        self.assertNotEqual(retail_art_digest(342, raster),
                            EXPECTED_RETAIL_BGR_FNV)

    def test_missing_real_witness_refuses_pam_approval(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            for stage in ("title", "root"):
                (folder / f"modern-native-{stage}-342x224.pam").write_bytes(
                    pam(342, 224, bytes(342 * 224 * 4)))
            with self.assertRaisesRegex(ValueError, "missing/out-of-order"):
                validate_native_capture(folder, "", exe_sha256="invalid")
            with self.assertRaisesRegex(ValueError, "missing/out-of-order"):
                validate_native_capture(
                    folder, "UR_BALDOSA_MODERN_ROOT opened=1\n",
                    exe_sha256="invalid")

    def test_fake_log_cannot_turn_empty_pixels_into_real_art(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            for stage in ("title", "root"):
                (folder / f"modern-native-{stage}-342x224.pam").write_bytes(
                    pam(342, 224, bytes(342 * 224 * 4)))
            contents = "\n".join((
                "UR_BALDOSA_MODERN_ROOT opened=1",
                "UR_BALDOSA_MODERN_TITLE native_p1_start=1 frame=60",
                "UR_BALDOSA_MODERN_TITLE entered_root=1",
                "UR_BALDOSA_MODERN_ROOT painted=1",
            ))
            with self.assertRaisesRegex(ValueError, "implausibly uniform"):
                validate_native_capture(folder, contents, exe_sha256="invalid")


if __name__ == "__main__":
    unittest.main()
