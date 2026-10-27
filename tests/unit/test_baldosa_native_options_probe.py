#!/usr/bin/env python3
"""The native Options probe parses real root log lines strictly."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_native_options_probe as probe

LOG = (
    "UR_BALDOSA_MODERN_ROOT options_boot row=DISPLAY display=WINDOWED "
    "vsync=ON volume=100 status=NONE help=0 load=missing\n"
    "UR_BALDOSA_MODERN_ROOT options_adjusted row=VOLUME display=WINDOWED "
    "vsync=ON volume=90 status=DEFAULTS RESTORED help=0 load=loaded\n"
    "UR_BALDOSA_MODERN_ROOT options_gamepad frame=60 button=12\n")


class OptionsProbeTests(unittest.TestCase):
    def test_events_and_requirements(self):
        self.assertEqual(len(probe.events(LOG)), 2)
        probe.require(LOG, "options_boot", load="missing", volume="100")
        probe.require(LOG, "options_adjusted", status="DEFAULTS RESTORED")
        with self.assertRaises(ValueError):
            probe.require(LOG, "options_adjusted", volume="80")
        with self.assertRaises(ValueError):
            probe.require("", "options_boot")
        self.assertEqual(probe.gamepad_count(LOG), 1)

    def test_claims_no_hardware_or_release_credit(self):
        text = Path(probe.__file__).read_text()
        self.assertIn('"physical_gamepad_certified": False', text)
        self.assertIn('"release_gate_credit": 0', text)


    def test_native_root_keeps_non_acp_user_paths_for_options_and_practice(self):
        # Source seam only: actual Win32 quarantine and cold-reopen still need
        # execution against the combined Options fix on an integrated PE.
        root = (Path(__file__).resolve().parents[2] /
                "tools/baldosa_native_modern_root.cpp").read_text(
                    encoding="utf-8")
        self.assertIn('_wgetenv(L"SNESRECOMP_USER_DATA_DIR")', root)
        self.assertIn("const fs::path user_root = modern_user_data_root();", root)
        self.assertIn("const auto user_root = modern_user_data_root();", root)
        self.assertIn("baldosa_options_path(user_root).u8string()", root)
        self.assertNotIn("baldosa_options_path(user_root).string()", root)
        self.assertNotIn('const fs::path user_root(configured_root)', root)


    def test_non_acp_options_root_and_byte_exact_cold_reopen(self):
        with tempfile.TemporaryDirectory() as td:
            root = probe.options_probe_user_root(Path(td))
            self.assertTrue(any(ord(ch) > 255 for ch in root.name))
            root.mkdir()
            options = root / "options-v1.txt"
            saved = b"UR-HOST-STATE/6\ndisplay_mode=borderless\nvsync=on\n"
            damaged = b"UR-HOST-STATE/6\ninvalid options\n"
            options.write_bytes(saved)
            quarantine = Path(str(options) + ".damaged")
            quarantine.write_bytes(damaged)
            log = ("UR_BALDOSA_MODERN_ROOT options_boot row=DISPLAY "
                   "display=BORDERLESS vsync=ON volume=100 "
                   "status=NONE help=0 load=loaded\n")
            probe.verify_post_quarantine_cold_reopen(
                log, options, saved, damaged)
            options.write_bytes(saved + b"changed")
            with self.assertRaisesRegex(ValueError, "fresh saved bytes"):
                probe.verify_post_quarantine_cold_reopen(
                    log, options, saved, damaged)
            options.write_bytes(saved)
            quarantine.write_bytes(damaged + b"changed")
            with self.assertRaisesRegex(ValueError, "quarantined bytes"):
                probe.verify_post_quarantine_cold_reopen(
                    log, options, saved, damaged)
            quarantine.unlink()
            with self.assertRaisesRegex(ValueError, "quarantined bytes"):
                probe.verify_post_quarantine_cold_reopen(
                    log, options, saved, damaged)
            with self.assertRaisesRegex(ValueError, "Missing native Options"):
                probe.verify_post_quarantine_cold_reopen(
                    log.replace("load=loaded", "load=missing"),
                    options, saved, damaged)


if __name__ == "__main__":
    unittest.main()
