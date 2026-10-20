"""ROM-free tests for the one-source native Windows SDL screenshot driver.

The faked subprocess is ONLY a test of transport/refusal behavior; it cannot
earn capture, controller, hardware or visual approval.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import qa_modern_visual_win32_capture_driver as driver
from tools import check_modern_visual_capture_bundle as checker


class NativeWindowsCaptureDriverTest(unittest.TestCase):
    def test_actual_readback_log_parser_bounds(self):
        saved = ("UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=40 "
                 "guest_frame=40 output=1024x768 source=SDL_RenderReadPixels")
        mismatch = ("UR_MODERN_VISUAL_SDL_CAPTURE refused=output-size "
                    "draw=40 observed=1024x768 requested=1280x720")
        self.assertEqual(driver.READBACK.findall(saved), [("1024", "768")])
        self.assertEqual(driver.READBACK.findall(mismatch), [("1024", "768")])
        self.assertEqual(driver.READBACK.findall("mock status=good"), [])

    def test_reprobes_actual_size_then_preserves_unapproved_exact_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            exe, rom, out = base / "native.exe", base / "rom.sfc", base / "capture"
            exe.write_bytes(b"fake executable for unit only")
            rom.write_bytes(b"FAKE ROM MUST NOT BE ARCHIVED")
            calls = []

            def fake_win32_process(command, **kw):
                env = kw["env"]
                calls.append((command, env))
                self.assertEqual(env["UR_EXECUTION_MODE"], "modern")
                self.assertEqual(env["UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"], "14")
                self.assertEqual(env["SDL_VIDEODRIVER"], "windows")
                self.assertEqual(env["SDL_AUDIODRIVER"], "dummy")
                requested = (
                    int(env["UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_WIDTH"]),
                    int(env["UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_HEIGHT"]))
                size = (800, 600)
                if requested == size:
                    head = (b"P7\nWIDTH 800\nHEIGHT 600\nDEPTH 4\n"
                            b"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
                    rgba = b"\x15\x48\x83\xff" * (800 * 600)
                    Path(env["UR_MODERN_VISUAL_SDL_CAPTURE_FILE"]).write_bytes(
                        head + rgba)
                    event = ("UR_MODERN_VISUAL_SDL_CAPTURE status=saved "
                             "draw=40 guest_frame=40 output=800x600 "
                             "source=SDL_RenderReadPixels\n")
                else:
                    event = ("UR_MODERN_VISUAL_SDL_CAPTURE refused=output-size "
                             "draw=40 observed=800x600 requested=1280x720\n")
                return subprocess.CompletedProcess(
                    command, 0,
                    stdout="UR_BALDOSA_MODERN_ROOT opened=1\n" + event,
                    stderr="")

            def controlled_hash(path):
                if path == rom:
                    return driver.USA_SHA256
                with path.open("rb") as src:
                    return hashlib.sha256(src.read()).hexdigest()

            with (patch.object(driver.subprocess, "run",
                               side_effect=fake_win32_process),
                  patch.object(driver, "sha256", side_effect=controlled_hash)):
                receipt = driver.run(exe, rom, out, "a" * 40,
                                     "windows", 30)
            self.assertEqual(len(calls), 2)
            self.assertEqual(receipt["actual_sdl_renderer_output"], [800, 600])
            self.assertEqual(receipt["native_process_exit"], 0)
            self.assertFalse(receipt["source_bound_by_independent_rebuild"])
            self.assertFalse(receipt["visual_approved"])
            self.assertFalse(receipt["hardware_approved"])
            self.assertFalse(receipt["authentic_isolation_approved"])
            self.assertEqual(receipt["release_gate_credit"], 0)
            self.assertEqual(
                checker.png_pixels((out / "actual-sdl-drawable.png").read_bytes()),
                (800, 600))
            self.assertNotIn("FAKE ROM", (out / "readback-receipt.json").read_text())
            self.assertFalse((out / "Uniracers_USA.sfc").exists())
            self.assertTrue((out / "capture_observed" / "native-process.log").is_file())

    def test_exact_native_output_config_written_without_default_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            seen = []

            def fake_native(command, **kw):
                stage = Path(kw["cwd"])
                cfg = (stage / "config.ini").read_text()
                self.assertIn("[Graphics]\nWindowSize = 1280x720\n", cfg)
                self.assertIn("[Sound]\nEnableAudio = 0\n", cfg)
                seen.append(cfg)
                return subprocess.CompletedProcess(
                    command, 0,
                    stdout=("UR_BALDOSA_MODERN_ROOT opened=1\n"
                            "UR_MODERN_VISUAL_SDL_CAPTURE refused=output-size "
                            "draw=40 observed=640x480 requested=1280x720\n"),
                    stderr="")

            def fake_sha(path):
                return driver.USA_SHA256 if path == rom else "a" * 64

            rom = base / "fake-copyrighted-ROM"
            exe = base / "fake-executable"
            rom.write_bytes(b"fake rom for test only")
            exe.write_bytes(b"fake exe for test only")
            with (patch.object(driver.subprocess, "run", side_effect=fake_native),
                  patch.object(driver, "sha256", side_effect=fake_sha)):
                with self.assertRaisesRegex(RuntimeError, "Exact requested SDL drawable"):
                    driver.run(exe, rom, base / "out", "a" * 40,
                               "windows", 10, window_size=(1280, 720))
            self.assertEqual(len(seen), 1)
            self.assertTrue((base / "out" / "probe_first" /
                             "native-process.log").is_file())
            self.assertFalse((base / "out" / "capture_observed").exists())

    def test_explicit_output_geometry_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            exe, rom = base / "exe", base / "rom"
            exe.write_bytes(b"fixture")
            rom.write_bytes(b"fixture")
            with patch.object(driver, "sha256", side_effect=lambda p:
                              driver.USA_SHA256 if p == rom else "a" * 64):
                for size in [(320, 0), (3841, 2160), (640, 2161)]:
                    with self.subTest(size=size), self.assertRaisesRegex(
                            ValueError, "Unsafe exact native Win32 output"):
                        driver.run(exe, rom, base / "output", "a" * 40,
                                   "windows", 10, window_size=size)

    def test_missing_real_native_root_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            def no_root(command, **kw):
                return subprocess.CompletedProcess(
                    command, 0, stdout=(
                        "UR_MODERN_VISUAL_SDL_CAPTURE refused=output-size "
                        "draw=40 observed=800x600 requested=1280x720"),
                    stderr="")
            with patch.object(driver.subprocess, "run", side_effect=no_root):
                with self.assertRaisesRegex(RuntimeError, "Modern root not observed"):
                    driver.launch(stage / "does-not-exist.exe",
                                  stage / "does-not-exist.sfc", stage,
                                  "nativetest", (1280, 720), "windows", 2)


if __name__ == "__main__":
    unittest.main()
