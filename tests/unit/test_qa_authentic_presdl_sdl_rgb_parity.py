"""Adversarial ROM-free source-to-SDL exact Authentic RGB parity tests.

Fake images only test transport and fail-closed pixel comparison. They are
NEVER native execution, hardware display or release acceptance.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from tools import qa_authentic_presdl_sdl_rgb_parity as parity


class AuthenticPresdlSdlRGBParityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "native-source.ppm"
        self.drawable = self.root / "real-sdl-candidate.pam"
        self.source_rgb = bytes(
            channel for y in range(224) for x in range(256)
            for channel in ((x * 7 + y * 3) % 256,
                            (y * 11 + x) % 256,
                            (x ^ y) % 256)
        )
        self.source.write_bytes(b"P6\n256 224\n255\n" + self.source_rgb)

    def generate(self, width, height, *, alpha=0, source=None):
        source = source if source is not None else self.source_rgb
        if 3 * width >= 4 * height:
            vw, vh = height * 4 // 3, height
        else:
            vw, vh = width, width * 3 // 4
        left, top = (width - vw) // 2, (height - vh) // 2
        result = bytearray(width * height * 4)
        for y in range(top, top + vh):
            sy = ((2 * (y - top) + 1) * 224) // (2 * vh)
            for x in range(left, left + vw):
                sx = ((2 * (x - left) + 1) * 256) // (2 * vw)
                src = 3 * (sy * 256 + sx)
                dst = 4 * (y * width + x)
                result[dst:dst+3] = source[src:src+3]
                result[dst+3] = alpha
        hdr = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\n"
               "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
        self.drawable.write_bytes(hdr + result)
        return hdr, result

    def test_exact_full_43_rgb_with_entirely_zero_alpha(self):
        self.generate(320, 240)
        observed = parity.verify(self.source, self.drawable)
        self.assertEqual(observed["authentic_content_viewport"], [0, 0, 320, 240])
        self.assertEqual(observed["source_to_sdl_exact_rgb_pixels"], 320 * 240)
        self.assertEqual(observed["outside_black_exact_rgb_pixels"], 0)
        self.assertEqual(observed["sdl_nonzero_alpha_pixels"], 0)
        self.assertEqual(observed["source_ppm_sha256"],
                         hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertFalse(observed["physical_display_approved"])
        self.assertFalse(observed["guest_crc_oracle_approved"])
        self.assertEqual(observed["release_gate_credit"], 0)

    def test_exact_wide_pillarbox_rgb_and_alpha_diagnostic(self):
        self.generate(640, 360, alpha=255)
        observed = parity.verify(self.source, self.drawable)
        self.assertEqual(observed["authentic_content_viewport"], [80, 0, 480, 360])
        self.assertEqual(observed["source_to_sdl_exact_rgb_pixels"], 480 * 360)
        self.assertEqual(observed["outside_black_exact_rgb_pixels"], 160 * 360)
        self.assertEqual(observed["sdl_nonzero_alpha_pixels"], 480 * 360)
        self.assertFalse(observed["integrated_modern_visual_approved"])

    def test_reject_one_modified_source_content_pixel(self):
        header, raw = self.generate(320, 240)
        raw[4 * (123 * 320 + 177)] ^= 1
        self.drawable.write_bytes(header + raw)
        with self.assertRaisesRegex(parity.ParityError, "RGB divergence"):
            parity.verify(self.source, self.drawable)

    def test_reject_nonblack_pixel_in_letterbox(self):
        header, raw = self.generate(640, 360)
        raw[4 * (40 * 640 + 17)] = 7
        self.drawable.write_bytes(header + raw)
        with self.assertRaisesRegex(parity.ParityError, "nonblack RGB outside"):
            parity.verify(self.source, self.drawable)

    def test_reject_black_source_wrong_geometry_trailing_and_links(self):
        self.generate(320, 240)
        self.source.write_bytes(b"P6\n256 224\n255\n" + bytes(256 * 224 * 3))
        with self.assertRaisesRegex(parity.ParityError, "entirely black"):
            parity.verify(self.source, self.drawable)
        self.source.write_bytes(b"P6\n255 224\n255\n" + bytes(255 * 224 * 3))
        with self.assertRaisesRegex(parity.ParityError, "geometry changed"):
            parity.verify(self.source, self.drawable)
        self.source.write_bytes(b"P6\n256 224\n255\n" + self.source_rgb)
        self.drawable.write_bytes(self.drawable.read_bytes() + b"extra")
        with self.assertRaisesRegex(parity.ParityError, "trailing bytes"):
            parity.verify(self.source, self.drawable)
        self.generate(320, 240)
        linked = self.root / "linked.pam"
        linked.symlink_to(self.drawable)
        with self.assertRaisesRegex(parity.ParityError, "redirected"):
            parity.verify(self.source, linked)


if __name__ == "__main__":
    unittest.main()
