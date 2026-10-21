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
    verify_native_presented_frames, verify_native_title_entry,
)


def pam(width: int, height: int, pixels: bytes) -> bytes:
    return (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
            "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode() + pixels


class ModernTitleNativeCaptureTests(unittest.TestCase):
    def test_real_p1_native_entry_order_depends_only_on_reduced_motion(self):
        opened = "UR_BALDOSA_MODERN_ROOT opened=1"
        pressed = "UR_BALDOSA_MODERN_TITLE native_p1_start=1 frame=60"
        entered = "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=60 input_owned=1"
        painted = "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared"
        ordinary = "\n".join((opened, pressed, entered, painted))
        immediate = "\n".join((opened, entered, pressed, painted))
        verify_native_title_entry(ordinary)
        verify_native_title_entry(immediate, reduced_motion=True)
        with self.assertRaisesRegex(ValueError, "missing/out-of-order"):
            verify_native_title_entry(immediate)
        with self.assertRaisesRegex(ValueError, "missing/out-of-order"):
            verify_native_title_entry(ordinary, reduced_motion=True)
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            verify_native_title_entry(ordinary + "\n" + pressed)

    def test_real_host_enter_route_is_separate_from_gamepad(self):
        opened = "UR_BALDOSA_MODERN_ROOT opened=1"
        keyboard = "UR_BALDOSA_MODERN_TITLE native_keyboard_enter=1 frame=60"
        gamepad = "UR_BALDOSA_MODERN_TITLE native_p1_start=1 frame=60"
        entered = "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=60 input_owned=1"
        painted = "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared"
        keyboard_log = "\n".join((opened, keyboard, entered, painted))
        immediate = "\n".join((opened, entered, keyboard, painted))
        verify_native_title_entry(keyboard_log, confirm="keyboard")
        verify_native_title_entry(immediate, reduced_motion=True, confirm="keyboard")
        for log in (keyboard_log, immediate):
            with self.assertRaisesRegex(ValueError, "missing/duplicate"):
                verify_native_title_entry(log, confirm="gamepad")
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            verify_native_title_entry(
                "\n".join((opened, gamepad, entered, painted)),
                confirm="keyboard")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            verify_native_title_entry(keyboard_log, confirm="other")

    def test_real_start_button_is_not_a_or_keyboard_enter(self):
        opened = "UR_BALDOSA_MODERN_ROOT opened=1"
        pressed = "UR_BALDOSA_MODERN_TITLE native_p1_start_button=1 frame=60"
        entered = "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=74 input_owned=1"
        painted = "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared"
        log = "\n".join((opened, pressed, entered, painted))
        verify_native_title_entry(log, confirm="start")
        verify_native_title_entry(
            "\n".join((opened, entered, pressed, painted)),
            reduced_motion=True, confirm="start")
        for route in ("gamepad", "keyboard"):
            with self.subTest(route=route), self.assertRaisesRegex(
                ValueError, "missing/duplicate"
            ):
                verify_native_title_entry(log, confirm=route)
        with self.assertRaisesRegex(ValueError, "missing/duplicate"):
            verify_native_title_entry(log + "\n" + pressed, confirm="start")
        with self.assertRaisesRegex(ValueError, "missing/out-of-order"):
            verify_native_title_entry(
                "\n".join((opened, entered, pressed, painted)),
                confirm="start")

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
            self.assertEqual(read_pam(path, expected_width=256)[:2], (256, 224))
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
            with self.assertRaisesRegex(ValueError, "missing/duplicate"):
                validate_native_capture(folder, "", exe_sha256="invalid")
            with self.assertRaisesRegex(ValueError, "missing/duplicate"):
                validate_native_capture(
                    folder, "UR_BALDOSA_MODERN_ROOT opened=1\n",
                    exe_sha256="invalid")

    def test_native_four_by_three_host_raster_contract(self):
        # Test the actual 256-wide original-density shape, with the retail
        # picture centred separately (not a crop of the 342-wide output).
        with tempfile.TemporaryDirectory() as root:
            where = Path(root)
            photos = where / "presented"
            source = where / "captures"
            photos.mkdir()
            source.mkdir()
            w, h = 256, 224
            for n, (stage, pixel) in enumerate((
                ("title", bytes((36, 52, 67, 255))),
                ("root", bytes((70, 90, 110, 255))),
            )):
                (source / f"modern-native-{stage}-256x224.pam").write_bytes(
                    pam(w, h, pixel * (w * h)))
                (photos / f"present_{n:06d}.ppm").write_bytes(
                    b"P6\n256 224\n255\n" + pixel[:3] * (w * h))
            (photos / "presents.csv").write_text(
                "present,frame,alpha,crc32,luma\n"
                "0,32,0.0,12345678,32.0\n"
                "1,80,0.0,abcdef12,80.0\n")
            receipt = verify_native_presented_frames(photos, source, expected_width=256)
            self.assertEqual(receipt["matched"]["title"]["source_match_fraction"], 1.0)
            self.assertEqual(receipt["matched"]["root"]["source_match_fraction"], 1.0)
            self.assertEqual(read_present_ppm(photos / "presented-root.ppm", 256)[:2],
                             (256, 224))
            with self.assertRaisesRegex(ValueError, "dimensions"):
                read_present_ppm(photos / "presented-root.ppm", 342)

    def test_reduced_motion_uses_unmoving_original_logo_in_native_presents(self):
        # Source and PPM fixtures exercise the checker, never masquerade as
        # actual SDL native acceptance or replace verified retail-art SHA.
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            source = base / "captures"
            presented = base / "presented"
            source.mkdir()
            presented.mkdir()
            width, height = 342, 224
            title_pixel = bytes((15, 80, 132, 255))
            root_pixel = bytes((83, 96, 100, 255))
            for name, pixel in (("title", title_pixel), ("root", root_pixel)):
                (source / f"modern-native-{name}-342x224.pam").write_bytes(
                    pam(width, height, pixel * (width * height)))
            def write_present(index, pixel):
                (presented / f"present_{index:06d}.ppm").write_bytes(
                    b"P6\n342 224\n255\n" + pixel[:3] * (width * height))
            write_present(0, title_pixel)
            write_present(1, root_pixel)  # forged movement before confirm
            write_present(2, root_pixel)
            (presented / "presents.csv").write_text(
                "present,frame,alpha,crc32,luma\n"
                "0,16,0,12345678,11\n"
                "1,32,0,12345678,11\n"
                "2,80,0,12345678,11\n")
            with self.assertRaisesRegex(ValueError, "reduced-motion original title moved"):
                verify_native_presented_frames(
                    presented, source, expected_width=width, reduced_motion=True)
            write_present(1, title_pixel)
            accepted = verify_native_presented_frames(
                presented, source, expected_width=width, reduced_motion=True)
            self.assertEqual(accepted["presentations_examined"], 3)
            self.assertEqual(accepted["matched"]["root"]["present_frame"], 80)

    def test_original_logo_lift_and_native_exit_sweep_are_retained(self):
        # Synthetic verifier tests are deliberately distinct from real Win32
        # source/PE evidence. Positive geometry here must never award QA.
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, photos = base / "captures", base / "presented"
            source.mkdir()
            photos.mkdir()
            w, h = 256, 224
            base_rgba = bytes((31, 43, 61, 255))
            title = bytearray(base_rgba * (w * h))
            left = (w - 238) // 2
            for y in range(27, 108):
                for x in range(left, left + 238):
                    i = (y * w + x) * 4
                    title[i:i+3] = bytes(((x + y) & 255,
                                         (x + 7*y) & 255,
                                         (3*x + y) & 255))
            root = bytes((88, 108, 128, 255)) * (w * h)
            (source / "modern-native-title-256x224.pam").write_bytes(
                pam(w, h, title))
            (source / "modern-native-root-256x224.pam").write_bytes(
                pam(w, h, root))
            def rgb(rgba):
                return b"".join(rgba[i:i + 3] for i in range(0, len(rgba), 4))
            settled = rgb(title)
            entry = bytearray(rgb(base_rgba * (w * h)))
            for y in range(81):
                for x in range(left, left + 238):
                    start = ((y + 27) * w + x) * 3
                    end = ((y + 31) * w + x) * 3
                    entry[end:end+3] = settled[start:start+3]
            leaving = bytearray(settled)
            for x in range(90):
                start = (192 * w + x) * 3
                leaving[start:start+3] = bytes((0x6c, 0xbf, 0xeb))
            def write_photo(i, content):
                (photos / f"present_{i:06d}.ppm").write_bytes(
                    b"P6\n256 224\n255\n" + content)
            (photos / "presents.csv").write_text(
                "present,frame,alpha,crc32,luma\n"
                "0,16,0,12345678,11\n"
                "1,32,0,12345678,11\n"
                "2,64,0,12345678,11\n"
                "3,80,0,12345678,11\n")
            write_photo(0, settled)  # forged static title without +4px lift
            write_photo(1, settled)
            write_photo(2, leaving)
            write_photo(3, rgb(root))
            with self.assertRaisesRegex(ValueError, "exact \\+4px"):
                verify_native_presented_frames(
                    photos, source, w, require_motion_evidence=True)
            write_photo(0, bytes(entry))
            write_photo(2, settled)  # forged static title instead of exit sweep
            with self.assertRaisesRegex(ValueError, "leaving sweep"):
                verify_native_presented_frames(
                    photos, source, w, require_motion_evidence=True)
            write_photo(2, bytes(leaving))
            accepted = verify_native_presented_frames(
                photos, source, w, require_motion_evidence=True)
            self.assertEqual(accepted["motion"]["entry"]["present_frame"], 16)
            self.assertEqual(accepted["motion"]["leaving"]["present_frame"], 64)
            self.assertEqual(accepted["motion"]["entry"]["source_logo_match_fraction"], 1.0)
            self.assertEqual(accepted["motion"]["leaving"]["source_logo_match_fraction"], 1.0)
            self.assertTrue((photos / "presented-entry.ppm").is_file())
            self.assertTrue((photos / "presented-leaving.ppm").is_file())
            self.assertFalse((photos / "present_000000.ppm").exists())

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
