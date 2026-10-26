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
# Self-contained source fixtures: unittest discovery does not require
# tests/ to be an importable package on every runner.
HOST = [
    "[Gamepad] UR_CONTROLLER_SEAT assign instance=101 seat=0 reason=added",
    "[Gamepad] UR_CONTROLLER_SEAT assign instance=202 seat=1 reason=added",
]
STAGES = [
    "UR_BALDOSA_MODERN_TITLE painted=1 raster=342x224 host=modern",
    "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=75 input_owned=1",
    "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared",
    "UR_BALDOSA_MODERN_ROOT selected=1",
    "UR_BALDOSA_MODERN_ROOT practice_opened=1 available=3 course=0 source_menu_required=1",
    "UR_BALDOSA_MODERN_DESTINATION stage=practice-picker raster=342x224 root=11,10,320,204 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT practice_closed=1",
    "UR_BALDOSA_MODERN_ROOT selected=2",
    "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
    "UR_BALDOSA_MODERN_DESTINATION stage=multiplayer-join raster=342x224 root=11,10,320,204 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
    "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
    "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
]


SOURCE = [
    "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike source=real_guest",
    *STAGES,
    "UR_BALDOSA_MODERN_TWO_PAD_RACE source_stock_setup=1 menu=3d phase=f60c",
    "UR_BALDOSA_MODERN_TWO_PAD_RACE source_p2_picker=right seat=2",
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
        self.assertIn("SDL_GAMEPAD_BUTTON_DPAD_RIGHT", mode)
        self.assertIn("source_p2_picker=right seat=2", mode)
        self.assertLess(mode.index("source_p2_picker=right seat=2"),
                        mode.index("source_start_pulses=5 seats=1,2"))
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
        picker_index = next(i for i, line in enumerate(SOURCE)
                            if "source_p2_picker=" in line)
        mutants = {
            "no original GO": [x for x in SOURCE if "source_go=1" not in x],
            "no P2 rider choice": [x for x in SOURCE if "source_p2_picker=" not in x],
            "wrong P2 choice": [x.replace("source_p2_picker=right", "source_p2_picker=down") for x in SOURCE],
            "P2 choice after starts": [*SOURCE[:picker_index],
                                       SOURCE[picker_index + 1], SOURCE[picker_index],
                                       *SOURCE[picker_index + 2:]],
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
