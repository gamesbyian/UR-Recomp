"""Final-SDL motion proof adversarial fixtures, never substitute for actual Windows PE."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import qa_modern_motion_final_sdl_pair as proof
from tools import qa_modern_visual_win32_capture_driver as driver

W, H = 320, 224
SOURCE = "a" * 40
EXE = "b" * 64
LOG = (b"UR_BALDOSA_MODERN_ROOT opened=1\n"
       b"UR_BALDOSA_MODERN_ROOT painted=1 destinations=5\n"
       b"UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 "
       b"guest_frame=40 output=320x224 source=SDL_RenderReadPixels\n")
HEADER = b"P7\nWIDTH 320\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"


def synthetic_case(root: Path, name: str, changed=False, *,
                   source=SOURCE, exe=EXE):
    stage = root / name
    (stage / "probe_first").mkdir(parents=True)
    pixels = bytearray(bytes((50, 30, 25, 0)) * (W * H))
    if changed:
        pos = (67 * W + 13) * 4
        pixels[pos] = 151
    p7 = HEADER + bytes(pixels)
    (stage / "probe_first" / "actual-sdl-drawable.pam").write_bytes(p7)
    (stage / "probe_first" / "native-process.log").write_bytes(LOG)
    receipt = {
        "native_semantic_route": name,
        "source_sha": source,
        "execution_mode": "modern",
        "native_process_exit": 0,
        "SDL_driver": "windows",
        "observed_in_draw": 40,
        "native_process_log_sha256": hashlib.sha256(LOG).hexdigest(),
        "p7_sha256": hashlib.sha256(p7).hexdigest(),
        "exe_sha256": exe,
        "actual_sdl_renderer_output": [W, H],
        "requested_window_size": [W, H],
    }
    (stage / "readback-receipt.json").write_text(json.dumps(receipt) + "\n")
    return stage


def all_cases(root: Path):
    for name in proof.CASES:
        synthetic_case(root, name, changed=(name == "root-motion-normal-eight"))


class FinalSDLNativeMenuMotionTests(unittest.TestCase):
    def test_known_good_technical_proof_and_refusal_to_certify_art(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            all_cases(root)
            result = proof.verify_four_real_native_motion_cases(root, SOURCE)
            self.assertEqual(result["normal_0_to_8_tick_rgb"]["changed_rgb_pixels"], 1)
            self.assertEqual(result["normal_0_to_8_tick_rgb"]["changed_bbox_xyxy"],
                             [13, 67, 13, 67])
            self.assertEqual(result["reduced_0_to_8_tick_rgb"]["changed_rgb_pixels"], 0)
            self.assertFalse(result["character_likeness_approved"])
            self.assertFalse(result["physical_hardware_approved"])
            self.assertFalse(result["native_60hz_wall_clock_cadence_certified"])
            self.assertEqual(result["release_gate_credit"], 0)

    def test_reject_static_normal_and_motion_in_reduced(self):
        for name in ("root-motion-normal-eight", "root-motion-reduced-eight"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                all_cases(root)
                stage = root / name
                from_name = ("root-motion-normal-zero" if "normal" in name
                             else "root-motion-normal-eight")
                # Replace the P7 and self-consistent SHA receipt to emulate
                # either a source that failed to animate or reduced-motion leak.
                original = (root / from_name / "probe_first" /
                            "actual-sdl-drawable.pam").read_bytes()
                (stage / "probe_first" / "actual-sdl-drawable.pam").write_bytes(original)
                receipt_file = stage / "readback-receipt.json"
                receipt = json.loads(receipt_file.read_text())
                receipt["p7_sha256"] = hashlib.sha256(original).hexdigest()
                receipt_file.write_text(json.dumps(receipt))
                with self.assertRaisesRegex(
                    ValueError, "no menu motion pixels|still moves"):
                    proof.verify_four_real_native_motion_cases(root, SOURCE)

    def test_reject_mixed_exe_source_and_bad_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            all_cases(root)
            stage = root / proof.CASES[0]
            receipt_file = stage / "readback-receipt.json"
            original = json.loads(receipt_file.read_text())
            for key, value in [
                ("exe_sha256", "c" * 64),
                ("source_sha", "c" * 40),
                ("requested_window_size", [640, 480]),
                ("observed_in_draw", 41),
                ("execution_mode", "authentic"),
            ]:
                receipt = {**original, key: value}
                receipt_file.write_text(json.dumps(receipt))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    proof.verify_four_real_native_motion_cases(root, SOURCE)
            receipt_file.write_text(json.dumps(original))

    def test_reject_mutated_pixels_or_logs_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            all_cases(root)
            stage = root / proof.CASES[0]
            p7 = stage / "probe_first" / "actual-sdl-drawable.pam"
            raw = p7.read_bytes()
            p7.write_bytes(raw[:-4])
            with self.assertRaisesRegex(ValueError, "provenance"):
                proof.verify_four_real_native_motion_cases(root, SOURCE)
            p7.write_bytes(raw)
            log = stage / "probe_first" / "native-process.log"
            valid = log.read_bytes()
            log.write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError, "provenance"):
                proof.verify_four_real_native_motion_cases(root, SOURCE)
            log.write_bytes(valid)
            log.unlink()
            log.symlink_to(stage / "readback-receipt.json")
            with self.assertRaisesRegex(ValueError, "symlinked"):
                proof.verify_four_real_native_motion_cases(root, SOURCE)

    def test_native_driver_routes_are_pinned_to_same_real_capture_draw(self):
        for name in proof.CASES:
            self.assertIn(name, driver.ROUTES)
            self.assertEqual(driver.ROUTES[name], ("14", 40, ""))
        self.assertEqual(driver.ROUTES["root-quit"], ("14", 40, ""))


if __name__ == "__main__":
    unittest.main()
