#!/usr/bin/env python3
"""Adversarial admission for the controller-only native title -> stock 2P path.

The log fixture is synthetic negative/positive verifier evidence only. The
Windows workflow must separately run the actual SDL virtual-pad mode 33.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from run_baldosa_keyboard_pad_join_acceptance import (
    verify_controller_only_two_pad_root,
)

HOST = [
    "[Gamepad] UR_CONTROLLER_SEAT assign instance=101 seat=0 reason=added",
    "[Gamepad] UR_CONTROLLER_SEAT assign instance=202 seat=1 reason=added",
]
STAGES = [
    "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=75 input_owned=1",
    "UR_BALDOSA_MODERN_ROOT selected=1",
    "UR_BALDOSA_MODERN_ROOT practice_opened=1 available=3 course=0 source_menu_required=1",
    "UR_BALDOSA_MODERN_DESTINATION stage=practice-picker raster=342x224 root=0,0,342,224 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT practice_closed=1",
    "UR_BALDOSA_MODERN_ROOT selected=2",
    "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
    "UR_BALDOSA_MODERN_DESTINATION stage=multiplayer-join raster=342x224 root=0,0,342,224 source=modern_product_view",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
    "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
    "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
    "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
]


class ControllerOnlyTwoPadRootAcceptance(unittest.TestCase):
    def test_source_uses_two_real_sdl_seats_and_no_keyboard_shortcut(self):
        source = (ROOT / "tools/baldosa_native_modern_root.cpp").read_text(encoding="utf-8")
        fixture = source.split('if (std::strcmp(opt, "33") == 0) {', 1)[1].split(
            "    // CI-only mode 19:", 1
        )[0]
        self.assertIn("SDL_AttachVirtualJoystick(&desc)", fixture)
        self.assertIn("SDL_SetJoystickVirtualButton(", fixture)
        self.assertIn("{164u, 0, SDL_GAMEPAD_BUTTON_SOUTH}", fixture)
        self.assertIn("{168u, 1, SDL_GAMEPAD_BUTTON_SOUTH}", fixture)
        self.assertNotIn("SDL_KEYDOWN", fixture)
        self.assertNotIn("ur_baldosa_modern_root_gamepad(", fixture)
        runner = (ROOT / "tools/run_baldosa_keyboard_pad_join_acceptance.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text(encoding="utf-8")
        self.assertIn('"controller_only_two_pad_root", "33"', runner)
        self.assertIn("verify_controller_only_two_pad_root(log)", runner)
        self.assertIn("controller_only_two_pad_root/log.txt", workflow)

    def test_native_product_route_and_mutations(self):
        good = [*HOST, *STAGES]
        verify_controller_only_two_pad_root("\n".join(good) + "\n")
        mutants = {
            "no title": [x for x in good if "entered_root=1" not in x],
            "no painted Practice": [x for x in good if "stage=practice-picker" not in x],
            "no painted join": [x for x in good if "stage=multiplayer-join" not in x],
            "missing P1 confirmation": [x for x in good if "confirmed seat=1" not in x],
            "missing P2 confirmation": [x for x in good if "confirmed seat=2" not in x],
            "missing original 2P admission": [x for x in good if "menu=3d" not in x],
            "wrong source menu": [x.replace("menu=3d", "menu=3c") for x in good],
            "missing seat P2": [x for x in good if "instance=202" not in x],
            "duplicate host P1": [*good, HOST[0]],
            "seat churn": [*good, "[Gamepad] UR_CONTROLLER_SEAT vacate instance=202 seat=1 key=abcd"],
            "wrong selection": [x.replace("selected=2", "selected=3") for x in good],
            "join before Practice close": [*HOST, *STAGES[:4], *STAGES[6:8],
                                           *STAGES[4:6], *STAGES[8:]],
            "P2 before P1": [*HOST, *STAGES[:8], STAGES[9], STAGES[8], *STAGES[10:]],
            "spurious 1P request": [*good, "UR_BALDOSA_MODERN_ROOT stock_requested players=1"],
            "duplicate admission": [*good, STAGES[-1]],
        }
        for label, candidate in mutants.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify_controller_only_two_pad_root("\n".join(candidate) + "\n")


if __name__ == "__main__":
    unittest.main()
