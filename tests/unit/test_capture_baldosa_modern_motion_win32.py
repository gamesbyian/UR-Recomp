#!/usr/bin/env python3
"""Prove bounded real-PE runner contracts without fabricating native evidence.

Mocks only subprocess for the pure Python acceptance wrapper. The source
motion receipt is independently verified; stub process rows are synthetic
and NEVER used as evidence that any Windows PE was actually executed.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import capture_baldosa_modern_motion_win32 as capture
import verify_modern_menu_motion_capture as proof


def simulated_original_menu_receipts(
        count: int = 48, scripted_navigation: bool = False) -> str:
    source = json.loads(proof.SOURCE.read_text(encoding="utf-8"))
    steps = source["transition_main_to_options"]["enter_velocity_px_per_frame"]
    lines = ["UR_BALDOSA_MODERN_ROOT opened=1"]
    selected, origin_y, selection_tick = 0, 0, 0
    for i in range(count):
        if scripted_navigation and i in (60, 61, 62):
            chosen = i - 59
            old_y = selected * 21
            elapsed = min(12, i - selection_tick)
            if origin_y != old_y and elapsed < 12:
                elapsed += 1
            old_display_y = old_y + proof.measured_cursor_offset(
                origin_y - old_y, elapsed,
                source["cursor"]["move_y_per_frame"])
            origin_y = old_display_y
            selected = chosen
            selection_tick = i
            lines.append(f"UR_BALDOSA_MODERN_ROOT selected={chosen}")
        age = min(12, i - selection_tick)
        if origin_y != selected * 21 and age < 12:
            age += 1
        offset = proof.measured_cursor_offset(
            origin_y - selected * 21, age,
            source["cursor"]["move_y_per_frame"])
        stamp = dict(ordinal=i, tick60=i, selection=selected,
                     spin=(i // 2) % 16, offset=offset,
                     entrance=256 - sum(steps[:min(i, 39)]), reduced=0,
                     root_x=8, root_w=240, surface_w=256,
                     surface_h=224, painted=1)
        lines.append(proof.PREFIX + " ".join(
            f"{key}={stamp[key]}" for key in proof.FIELDS))
    return "\n".join(lines) + "\n"


class WindowsModernMenuMotionNativeReceiptTests(unittest.TestCase):
    def test_exact_capture_environment_and_native_source_wait_window(self):
        env = capture.EXPECTED_CAPTURE_ENV
        self.assertEqual(env["UR_BALDOSA_MODERN_ROOT"], "1")
        self.assertEqual(env["UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"], "0")
        self.assertEqual(env["UR_MODERN_MENU_TEST_TICK60"], "0")
        self.assertEqual(env["UR_MODERN_MENU_TEST_ADVANCE_PER_PRESENT"], "1")
        self.assertEqual(env["UR_REDUCED_MOTION"], "0")
        self.assertEqual(env["SDL_VIDEODRIVER"], "dummy")
        self.assertLess(capture.FRAMES, 943)  # avoid a source attract cycle
        self.assertGreater(capture.FRAMES, 500)  # ample real native draws

    def test_process_contract_and_source_native_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe, rom, out = root / "game.exe", root / "game.sfc", root / "capture"
            exe.write_bytes(b"executable-byte-placeholder")
            rom.write_bytes(b"rom-byte-placeholder")
            seen = []
            def fake_run(command, *, cwd, env, timeout, text, capture_output, errors):
                seen.append(dict(command=command, cwd=cwd, env=env.copy(),
                                 timeout=timeout, text=text, errors=errors))
                return SimpleNamespace(returncode=0,
                                       stdout=simulated_original_menu_receipts(),
                                       stderr="")
            with patch.object(capture, "validate_paths",
                              return_value=("a" * 64, capture.USA_SHA256)):
                with patch.object(capture.subprocess, "run", side_effect=fake_run):
                    receipt = capture.run_native(exe, rom, out, timeout=60)
            self.assertEqual(receipt["native_draw_count"], 48)
            self.assertTrue(receipt["real_windows_game_process"])
            self.assertTrue(receipt["native_root_opened_after_config"])
            self.assertFalse(receipt["source_guest_d7_admission_proven"])
            self.assertIn("SDL P7 final drawable", receipt["not_proven"])
            self.assertTrue(receipt["test_clock_per_native_root_draw"])
            self.assertEqual(receipt["exe_sha256"], "a" * 64)
            self.assertEqual(seen[0]["timeout"], 60)
            self.assertEqual(seen[0]["env"]["SDL_VIDEODRIVER"], "dummy")
            self.assertEqual(seen[0]["env"]["UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"], "0")
            self.assertEqual(seen[0]["command"][0], str(exe.resolve()))
            self.assertEqual((out / "source-idle-root.script").read_text(),
                             f"wait {capture.FRAMES}\nquit\n")
            self.assertIn("UR_MODERN_MENU_MOTION_CAPTURE",
                          (out / "native-game.log").read_text())
            self.assertEqual(
                json.loads((out / "motion-native-draw-receipt.json").read_text())
                    ["native_draw_count"], 48)

    def test_existing_native_keyboard_navigation_paints_three_real_focus_rows(self):
        # All rows here are SYNTHETIC unit data, not actual Win32 proof.
        # The real bridge runs this same mode inside the actual Windows PE.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe, rom, out = root/"game.exe", root/"game.sfc", root/"navigation"
            exe.write_bytes(b"not-real-game")
            rom.write_bytes(b"not-real-rom")
            seen = []
            def fake_run(command, *, cwd, env, timeout, text, capture_output, errors):
                seen.append(env.copy())
                return SimpleNamespace(returncode=0,
                    stdout=simulated_original_menu_receipts(
                        count=120, scripted_navigation=True), stderr="")
            with patch.object(capture, "validate_paths",
                              return_value=("b" * 64, capture.USA_SHA256)):
                with patch.object(capture.subprocess, "run", side_effect=fake_run):
                    receipt = capture.run_native(
                        exe, rom, out, timeout=60, scripted_navigation=True)
            self.assertEqual(receipt["native_draw_count"], 120)
            self.assertTrue(receipt["scripted_navigation"])
            self.assertEqual(receipt["scripted_keyboard_edges"], 3)
            self.assertFalse(receipt["physical_controller_tested"])
            self.assertEqual(seen[0]["UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"], "1")
            self.assertEqual(seen[0][
                "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE_LAST_FRAME"], "62")
            records = proof.parse_log((out / "native-game.log").read_text())
            self.assertEqual(records[-1]["selection"], 3)
            self.assertTrue(any(event["offset"] < 0 for event in records))
            self.assertEqual(receipt["session_count"], 1)
            self.assertEqual(receipt["sessions"][0]["root_width"], 240)
            self.assertIn("physical controller navigation", receipt["not_proven"])

    def test_missing_source_root_and_partial_motion_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe, rom = root / "game.exe", root / "game.sfc"
            exe.write_bytes(b"placeholder")
            rom.write_bytes(b"placeholder")
            for name, log, error in [
                ("no_open", simulated_original_menu_receipts().replace(
                    "UR_BALDOSA_MODERN_ROOT opened=1",
                    "UR_BALDOSA_MODERN_ROOT opened=0"), "did not open"),
                ("too_short", simulated_original_menu_receipts(7),
                 "no complete"),
                ("wrong_clock", simulated_original_menu_receipts().replace(
                    "tick60=2", "tick60=6", 1), "one-tick"),
                ("selector", simulated_original_menu_receipts() +
                 "UR_BALDOSA_MODERN_ROOT selected=1\n", "unexpectedly injected"),
            ]:
                with self.subTest(case=name):
                    out = root / name
                    def stub(*a, **kw):
                        return SimpleNamespace(returncode=0, stdout=log, stderr="")
                    with patch.object(capture, "validate_paths",
                                      return_value=("a" * 64, capture.USA_SHA256)):
                        with patch.object(capture.subprocess, "run", side_effect=stub):
                            with self.assertRaisesRegex(ValueError, error):
                                capture.run_native(exe, rom, out)

    def test_explicit_limits_and_real_windows_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "timeout"):
                capture.run_native(root/"not.exe", root/"not.sfc",
                                   root/"out", timeout=151)
            if sys.platform != "win32":
                with self.assertRaisesRegex(ValueError, "requires Windows"):
                    capture.validate_paths(root/"not.exe", root/"not.sfc",
                                           root/"out")


if __name__ == "__main__":
    unittest.main()
