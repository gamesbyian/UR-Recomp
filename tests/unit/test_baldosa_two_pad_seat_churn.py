#!/usr/bin/env python3
"""Fail closed when virtual 2P host seats change before guest admission.

The Windows mode-19 fixture proves two initial assignments, but an assignment
is not a persistent seat lease. This test guards the validator against a
vacate/move/claim between initial seating and actual guest 0x3d admission.
It is log-validation evidence, not a physical-controller or release gate.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from run_baldosa_keyboard_pad_join_acceptance import verify_two_virtual_pads

SEAT0 = ("[Gamepad] UR_CONTROLLER_SEAT assign instance=41 seat=0 "
         "reason=vacant player_index=0 key=0000000000000041")
SEAT1 = ("[Gamepad] UR_CONTROLLER_SEAT assign instance=42 seat=1 "
         "reason=vacant player_index=1 key=0000000000000042")
OPEN = "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2"
P1 = "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1"
P2 = "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2"
REQUEST = "UR_BALDOSA_MODERN_ROOT stock_requested players=2"
ENTER = "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d"


class TwoPadSeatChurnTests(unittest.TestCase):
    def test_stable_seats_and_post_admission_teardown_are_allowed(self):
        stable = "\n".join((SEAT0, SEAT1, OPEN, P1, P2, REQUEST, ENTER)) + "\n"
        verify_two_virtual_pads(stable)
        verify_two_virtual_pads(stable +
                                "[Gamepad] UR_CONTROLLER_SEAT vacate instance=42 seat=1\n")

    def test_any_pre_admission_host_ownership_change_fails(self):
        for event, location in (
            ("[Gamepad] UR_CONTROLLER_SEAT vacate instance=41 seat=0", "before_join"),
            ("[Gamepad] UR_CONTROLLER_SEAT vacate instance=42 seat=1", "after_join"),
            ("[Gamepad] UR_CONTROLLER_SEAT move instance=42 from=1 to=0", "after_p1"),
            ("[Gamepad] UR_CONTROLLER_SEAT claim instance=43 seat=1", "before_entry"),
            ("UR_CONTROLLER_SEAT vacate instance=42 seat=1", "before_entry"),
        ):
            with self.subTest(event=event, location=location):
                items = [SEAT0, SEAT1]
                if location == "before_join":
                    items.append(event)
                items += [OPEN]
                if location == "after_join":
                    items.append(event)
                items += [P1]
                if location == "after_p1":
                    items.append(event)
                items += [P2, REQUEST]
                if location == "before_entry":
                    items.append(event)
                items.append(ENTER)
                with self.assertRaisesRegex(ValueError, "ownership changed"):
                    verify_two_virtual_pads("\n".join(items) + "\n")


if __name__ == "__main__":
    unittest.main()
