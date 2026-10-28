#!/usr/bin/env python3
"""Reject false keyboard+pad 2P admissions after host seat churn.

Source-log checks only: real SDL3 Windows execution and physical-pad QA
remain separate. The positive route must retain the moved pad's host seat
through genuine original guest menu 0x3d.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from run_baldosa_keyboard_pad_join_acceptance import verify_keyboard_plus_pad

OPEN = "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2"
P1 = "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1"
INITIAL = "[Gamepad] UR_CONTROLLER_SEAT assign instance=42 seat=0 reason=vacant"
HOST_MOVE = "[Gamepad] UR_CONTROLLER_SEAT move instance=42 from=0 to=1"
JOIN_MOVE = "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2"
P2 = "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2"
REQUEST = "UR_BALDOSA_MODERN_ROOT stock_requested players=2"
ENTER = "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d"


def joined(*lines: str) -> str:
    return "\n".join(lines) + "\n"


class KeyboardPadSeatLeaseTests(unittest.TestCase):
    def test_stable_move_passes_but_unordered_teardown_is_not_accepted(self):
        valid = joined(INITIAL, OPEN, P1, HOST_MOVE, JOIN_MOVE, P2, REQUEST, ENTER)
        verify_keyboard_plus_pad(valid)
        # A host vacate cannot be placed after guest GO by comparing
        # concatenated stdout and stderr string offsets.
        with self.assertRaisesRegex(ValueError, "ownership changed"):
            verify_keyboard_plus_pad(
                valid + "[Gamepad] UR_CONTROLLER_SEAT vacate instance=42 seat=1\n"
            )

    def test_host_root_offsets_are_not_a_guest_clock(self):
        # The actual runner concatenates stdout before stderr. Synthetic
        # interleaving cannot establish whether a move preceded the root
        # callback in guest time. The root milestone itself is source-owned.
        late = joined(INITIAL, OPEN, P1, JOIN_MOVE, HOST_MOVE, P2, REQUEST, ENTER)
        verify_keyboard_plus_pad(late)

    def test_malformed_or_embedded_host_move_cannot_count(self):
        for bad_move in (
            "[Gamepad] UR_CONTROLLER_SEAT move instance=42 from=0 to=10",
            "unrelated UR_CONTROLLER_SEAT move instance=42 from=0 to=1",
        ):
            with self.subTest(bad_move=bad_move):
                log = joined(OPEN, P1, bad_move, JOIN_MOVE, P2,
                             REQUEST, ENTER)
                with self.assertRaisesRegex(ValueError, "did not move"):
                    verify_keyboard_plus_pad(log)

    def test_host_seat_churn_before_guest_admission_is_rejected(self):
        for event in (
            "[Gamepad] UR_CONTROLLER_SEAT vacate instance=42 seat=1",
            "[Gamepad] UR_CONTROLLER_SEAT move instance=42 from=1 to=0",
            "[Gamepad] UR_CONTROLLER_SEAT claim instance=43 seat=1",
            "[Gamepad] UR_CONTROLLER_SEAT assign instance=43 seat=1 reason=vacant",
            "UR_CONTROLLER_SEAT vacate instance=42 seat=1",
        ):
            with self.subTest(event=event):
                # Each of these previously passed despite losing seat-2
                # continuity between host migration and stock admission.
                log = joined(INITIAL, OPEN, P1, HOST_MOVE, JOIN_MOVE, P2,
                             REQUEST, event, ENTER)
                with self.assertRaisesRegex(ValueError, "ownership changed"):
                    verify_keyboard_plus_pad(log)


if __name__ == "__main__":
    unittest.main()
