"""Adversarial tests for genuine native title/root PAM receipt admission.

These synthetic bytes are *negative-path fixtures only*; success requires an
actual pinned Windows EXE and source-correct artwork, never fixture screenshots.
"""
import tempfile
import unittest
from pathlib import Path

from tools.capture_baldosa_modern_title_win32 import (
    read_pam, retail_art_digest, fnv_pixels, validate_native_capture,
    EXPECTED_RETAIL_BGR_FNV, read_present_ppm,
    verify_native_presented_frames,
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


    def test_host_presented_images_reject_missing_csv_and_bad_ppm(self):
        with tempfile.TemporaryDirectory() as root:
            present = Path(root) / "presented"
            present.mkdir()
            with self.assertRaisesRegex(ValueError, "missing native present"):
                verify_native_presented_frames(present, present.parent / "captures")
            ppm = present / "present_000000.ppm"
            ppm.write_bytes(b"P6\n342 224\n255\n" + bytes(2))
            with self.assertRaisesRegex(ValueError, "dimensions"):
                read_present_ppm(ppm)
            ppm.write_bytes(b"not a ppm")
            with self.assertRaisesRegex(ValueError, "not a host P6"):
                read_present_ppm(ppm)

    def test_host_presented_source_matches_before_SDL_upload(self):
        # Synthetic negative/algorithm fixtures only. The production
        # candidate and original title digest are separately required.
        with tempfile.TemporaryDirectory() as root:
            where = Path(root)
            presented = where / "presented"
            source = where / "captures"
            presented.mkdir()
            source.mkdir()
            w, h = 342, 224
            pairs = (("title", bytes((17, 25, 34, 255))),
                     ("root", bytes((88, 101, 113, 255))))
            for n, (stage, pixel) in enumerate(pairs):
                rgba = pixel * (w * h)
                rgb = pixel[:3] * (w * h)
                (source / f"modern-native-{stage}-342x224.pam").write_bytes(
                    pam(w, h, rgba))
                (presented / f"present_{n:06d}.ppm").write_bytes(
                    b"P6\n342 224\n255\n" + rgb)
            (presented / "presents.csv").write_text(
                "present,frame,alpha,crc32,luma\n"
                "0,20,0.0,12345678,44.0\n"
                "1,100,0.0,abcdef12,96.0\n")
            result = verify_native_presented_frames(presented, source)
            self.assertEqual(result["presentations_examined"], 2)
            self.assertEqual(result["matched"]["title"]["present_frame"], 20)
            self.assertEqual(result["matched"]["root"]["present_frame"], 100)
            self.assertTrue((presented / "presented-title.ppm").exists())
            self.assertFalse((presented / "present_000000.ppm").exists())
            # One forged nonblank frame cannot claim both title and root.
            (presented / "presented-root.ppm").unlink()
            (presented / "present_000000.ppm").write_bytes(
                b"P6\n342 224\n255\n" + (pairs[0][1][:3] * (w * h)))
            (presented / "present_000001.ppm").write_bytes(
                b"P6\n342 224\n255\n" + (pairs[0][1][:3] * (w * h)))
            with self.assertRaisesRegex(ValueError, "root never reached"):
                verify_native_presented_frames(presented, source)


if __name__ == "__main__":
    unittest.main()
