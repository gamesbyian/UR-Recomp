"""Adversarial ROM-free tests for real Authentic P6 -> SDL3 pixel parity.

Only synthetic images, process logs and receipts: tests do NOT execute the
original game or grant physical/visual approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import qa_modern_visual_authentic_rgb_parity as qa


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class AuthenticRGBParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stage = self.root / "probe_first"
        self.stage.mkdir()
        self.receipt = self.root / "readback-receipt.json"
        self.w, self.h = 640, 360
        # Pattern varies in both directions, avoiding a uniform image that
        # could falsely pass wrong scaling, cropping or pitch indexing.
        self.src = bytes(c for y in range(224) for x in range(256)
                         for c in (x % 256, y % 256, (x * 5 + y * 3) % 256))
        self.p6 = qa.P6_HEADER + self.src
        (self.stage / "stock-composed-before-sdl.ppm").write_bytes(self.p6)
        self.rgba = bytearray(self.w * self.h * 4)
        vw = 480
        for y in range(self.h):
            sy = min(223, ((2 * y + 1) * 224) // (2 * self.h))
            for x in range(80, 80 + vw):
                sx = min(255, ((2 * (x - 80) + 1) * 256) // (2 * vw))
                i = (y * self.w + x) * 4
                j = (sy * 256 + sx) * 3
                self.rgba[i:i+3] = self.src[j:j+3]
                # Deliberately zero alpha to model observed SDL3 readback.
        self.write_p7()
        self.log = (
            "[snes_load] name=UNIRACERS\n"
            "UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=240 "
            "guest_frame=240 output=640x360 "
            "source=SDL_RenderReadPixels backend=sdl3\n"
        ).encode()
        (self.stage / "native-process.log").write_bytes(self.log)
        self.fields = {
            "execution_mode": "authentic",
            "native_semantic_route": "authentic-stock",
            "actual_sdl_renderer_output": [self.w, self.h],
            "p7_sha256": sha(self.p7),
            "native_process_log_sha256": sha(self.log),
            "exe_sha256": "a" * 64,
            "release_gate_credit": 0,
            "authentic_isolation_approved": False,
        }
        self.write_receipt()

    def write_p7(self):
        header = (f"P7\nWIDTH {self.w}\nHEIGHT {self.h}\nDEPTH 4\n"
                  "MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n").encode()
        self.p7 = header + self.rgba
        (self.stage / "actual-sdl-drawable.pam").write_bytes(self.p7)

    def write_receipt(self):
        self.receipt.write_text(json.dumps(self.fields))

    def sync_hash(self):
        self.fields["p7_sha256"] = sha(self.p7)
        self.write_receipt()

    def test_exact_synthetic_native_rgb_even_with_zero_alpha(self):
        report = qa.verify(self.stage, self.receipt)
        self.assertTrue(report["rgb_pixel_parity_proven"])
        self.assertEqual(report["viewport"], [80, 0, 480, 360])
        self.assertEqual(report["rgb_exact_viewport_pixels"], 480 * 360)
        self.assertEqual(report["rgb_exact_black_bar_pixels"], 160 * 360)
        self.assertEqual(report["total_exact_rgb_pixels"], 640 * 360)
        self.assertEqual(report["nonzero_alpha_pixels"], 0)
        self.assertFalse(report["authentic_isolation_approved"])
        self.assertFalse(report["human_visual_approved"])
        self.assertEqual(report["release_gate_credit"], 0)

    def test_one_corrupted_content_pixel_with_updated_sha_rejected(self):
        i = (100 * self.w + 123) * 4
        self.rgba[i] ^= 0x40
        self.write_p7()
        self.sync_hash()
        with self.assertRaisesRegex(qa.EvidenceError, "first divergence"):
            qa.verify(self.stage, self.receipt)

    def test_nonblack_pillarbox_with_updated_sha_rejected(self):
        self.rgba[0:3] = b"\x11\x22\x33"
        self.write_p7()
        self.sync_hash()
        with self.assertRaisesRegex(qa.EvidenceError, "nonblack stock pillarbox"):
            qa.verify(self.stage, self.receipt)

    def test_source_hash_mismatch_and_modern_leak_rejected(self):
        self.fields["p7_sha256"] = "0" * 64
        self.write_receipt()
        with self.assertRaisesRegex(qa.EvidenceError, "receipt hash"):
            qa.verify(self.stage, self.receipt)
        self.sync_hash()
        new_log = self.log + b"UR_BALDOSA_MODERN_ROOT opened=1\n"
        (self.stage / "native-process.log").write_bytes(new_log)
        self.fields["native_process_log_sha256"] = sha(new_log)
        self.write_receipt()
        with self.assertRaisesRegex(qa.EvidenceError, "Modern root leaked"):
            qa.verify(self.stage, self.receipt)

    def test_wrong_mode_and_wrong_guest_marker_rejected(self):
        self.fields["execution_mode"] = "modern"
        self.write_receipt()
        with self.assertRaisesRegex(qa.EvidenceError, "receipt hash"):
            qa.verify(self.stage, self.receipt)
        self.fields["execution_mode"] = "authentic"
        log = self.log.replace(b"draw=240", b"draw=241")
        (self.stage / "native-process.log").write_bytes(log)
        self.fields["native_process_log_sha256"] = sha(log)
        self.write_receipt()
        with self.assertRaisesRegex(qa.EvidenceError, "stock-load or SDL3"):
            qa.verify(self.stage, self.receipt)

    def test_p6_truncated_and_redirected_rejected(self):
        source = self.stage / "stock-composed-before-sdl.ppm"
        source.write_bytes(self.p6[:-1])
        with self.assertRaisesRegex(qa.EvidenceError, "P6 format/geometry"):
            qa.verify(self.stage, self.receipt)
        source.unlink()
        source.symlink_to(self.stage / "actual-sdl-drawable.pam")
        with self.assertRaisesRegex(qa.EvidenceError, "redirected"):
            qa.verify(self.stage, self.receipt)


if __name__ == "__main__":
    unittest.main()
