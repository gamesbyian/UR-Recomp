"""Adversarial ROM-free tests for original native Win32 title/root P7 evidence.

Synthetic RGBA here tests only the independent verifier. Actual title/root
pixels must come from a compiled original AOT PE on Windows in CI.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import qa_modern_title_final_sdl_transition as proof
from tools import qa_modern_visual_win32_capture_driver as driver

W, H = 320, 224
SOURCE = "a" * 40
EXE = "b" * 64
HEAD = b"P7\nWIDTH 320\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"


def case(root, name, changed=False, *, source=SOURCE, exe=EXE):
    stage = root / name
    (stage / "probe_first").mkdir(parents=True)
    pixels = bytearray(bytes((20, 30, 55, 0)) * (W * H))
    if changed:
        # Change 20x20 pixels in center of a genuinely-structured test P7.
        for y in range(80, 100):
            for x in range(110, 130):
                p = (y * W + x) * 4
                pixels[p:p+3] = b"\xf0\x81\x40"
    raster = HEAD + pixels
    log = (b"UR_BALDOSA_MODERN_ROOT opened=1\n"
           b"UR_BALDOSA_MODERN_TITLE painted=1 raster=256x224\n")
    if name.endswith("-entered-root"):
        log += (b"UR_BALDOSA_MODERN_TITLE entered_root=1 frame=74 input_owned=1\n"
                b"UR_BALDOSA_MODERN_ROOT painted=1\n")
    log += (b"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 "
            b"guest_frame=80 output=320x224 source=SDL_RenderReadPixels\n")
    (stage / "probe_first/actual-sdl-drawable.pam").write_bytes(raster)
    (stage / "probe_first/native-process.log").write_bytes(log)
    receipt = {
        "source_sha": source, "exe_sha256": exe,
        "native_semantic_route": name, "execution_mode": "modern",
        "native_process_exit": 0, "SDL_driver": "windows",
        "observed_in_draw": 40, "actual_sdl_renderer_output": [W, H],
        "requested_window_size": [W, H],
        "native_process_log_sha256": hashlib.sha256(log).hexdigest(),
        "p7_sha256": hashlib.sha256(raster).hexdigest(),
    }
    (stage / "readback-receipt.json").write_text(json.dumps(receipt))
    return stage


def cases(root):
    for name in proof.CASES:
        case(root, name, changed=name.endswith("-entered-root"))


class RealWin32TitleP7Test(unittest.TestCase):
    def test_expected_native_routes_without_synthetic_guest_writes(self):
        for name in proof.CASES:
            self.assertIn(name, driver.ROUTES)
            self.assertEqual(driver.ROUTES[name][0], "15")
            self.assertEqual(driver.ROUTES[name][1], 40)
        self.assertNotIn("UR_MODERN_MENU_TEST_TICK60",
                         driver.motion_phase_environment("title-still"))

    def test_independent_real_p7_manifest_and_negative_release_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases(root)
            evidence = proof.verify(root, SOURCE)
            self.assertEqual(evidence["normal"]["changed_rgb_pixels_in_center_roi"], 400)
            self.assertEqual(evidence["reduced_motion"]["changed_rgb_pixels_in_center_roi"], 400)
            self.assertEqual(evidence["normal"]["difference_bbox_xyxy"],
                             [110, 80, 129, 99])
            self.assertFalse(evidence["original_title_visual_design_approved"])
            self.assertFalse(evidence["source_P6_to_final_SDL_exact_pixel_parity_proven"])
            self.assertFalse(evidence["physical_controller_and_display_approved"])
            self.assertEqual(evidence["release_gate_credit"], 0)

    def test_fails_if_one_stage_shows_static_or_no_real_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases(root)
            original = (root / "title-still/probe_first/actual-sdl-drawable.pam").read_bytes()
            to_replace = root / "title-entered-root/probe_first/actual-sdl-drawable.pam"
            to_replace.write_bytes(original)
            receipt_file = root / "title-entered-root/readback-receipt.json"
            receipt = json.loads(receipt_file.read_text())
            receipt["p7_sha256"] = hashlib.sha256(original).hexdigest()
            receipt_file.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "absent/static"):
                proof.verify(root, SOURCE)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases(root)
            stage = root / "title-entered-root/probe_first/native-process.log"
            log = stage.read_bytes().replace(b"entered_root=1", b"entered_root=0")
            stage.write_bytes(log)
            receipt_file = root / "title-entered-root/readback-receipt.json"
            receipt = json.loads(receipt_file.read_text())
            receipt["native_process_log_sha256"] = hashlib.sha256(log).hexdigest()
            receipt_file.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "handoff absent"):
                proof.verify(root, SOURCE)

    def test_reject_mixed_pe_source_geometry_and_modified_p7(self):
        for key, new_value in [
            ("exe_sha256", "c" * 64),
            ("source_sha", "c" * 40),
            ("actual_sdl_renderer_output", [400, 224]),
            ("observed_in_draw", 41),
            ("execution_mode", "authentic"),
        ]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                cases(root)
                receipt_file = root / "title-still/readback-receipt.json"
                receipt = json.loads(receipt_file.read_text())
                receipt[key] = new_value
                receipt_file.write_text(json.dumps(receipt))
                with self.assertRaises(ValueError):
                    proof.verify(root, SOURCE)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases(root)
            stage = root / "title-still/probe_first/actual-sdl-drawable.pam"
            stage.write_bytes(stage.read_bytes()[:-8])
            with self.assertRaisesRegex(ValueError, "provenance"):
                proof.verify(root, SOURCE)

    def test_symlinked_log_and_output_are_unacceptable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases(root)
            stage = root / "title-still/probe_first/native-process.log"
            stage.unlink()
            stage.symlink_to(root / "title-still/readback-receipt.json")
            with self.assertRaisesRegex(ValueError, "symlinked"):
                proof.verify(root, SOURCE)


if __name__ == "__main__":
    unittest.main()
