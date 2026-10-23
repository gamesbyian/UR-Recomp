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
            "UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2",
            "UR_CONTROLLER_SEAT move instance=42 from=0 to=1",
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

    def test_runner_order_check_fails_closed(self):
        runner.ordered("a\nb\n", ("a", "b"), "ok")
        with self.assertRaisesRegex(ValueError, "out of order"):
            runner.ordered("b\na\n", ("a", "b"), "x")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            runner.ordered("a\na\nb\n", ("a", "b"), "x")


if __name__ == "__main__":
    unittest.main()
