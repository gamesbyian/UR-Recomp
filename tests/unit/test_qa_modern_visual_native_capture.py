"""ROM-free adversarial QA for exact final-native SDL screenshot transport.

No test here runs a Windows game or asserts an actual source-captured image.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest

from tools import qa_modern_visual_pam_png as pam
from tools import qa_modern_visual_sdl_capture as sdl
from tools import check_modern_visual_capture_bundle as audit


class NativeSDLStageTests(unittest.TestCase):
    def host(self):
        return (
            "#include <stdio.h>\n"
            "static void SdlRenderer_EndDraw(void) {\n" +
            sdl.ANCHOR +
            "}\nstatic void SdlRenderer_Reconfigure(void) {}\n"
        )

    def test_unique_real_sdl_endpoint_and_inert_default(self):
        source = self.host()
        result = sdl.patch_host(source)
        self.assertNotEqual(result, source)
        self.assertEqual(result.count(sdl.MARK), 1)
        self.assertEqual(result.count("UrQaModernReadDrawable();"), 1)
        self.assertIn("SDL_RenderReadPixels(g_renderer", result)
        self.assertIn("SDL_RenderPresent(g_renderer)", result)
        self.assertLess(result.index("UrQaModernReadDrawable();"),
                        result.index("SDL_RenderPresent(g_renderer)"))
        self.assertIn("UR_MODERN_VISUAL_SDL_CAPTURE_DRAW", result)
        self.assertIn("UR_MODERN_VISUAL_SDL_CAPTURE_FILE", result)
        self.assertIn("UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_WIDTH", result)
        self.assertIn("UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_HEIGHT", result)
        # SDL3 returns a surface; SDL2 writes into the supplied array.
        # Both must call this same observer in the real EndDraw path.
        self.assertIn("#if SNESRECOMP_SDL3", result)
        self.assertIn("SDL_Surface *native = SDL_RenderReadPixels(g_renderer, NULL);", result)
        self.assertIn("SDL_ConvertSurface(native, SDL_PIXELFORMAT_ARGB8888)", result)
        self.assertIn("SDL_DestroySurface(argb)", result)
        self.assertIn("SDL_RenderReadPixels(g_renderer, NULL, SDL_PIXELFORMAT_ARGB8888,", result)
        self.assertNotIn("#if !SNESRECOMP_SDL3\\n  UrQaModernReadDrawable();", result)
        self.assertIn("if (!target || !*target || !output || !*output", result)
        self.assertEqual(sdl.patch_host(result), result)

    def test_source_drift_multiple_or_wrong_owner_rejected(self):
        with self.assertRaisesRegex(ValueError, "drift"):
            sdl.patch_host("static void SdlRenderer_EndDraw(void) {}")
        with self.assertRaisesRegex(ValueError, "drift"):
            sdl.patch_host(self.host() + sdl.ANCHOR)
        source = ("static void SdlRenderer_EndDraw(void) {}\n"
                  "static void SdlRenderer_Reconfigure(void) {}\n" +
                  sdl.ANCHOR)
        with self.assertRaisesRegex(ValueError, "outside"):
            sdl.patch_host(source)

    def test_disposable_stage_and_restage_without_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "runner/src/desktop/host_main.c"
            target.parent.mkdir(parents=True)
            target.write_text(self.host(), encoding="utf-8")
            self.assertTrue(sdl.stage(root))
            first = target.read_bytes()
            self.assertFalse(sdl.stage(root))
            self.assertEqual(first, target.read_bytes())
            target.unlink()
            target.symlink_to(root / "not-a-file")
            with self.assertRaisesRegex(ValueError, "missing/redirected"):
                sdl.stage(root)


class PAMToPNGTests(unittest.TestCase):
    @staticmethod
    def p7(w=3, h=2):
        head = (f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\n"
                f"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
        raw = bytes((x * 17 % 256 for x in range(w * h * 4)))
        return head + raw, raw

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "drawable.pam"
        self.png = self.root / "drawable.png"
        self.original, self.raw = self.p7()
        self.source.write_bytes(self.original)

    def test_byte_exact_rgba_roundtrip_and_nonapproval(self):
        receipt = pam.convert(self.source, self.png, (3, 2))
        data = self.png.read_bytes()
        self.assertEqual(audit.png_pixels(data), (3, 2))
        self.assertEqual(receipt["pixels"], [3, 2])
        self.assertEqual(receipt["source_p7_sha256"],
                         hashlib.sha256(self.original).hexdigest())
        self.assertEqual(receipt["converted_png_sha256"],
                         hashlib.sha256(data).hexdigest())
        self.assertFalse(receipt["actual_sdl_proven"])
        self.assertFalse(receipt["visual_approved"])
        self.assertEqual(receipt["release_gate_credit"], 0)
        # Independently concatenate the exact RGBA bytes decoded from PNG.
        pos, compressed = 8, b""
        while pos < len(data):
            length = struct.unpack_from(">I", data, pos)[0]
            tag = data[pos + 4:pos + 8]
            if tag == b"IDAT":
                compressed += data[pos + 8:pos + 8 + length]
            pos += 12 + length
        import zlib
        inflated = zlib.decompress(compressed)
        self.assertEqual(inflated, b"\x00" + self.raw[:12] +
                         b"\x00" + self.raw[12:])

    def test_reject_truncation_trailing_and_false_dimensions(self):
        for suffix in (self.original[:-1], self.original + b"X"):
            with self.subTest(length=len(suffix)):
                self.source.write_bytes(suffix)
                with self.assertRaisesRegex(pam.RasterError, "truncated or trailing"):
                    pam.convert(self.source, self.png, (3, 2))
        self.source.write_bytes(self.original)
        with self.assertRaisesRegex(pam.RasterError, "dimensions"):
            pam.convert(self.source, self.png, (2, 3))

    def test_reject_changed_pixel_type_and_nonsense_header(self):
        self.source.write_bytes(self.original.replace(b"DEPTH 4", b"DEPTH 3"))
        with self.assertRaisesRegex(pam.RasterError, "header"):
            pam.convert(self.source, self.png)
        self.source.write_bytes(b"P7\n" + self.original)
        with self.assertRaisesRegex(pam.RasterError, "header"):
            pam.convert(self.source, self.png)

    def test_reject_existing_destination_and_symlinks(self):
        self.png.write_bytes(b"prior")
        with self.assertRaisesRegex(pam.RasterError, "already exists"):
            pam.convert(self.source, self.png)
        self.png.unlink()
        alias = self.root / "link.pam"
        alias.symlink_to(self.source)
        with self.assertRaisesRegex(pam.RasterError, "redirected"):
            pam.convert(alias, self.png)

    def test_atomically_reject_existing_partial(self):
        temporary = self.root / "drawable.png.part"
        temporary.write_bytes(b"prior")
        with self.assertRaisesRegex(pam.RasterError, "temporary"):
            pam.convert(self.source, self.png)
        self.assertFalse(self.png.exists())
        self.assertEqual(temporary.read_bytes(), b"prior")

    def test_overlong_dimensions_and_missing_source_rejected(self):
        huge, _ = self.p7(3841, 2)
        self.source.write_bytes(huge)
        with self.assertRaisesRegex(pam.RasterError, "geometry"):
            pam.convert(self.source, self.png)
        self.source.unlink()
        with self.assertRaisesRegex(pam.RasterError, "missing"):
            pam.convert(self.source, self.png)


if __name__ == "__main__":
    unittest.main()
