#!/usr/bin/env python3
"""The native Options probe parses real root log lines strictly."""
from __future__ import annotations

import sys
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


if __name__ == "__main__":
    unittest.main()
