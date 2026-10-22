"""ROM-free negative and positive coverage for real SDL root pixel admission."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_menu_visual_language as atlas
import verify_modern_root_sdl_contrast as audit


def source_files(base: Path, wide: bool, ink: int = 200,
                 uhd: bool = False, native_480p: bool = False):
    if uhd and (not wide or native_480p):
        raise ValueError("4K source preview is 342-wide and not 480p")
    if native_480p and not wide:
        raise ValueError("native 856x480 source is 342-wide")
    source_w, w, h, root_x, root_width = (
        (342, 3840, 2160, 11, 320) if uhd else
        (342, 856, 480, 11, 320) if native_480p else
        (342, 1280, 720, 11, 320) if wide
        else (256, 1024, 768, 8, 240))
    surface = bytearray(w * h * 4)
    left = round((root_x + 8) * w / source_w)
    right = round((root_x + root_width - 8) * w / source_w)
    top = round(46 * h / 224)
    bottom = round(54 * h / 224)
    # Exact real native alpha semantics: checker A=0xE0, host font A=FF.
    for y in range(top, bottom):
        for x in range(left, right):
            k = (y * w + x) * 4
            grey = 80 if x // 32 % 2 else 47
            surface[k:k+4] = bytes([grey, grey, grey, 224])
    for y in range(top + 2, bottom - 2):
        for x in range(left + 25, left + 160):
            k = (y * w + x) * 4
            surface[k:k+4] = bytes([ink, ink, ink, 255])
    rgba = bytes(surface)
    p7 = base / "actual-sdl-drawable.pam"
    png = base / "actual-sdl-drawable.png"
    log = base / "native-process.log"
    header = (f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\n"
              f"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
    p7.write_bytes(header + rgba)
    atlas.write_png(png, w, h, rgba)
    root = f"{root_x},10,{root_width},204"
    log.write_text(
        f"UR_BALDOSA_MODERN_DESTINATION stage=root raster={source_w}x224 "
        f"root={root} source=modern_product_view\n"
        "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared\n"
        f"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 "
        f"guest_frame=40 output={w}x{h} "
        "source=SDL_RenderReadPixels backend=sdl3\n")
    receipt = {
        "schema_version": 1,
        "execution_mode": "modern",
        "SDL_driver": "windows",
        "native_process_exit": 0,
        "actual_sdl_renderer_output": [w, h],
        "visual_approved": False,
        "release_gate_credit": 0,
        "exe_sha256": "b"*64,
        "source_sha": "a"*40,
        "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
        "p7_sha256": hashlib.sha256(p7.read_bytes()).hexdigest(),
        "native_process_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
    }
    return receipt, png, p7, log


class NativeRootSdlContrastTests(unittest.TestCase):
    def test_source_bound_4_3_and_16_9_ada_text(self):
        for wide in (False, True):
            with self.subTest(wide=wide), tempfile.TemporaryDirectory() as td:
                receipt, png, p7, log = source_files(Path(td), wide)
                observed = audit.verify_capture(receipt, png, p7, log)
                self.assertTrue(observed["source_root_contrast_verified"])
                self.assertGreaterEqual(observed["minimum_contrast_ratio"], 4.5)
                self.assertEqual(observed["identity_rgb"], [[200, 200, 200]])
                self.assertEqual(observed["worst_checker_rgb"], [80, 80, 80])
                self.assertFalse(observed["visual_approved"])
                self.assertFalse(observed["hardware_approved"])
                self.assertEqual(observed["release_gate_credit"], 0)

    def test_actual_856x480_widescreen_source_geometry_and_contrast(self):
        # Newly observed in the exact successful source/PE-bound Windows
        # root snapshot from native Actions run 39555629743, artifact
        # 12325402655. Only its size and source palette are reconstructed
        # here; this synthetic fixture is not that original image.
        with tempfile.TemporaryDirectory() as td:
            receipt, png, p7, log = source_files(
                Path(td), True, native_480p=True)
            result = audit.verify_capture(receipt, png, p7, log)
            self.assertEqual(result["native_output"], [856, 480])
            self.assertEqual(result["native_source"], [342, 224])
            self.assertEqual(result["identity_rgb"], [[200, 200, 200]])
            self.assertGreaterEqual(result["minimum_contrast_ratio"], 4.5)
            self.assertFalse(result["visual_approved"])
            self.assertFalse(result["hardware_approved"])
            self.assertEqual(result["release_gate_credit"], 0)
            # A 256x224 root cannot masquerade as this actual wide host
            # merely by changing the successful native process marker.
            log.write_text(log.read_text().replace(
                "raster=342x224 root=11,10,320,204",
                "raster=256x224 root=8,10,240,204"))
            receipt["native_process_log_sha256"] = hashlib.sha256(
                log.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,"not recognized"):
                audit.verify_capture(receipt, png, p7, log)

    def test_4k_is_prospective_real_native_geometry_not_auto_approved(self):
        # 4K source-side pixel admission is distinct from physical display
        # or original artwork QA. A 342-wide host must be independently
        # present in the real process log; a 256-wide source cannot pass
        # simply by renaming its output to 3840x2160.
        with tempfile.TemporaryDirectory() as td:
            receipt, png, p7, log = source_files(Path(td), True, uhd=True)
            observed = audit.verify_capture(receipt, png, p7, log)
            self.assertEqual(observed["native_output"], [3840, 2160])
            self.assertEqual(observed["native_source"], [342, 224])
            self.assertFalse(observed["hardware_approved"])
            with self.assertRaisesRegex(ValueError, "not recognized"):
                bad = log.read_text().replace("raster=342x224", "raster=256x224")
                log.write_text(bad)
                receipt["native_process_log_sha256"] = hashlib.sha256(
                    log.read_bytes()).hexdigest()
                audit.verify_capture(receipt, png, p7, log)

    def test_real_old_screenshot_grey_fails_even_with_consistent_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            receipt, png, p7, log = source_files(Path(td), True, ink=152)
            with self.assertRaisesRegex(ValueError, "below 4.5:1"):
                audit.verify_capture(receipt, png, p7, log)

    def test_png_swap_and_source_bytes_are_checked(self):
        with tempfile.TemporaryDirectory() as td:
            receipt, png, p7, log = source_files(Path(td), False)
            original = bytearray(p7.read_bytes())
            original[-1] ^= 0x01
            p7.write_bytes(original)
            receipt["p7_sha256"] = hashlib.sha256(p7.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "PNG pixels differ"):
                audit.verify_capture(receipt, png, p7, log)
            receipt["p7_sha256"] = "0"*64
            with self.assertRaisesRegex(ValueError, "p7_sha256"):
                audit.verify_capture(receipt, png, p7, log)

    def test_mock_missing_geometry_or_actual_readback_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            receipt, png, p7, log = source_files(Path(td), True)
            for wrong_log, reason in (
                ("UR_BALDOSA_MODERN_ROOT painted=1\n", "missing actual"),
                ("UR_BALDOSA_MODERN_DESTINATION stage=root "
                 "raster=342x224 root=8,10,240,204\n"
                 "UR_BALDOSA_MODERN_ROOT painted=1\n"
                 "UR_MODERN_VISUAL_SDL_CAPTURE status=saved output=1280x720 "
                 "source=SDL_RenderReadPixels\n", "geometry"),
            ):
                log.write_text(wrong_log)
                receipt["native_process_log_sha256"] = hashlib.sha256(
                    log.read_bytes()).hexdigest()
                with self.assertRaisesRegex(ValueError, reason):
                    audit.verify_capture(receipt, png, p7, log)

    def test_p7_rejects_extra_data_even_if_hash_updated(self):
        with tempfile.TemporaryDirectory() as td:
            receipt, png, p7, log = source_files(Path(td), False)
            with p7.open("ab") as output:
                output.write(b"forged extra pixel")
            receipt["p7_sha256"] = hashlib.sha256(p7.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "truncated or trailing"):
                audit.verify_capture(receipt, png, p7, log)

    def test_native_log_capture_tokens_reject_prefix_and_duplicate_spoofs(self):
        # Historical H28 negative: substring search accepted a modified
        # status, output or source and falsely treated it as a real capture.
        # Regress the already-integrated strict parser, not its denied patch.
        real = ("UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 "
                "guest_frame=40 output=1280x720 "
                "source=SDL_RenderReadPixels backend=sdl3")
        self.assertTrue(audit.native_capture_matches(real, 1280, 720))
        for altered in (
            real.replace("status=saved", "status=savedFake"),
            real.replace("output=1280x720", "output=1280x7200"),
            real.replace("source=SDL_RenderReadPixels",
                         "source=SDL_RenderReadPixelsFake"),
            real.replace("status=saved", "xstatus=saved"),
            real + " status=saved",
            real + " output=1280x720",
            real + " source=SDL_RenderReadPixels",
            "prefix_" + real,
            "debug: " + real,
            real + " trailing-comment-without-equals",
        ):
            with self.subTest(altered=altered):
                self.assertFalse(audit.native_capture_matches(altered, 1280, 720))
        # Whitespace separation is deliberately allowed: field order is
        # irrelevant but the name and full value must remain exact.
        self.assertTrue(audit.native_capture_matches(
            "UR_MODERN_VISUAL_SDL_CAPTURE output=1280x720 "
            "source=SDL_RenderReadPixels status=saved", 1280, 720))
        self.assertFalse(audit.native_capture_matches(real, 1024, 768))

    def test_actual_capture_requires_unapproved_scope(self):
        with tempfile.TemporaryDirectory() as td:
            receipt, png, p7, log = source_files(Path(td), False)
            receipt["visual_approved"] = True
            with self.assertRaisesRegex(ValueError, "pre-approved"):
                audit.verify_capture(receipt, png, p7, log)


if __name__ == "__main__":
    unittest.main()
