#!/usr/bin/env python3
"""The Modern 2P join's keyboard + one pad and seat-left rules (#2225)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_baldosa_keyboard_pad_join_acceptance as runner

SOURCE = (ROOT / "tools" / "baldosa_native_modern_root.cpp").read_text(encoding="utf-8")


def body(start: str) -> str:
    text = SOURCE[SOURCE.index(start):]
    return text[:text.index("\n}\n")]


class KeyboardPadJoinTests(unittest.TestCase):
    def test_only_a_keyboard_p1_lets_the_lone_pad_join_as_p2(self):
        pad = body('extern "C" int ur_baldosa_modern_root_gamepad(')
        move = pad[pad.index("// Keyboard + one pad"):]
        move = move[:move.index("return 1;")]
        for condition in ("g_join_p1_by_keyboard", "g_two_seat_join.confirmed(0)",
                          "!g_two_seat_join.confirmed(1)", "g_stock_target == -1",
                          "snesrecomp_desktop_product_seat_source(1) == -1",
                          "snesrecomp_desktop_product_seat_source(0) != -1"):
            self.assertIn(condition, move)
        # The move is the last condition: nothing moves unless all hold.
        self.assertIn("snesrecomp_desktop_product_seat_move(0, 1)) {\n"
                      "        g_p2_join_edges.reset();\n", move)
        # Only the keyboard path marks a keyboard P1 confirmation.
        self.assertEqual(SOURCE.count("g_join_p1_by_keyboard = true;"), 1)
        key = body('extern "C" int ur_baldosa_modern_root_key(')
        self.assertIn("g_join_p1_by_keyboard = true;", key)

    def test_a_p2_whose_device_left_is_withdrawn_but_a_scripted_join_is_not(self):
        present = body("bool join_p2_owner_present() {")
        self.assertIn("g_join_p2_source == -1 ||", present)
        confirm = body("void join_confirm(unsigned seat) {")
        self.assertLess(confirm.index("join_watch_seat_owners();"),
                        confirm.index("g_two_seat_join.confirm(seat)"))
        self.assertIn("if (seat == 1) g_join_p2_source = snesrecomp_desktop_product_seat_source(1);",
                      confirm)
        admissible = body("bool confirmed_join_still_admissible() {")
        self.assertIn("if (!join_p2_owner_present()) return false;", admissible)
        watch = body("void join_watch_seat_owners() {")
        self.assertIn("g_two_seat_join.clear(1);", watch)

    def test_the_moved_pad_returns_only_when_its_join_is_over(self):
        back = body("void join_return_moved_pad() {")
        self.assertIn("g_two_seat_join.open() ||\n        g_stock_target != -1) return;", back)
        # Only the pad the join moved, only into an empty seat 1.
        self.assertLess(back.index("snesrecomp_desktop_product_seat_source(1) != g_join_moved_source"),
                        back.index("snesrecomp_desktop_product_seat_move(1, 0)"))
        self.assertLess(back.index("snesrecomp_desktop_product_seat_source(0) != -1) return;"),
                        back.index("snesrecomp_desktop_product_seat_move(1, 0)"))
        pad = body('extern "C" int ur_baldosa_modern_root_gamepad(')
        self.assertIn("g_join_moved_source = snesrecomp_desktop_product_seat_source(1);", pad)
        draw = body('extern "C" int ur_baldosa_modern_root_draw_frame(')
        self.assertIn("join_return_moved_pad();", draw)

    def test_positive_join_requires_actual_guest_2p_entry(self):
        stages = (
            "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
            "[Gamepad] UR_CONTROLLER_SEAT assign instance=42 seat=0 reason=vacant",
            "UR_CONTROLLER_SEAT move instance=42 from=0 to=1",
            "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
            "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
            "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
        )
        valid = "\n".join(stages) + "\n"
        runner.verify_keyboard_plus_pad(valid)
        # Previously the runner accepted a request that never entered the
        # real 2P guest screen, and did not reject subsequent route failure.
        for invalid in (
            valid.replace(stages[-1] + "\n", ""),
            valid.replace(stages[-1], stages[-1] + "\n" + stages[-1]),
            valid + "UR_BALDOSA_MODERN_ROOT stock_rejected=timeout\n",
            valid + "UR_BALDOSA_MODERN_ROOT stock_requested players=1\n",
            valid + "UR_BALDOSA_MODERN_ROOT join_seat_left seat=2\n",
        ):
            with self.subTest(invalid=invalid[-100:]):
                with self.assertRaises(ValueError):
                    runner.verify_keyboard_plus_pad(invalid)

    def test_split_stream_host_churn_before_move_cannot_pass_as_stable(self):
        # run_game concatenates all host stdout before all product stderr.
        # A pre-move vacate used to be invisible to the old slice beginning
        # at the move and could falsely satisfy the stock GO seat check.
        initial = ("[Gamepad] UR_CONTROLLER_SEAT assign instance=42 seat=0 "
                   "reason=vacant player_index=0 key=0000000000000042")
        move = "[Gamepad] UR_CONTROLLER_SEAT move instance=42 from=0 to=1"
        root = "\n".join((
            "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
            "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
            "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
            "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
        )) + "\n"
        runner.verify_keyboard_plus_pad(initial + "\n" + move + "\n" + root)
        with self.assertRaisesRegex(ValueError, "initial SDL P1 assignment"):
            runner.verify_keyboard_plus_pad(move + "\n" + root)
        with self.assertRaisesRegex(ValueError, "initial SDL P1 assignment"):
            runner.verify_keyboard_plus_pad(
                initial.replace("instance=42", "instance=43") + "\n" +
                move + "\n" + root)
        for extra in (
            initial,
            initial.replace("instance=42", "instance=43"),
            "[Gamepad] UR_CONTROLLER_SEAT assign instance=43 seat=1 reason=vacant",
        ):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                runner.verify_keyboard_plus_pad(
                    initial + "\n" + extra + "\n" + move + "\n" + root)
        for churn in (
            "[Gamepad] UR_CONTROLLER_SEAT vacate instance=42 seat=0",
            "[Gamepad] UR_CONTROLLER_SEAT claim instance=43 seat=0",
        ):
            with self.subTest(churn=churn), self.assertRaisesRegex(
                    ValueError, "ownership changed"):
                runner.verify_keyboard_plus_pad(
                    initial + "\n" + churn + "\n" + move + "\n" + root)
        # With independent stdout/stderr buffering, even apparent teardown
        # after the root milestone cannot be time-ordered. Fail closed.
        with self.assertRaisesRegex(ValueError, "ownership changed"):
            runner.verify_keyboard_plus_pad(
                initial + "\n" + move + "\n" +
                "[Gamepad] UR_CONTROLLER_SEAT vacate instance=42 seat=1\n" + root)

    def test_native_join_milestones_must_be_complete_lines(self):
        # Negative control: old substring matching would accept a menu
        # identifier with a longer suffix as genuine guest 0x3d admission.
        stages = (
            "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
            "[Gamepad] UR_CONTROLLER_SEAT assign instance=42 seat=0 reason=vacant",
            "[Gamepad] UR_CONTROLLER_SEAT move instance=42 from=0 to=1",
            "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
            "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
            "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
        )
        valid = "\n".join(stages) + "\n"
        runner.verify_keyboard_plus_pad(valid)
        for old, new in (
            (stages[-1], stages[-1] + "0"),
            (stages[-1], "prefix " + stages[-1]),
            (stages[-3], stages[-3] + "0"),
            (stages[-2], stages[-2] + "0"),
        ):
            with self.subTest(new=new):
                with self.assertRaisesRegex(ValueError, "complete line"):
                    runner.verify_keyboard_plus_pad(valid.replace(old, new))

    def test_positive_capture_window_and_failure_milestones(self):
        # The source-bound Windows 2P route uses 1800 turbo frames. The
        # shortened negative captures must remain independent of that wait.
        self.assertEqual(runner.POSITIVE_JOIN, "turbo on\nwait 1800\nquit\n")
        self.assertEqual(runner.JOIN, "wait 400\nquit\n")
        log = ("unrelated output\n"
               "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2\n"
               "UR_BALDOSA_MODERN_ROOT stock_requested players=2\n"
               "UR_BALDOSA_MODERN_ROOT stock_rejected=timeout\n"
               "UR_BALDOSA_MODERN_ROOT records_closed=1\n")
        self.assertEqual(runner.route_milestones(log), [
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
            "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
            "UR_BALDOSA_MODERN_ROOT stock_rejected=timeout",
        ])

    def test_cancelled_or_withdrawn_join_forbids_any_stock_entry(self):
        runner.reject_unexpected_stock_route("join_closed=1\n", "cancelled")
        for invalid in (
            "UR_BALDOSA_MODERN_ROOT stock_requested players=1\n",
            "UR_BALDOSA_MODERN_ROOT stock_requested players=2\n",
            "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d\n",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "unexpected"):
                    runner.reject_unexpected_stock_route(invalid, "cancelled")


    def test_two_virtual_pads_require_distinct_host_seats_and_guest_entry(self):
        seat0 = ("[Gamepad] UR_CONTROLLER_SEAT assign instance=41 seat=0 "
                 "reason=vacant player_index=0 key=0000000000000041")
        seat1 = ("[Gamepad] UR_CONTROLLER_SEAT assign instance=42 seat=1 "
                 "reason=vacant player_index=1 key=0000000000000042")
        stages = (
            "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
            "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
            "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
            "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
        )
        valid = "\n".join((seat0, seat1, *stages)) + "\n"
        runner.verify_two_virtual_pads(valid)
        for invalid in (
            valid.replace(seat1 + "\n", ""),
            valid.replace("instance=42", "instance=41"),
            valid.replace("seat=1 reason=", "seat=0 reason="),
            valid.replace(stages[-1] + "\n", ""),
            valid.replace(stages[-1], stages[-1] + "0"),
            valid.replace(seat0 + "\n", "").replace(
                stages[0], stages[0] + "\n" + seat0),
            valid + "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2\n",
            valid + "UR_BALDOSA_MODERN_ROOT stock_rejected=timeout\n",
        ):
            with self.subTest(invalid=invalid[-120:]):
                with self.assertRaises(ValueError):
                    runner.verify_two_virtual_pads(invalid)

    def test_two_virtual_pad_mode_uses_host_event_pump(self):
        source = body('extern "C" void ur_baldosa_modern_root_after_run_frame(')
        mode = source[source.index('if (std::strcmp(opt, "19") == 0)'):]
        mode = mode[:mode.index('    // TEST ONLY modes 15/16')]
        for token in ("SDL_AttachVirtualJoystick", "SDL_OpenJoystick",
                      "SDL_SetJoystickVirtualButton", "SDL_GAMEPAD_BUTTON_SOUTH",
                      "frame == 68u", "frame == 72u", "SDL_PushEvent"):
            self.assertIn(token, mode)
        for forbidden in ("g_ram[", "join_confirm(", "ur_baldosa_modern_root_gamepad("):
            self.assertNotIn(forbidden, mode)

    def test_runner_order_check_fails_closed(self):
        runner.ordered("a\nb\n", ("a", "b"), "ok")
        with self.assertRaisesRegex(ValueError, "out of order"):
            runner.ordered("b\na\n", ("a", "b"), "x")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            runner.ordered("a\na\nb\n", ("a", "b"), "x")


if __name__ == "__main__":
    unittest.main()
