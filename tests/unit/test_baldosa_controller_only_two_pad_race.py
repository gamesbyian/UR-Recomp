#!/usr/bin/env python3
"""Adversarial native two-SDL-pad source GO and earned 2P result admission.

All fixtures are synthetic verifier controls, not a substitute for the
actual Windows AOT executable and its retained source-scored guest log.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from run_baldosa_keyboard_pad_join_acceptance import (
    verify_controller_only_two_pad_race,
)
from tests.unit.test_baldosa_controller_only_two_pad_root import HOST, STAGES


SOURCE = [
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike source=real_guest",
    *STAGES,
    "UR_BALDOSA_MODERN_TWO_PAD_RACE source_stock_setup=1 menu=3d phase=f60c",
    "UR_BALDOSA_MODERN_TWO_PAD_RACE source_start_pulses=5 seats=1,2",
    "UR_BALDOSA_MODERN_TWO_PAD_RACE source_go=1 phase=8610 ticker=1",
    "UR_BALDOSA_MODERN_TWO_PAD_RACE source_input_completed=1 frames=3190",
    "UR_BALDOSA_NATIVE_MATCH CAPTURED=1 profile1=mike profile2=andrew course=course:01 source=guest",
    "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p race_host=3000 result_host=6000 riders=0,1 hundredths=900,920 winner=1 input_frames=3190 input_runs=7 published=1",
]


class TwoPadSourceRaceAcceptance(unittest.TestCase):
    def test_native_mode_and_ci_route_are_real_sdl_pads(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(encoding="utf-8")
        mode = source.split('if (std::strcmp(opt, "33") == 0 || std::strcmp(opt, "34") == 0) {', 1)[1].split(
            "    // CI-only mode 19:", 1
        )[0]
        runner = (ROOT / "tools/run_baldosa_keyboard_pad_join_acceptance.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text(encoding="utf-8")
        self.assertIn('std::strcmp(fixture, "34") != 0', source)
        self.assertIn("SDL_AttachVirtualJoystick(&desc)", mode)
        self.assertIn("SDL_SetJoystickVirtualButton(", mode)
        self.assertIn("source_phase == 0x8610u", mode)
        self.assertIn("source_input_completed=1 frames=3190", mode)
        self.assertNotIn("SDL_KEYDOWN", mode)
        self.assertNotIn("ur_baldosa_modern_root_gamepad(", mode)
        self.assertIn('"controller_only_two_pad_race", "34"', runner)
        self.assertIn("verify_controller_only_two_pad_race(log)", runner)
        self.assertIn("controller_only_two_pad_race/log.txt", workflow)

    def test_result_requires_source_guest_and_distinct_profiles(self):
        good = "\n".join([*HOST, *SOURCE]) + "\n"
        result = verify_controller_only_two_pad_race(good)
        self.assertEqual(result["source_input_frames"], 3190)
        mutants = {
            "no original GO": [x for x in SOURCE if "source_go=1" not in x],
            "no 2P result": [x for x in SOURCE if "NATIVE_RESULT observed" not in x],
            "no source pair": [x for x in SOURCE if "NATIVE_MATCH CAPTURED" not in x],
            "wrong P2 rider": [x.replace("riders=0,1", "riders=0,2") for x in SOURCE],
            "foreign P2 profile": [x.replace("profile2=andrew", "profile2=martin") for x in SOURCE],
            "not published": [x.replace("published=1", "published=0") for x in SOURCE],
            "zero source inputs": [x.replace("input_frames=3190", "input_frames=0") for x in SOURCE],
            "premature result": [*SOURCE[:-5], SOURCE[-1], *SOURCE[-5:-1]],
            "missing P2 seat": SOURCE,
            "duplicate GO": [*SOURCE, SOURCE[-4]],
            "wrong GO phase": [x.replace("phase=8610", "phase=f60c") for x in SOURCE],
            "no drive finish": [x for x in SOURCE if "source_input_completed=1" not in x],
            "wrong driver length": [x.replace("frames=3190", "frames=3191") for x in SOURCE],
            "wrong course": [x.replace("course=course:01", "course=course:02") for x in SOURCE],
        }
        for label, body in mutants.items():
            host = HOST[:1] if label == "missing P2 seat" else HOST
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify_controller_only_two_pad_race("\n".join([*host, *body]) + "\n")


if __name__ == "__main__":
    unittest.main()
