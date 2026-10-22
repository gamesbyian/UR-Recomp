#!/usr/bin/env python3
"""The SDL controller seat-ownership seam is narrow, guarded and idempotent."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_sdl_controller_lifecycle_spike as seam

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / seam.POLICY

# Every pinned anchor, in host order, with filler between them.
HOST_STUB = "\n".join((
    "static void Earlier(void) {}",
    seam.HELPERS_ANCHOR + "  switch (event->type) {",
    seam.PAD_REMOVED + "      gi->joystick_id = -1;\n    }\n    return true;",
    seam.PAD_BUTTON + "    }\n    return true;",
    seam.RAW_REMOVED + "      memset(gi, 0, sizeof(GamepadInfo));\n    }",
    "  }\n}",
    "static void ReassignGamepads(void) {",
    seam.REASSIGN,
    "  while (running) {",
    seam.TICK_ANCHOR + "  }",
    "static void OpenOneGamepad(int i) {",
    seam.SELECTION + "}",
    "static void OpenOneJoystick(int i) {",
    seam.RAW_SELECTION + "}",
))


class BaldosaSdlControllerLifecycleSpikeTests(unittest.TestCase):
    def staged(self) -> str:
        return seam.patch_host_main(HOST_STUB, POLICY)

    def test_seam_is_idempotent_and_marks_every_site(self):
        staged = self.staged()
        self.assertEqual(seam.patch_host_main(staged, POLICY), staged)
        # Helpers, five call sites and the acceptance tick.
        self.assertGreaterEqual(staged.count(seam.MARK), 7)
        self.assertIn(f'#include "{POLICY.as_posix()}"', staged)

    def test_the_seat_steal_is_gone(self):
        staged = self.staged()
        # The original rule let player index claim an occupied seat.
        self.assertNotIn("k == 0 || g_gamepad[j].joystick_id == -1", staged)
        self.assertNotIn("scan_order", staged)
        self.assertIn("ur_controller_seat_choose(g_ur_seats", staged)
        # Occupancy is read from the live table, never a cached copy.
        self.assertIn("g_ur_seats[i].occupied = g_gamepad[i].joystick_id != -1;", staged)
        # The self-test pad keeps its seat-0 requirement, but only if vacant.
        self.assertIn("SDL_JoystickInstanceID(g_selftest_pad) == joystick_id ? 0 : -1", staged)

    def test_removal_releases_before_the_slot_is_cleared(self):
        staged = self.staged()
        pad = staged.index("case SDL_CONTROLLERDEVICEREMOVED:")
        self.assertLess(staged.index("UrSeatRelease(gi);", pad),
                        staged.index("memset(gi, 0, sizeof(GamepadInfo));", pad))
        raw = staged.index("case SDL_JOYDEVICEREMOVED:")
        self.assertLess(staged.index("UrSeatRelease(gi);", raw),
                        staged.index("memset(gi, 0, sizeof(GamepadInfo));", raw))
        release = staged[staged.index("static void UrSeatRelease"):]
        release = release[:release.index("\n}\n")]
        # Held buttons go through the ordinary release path.
        self.assertIn("HandleGamepadInput(gi, b, false)", release)
        self.assertIn("gi->axis_buttons = 0;", release)
        self.assertIn("ur_controller_seat_vacated(", release)

    def test_an_unseated_spare_is_closed_on_removal(self):
        staged = self.staged()
        removed = staged[staged.index("case SDL_CONTROLLERDEVICEREMOVED:"):]
        self.assertLess(removed.index("if (!gi) UrSpareRemoved("),
                        removed.index("    if (gi) {\n"))
        spare = staged[staged.index("static void UrSpareRemoved"):]
        spare = spare[:spare.index("\n}\n")]
        self.assertIn("SDL_GameControllerFromInstanceID(id)", spare)
        self.assertIn("SDL_GameControllerClose(pad);", spare)

    def test_a_claiming_press_is_consumed(self):
        staged = self.staged()
        button = staged[staged.index("case SDL_CONTROLLERBUTTONDOWN:"):]
        claim = button.index("UrSeatClaim(")
        # The claim returns before the ordinary routed-pad branch.
        self.assertIn("return true;", button[claim:button.index("    if (gi) {\n", claim)])
        # Only presses claim; only open, non-excluded pads can be seated.
        self.assertIn("if (!gi && event->type == SDL_CONTROLLERBUTTONDOWN)", button)
        self.assertIn("if (SelftestPadExcludes(id)) return;", staged)

    def test_product_seat_view_is_read_only_and_bounded(self):
        staged = self.staged()
        getter = staged[staged.index("long long snesrecomp_desktop_product_seat_source(int seat) {"):]
        getter = getter[:getter.index("\n}\n")]
        self.assertIn("if (seat < 0 || seat >= UR_CONTROLLER_SEAT_COUNT) return -1;", getter)
        self.assertIn("int snesrecomp_desktop_product_input_scripted(void) {\n"
                      "  return g_script_count > 0;\n}", staged)
        self.assertNotIn("=", getter.replace("!=", "").replace(">=", "").replace("<=", ""))

    def test_no_guest_binding_or_keyboard_code_is_reachable(self):
        helpers = self.staged().split(seam.HELPERS_ANCHOR)[0]
        for forbidden in ("RtlRunFrame", "g_ram", "g_sram", "keybinds_",
                          "FindCmdForGamepadButton", "g_input_state",
                          "HandleInput(", "WriteConfigFile"):
            self.assertNotIn(forbidden, helpers, forbidden)

    def test_acceptance_is_inert_unless_requested_and_fails_closed(self):
        staged = self.staged()
        self.assertIn('HostGetenv("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE")', staged)
        self.assertIn("if (!g_ur_accept_on || g_ur_accept_step < 0) return;", staged)
        self.assertIn('g_ur_accept_failed ? "fail" : "pass"', staged)
        for step in ("no_steal", "p1_reclaimed", "spare_claimed_p2",
                     "held_released_on_remove", "returning_players_not_swapped",
                     "spare_closed_on_remove"):
            self.assertIn(f'"{step}"', staged)
        # SDL2 builds get an empty tick: virtual pads there use another API.
        self.assertIn("static void UrControllerLifecycleAcceptanceTick(void) {}", staged)

    def test_a_moved_pinned_host_is_rejected(self):
        for needle in (seam.SELECTION, seam.RAW_SELECTION, seam.PAD_REMOVED,
                       seam.PAD_BUTTON, seam.RAW_REMOVED, seam.REASSIGN,
                       seam.HELPERS_ANCHOR, seam.TICK_ANCHOR):
            with self.assertRaisesRegex(ValueError, "diverged"):
                seam.patch_host_main(HOST_STUB.replace(needle, ""), POLICY)
        with self.assertRaisesRegex(ValueError, "diverged"):
            seam.patch_host_main(HOST_STUB + seam.TICK_ANCHOR, POLICY)

    def test_plan_requires_the_project_policy(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d) / "game"
            host = game / "snesrecomp/runner/src/desktop/host_main.c"
            host.parent.mkdir(parents=True)
            host.write_text(HOST_STUB, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "seat policy"):
                seam.plan(game, Path(d) / "no-ur-root")
            [(path, before, after)] = seam.plan(game, ROOT)
            self.assertEqual(path, host)
            self.assertEqual(before, HOST_STUB)
            self.assertIn(seam.MARK, after)
            # plan() never writes.
            self.assertEqual(host.read_text(encoding="utf-8"), HOST_STUB)

    def test_policy_contract_compiles_as_c_and_cpp(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "seat-policy-test"
            subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(ROOT / "native" / "product"),
                 str(ROOT / "tests" / "native" / "controller_seat_assignment_policy_test.cpp"),
                 "-o", str(exe)],
                check=True)
            subprocess.run([str(exe)], check=True)
            c_file = Path(d) / "c99.c"
            c_file.write_text(
                '#include "controller_seat_assignment_policy.h"\n'
                "int main(void) {\n"
                "  UrControllerSeatSlot s[UR_CONTROLLER_SEAT_COUNT] = {{1, 1, 0}, {1, 0, 0}};\n"
                "  return ur_controller_seat_choose(s, 1, 0, -1).seat == 1 ? 0 : 1;\n"
                "}\n", encoding="utf-8")
            subprocess.run(
                ["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-Wconversion", "-I", str(ROOT / "native" / "product"),
                 str(c_file), "-o", str(Path(d) / "c99")],
                check=True)
            subprocess.run([str(Path(d) / "c99")], check=True)


if __name__ == "__main__":
    unittest.main()
