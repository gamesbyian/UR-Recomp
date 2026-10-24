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
    seam.RAW_BUTTON + "    return true;",
    "  }\n}",
    "static void PollKeyboardControls(const uint8_t *keys) {",
    seam.KEYBOARD_P1 + "}",
    "static uint32 GetActiveControllers(void) {",
    "  uint32 ctrl = g_script_controllers |",
    seam.ACTIVE_P1 + "                0;\n}",
    "static void RunInGameLauncher(void) {",
    "  SDL_ShowWindow(g_window);",
    seam.LAUNCHER_RETURN + "}",
    "static void ReassignGamepads(void) {",
    seam.REASSIGN,
    "static void OpenAllGamepads(void) {\n#if SNESRECOMP_SDL3\n  int njs = 0;",
    seam.ENUMERATE + "  int njs = SDL_NumJoysticks();\n#endif\n}",
    "int snesrecomp_desktop_main(void) {",
    seam.BACKGROUND + "}",
    "  while (running) {",
    seam.TICK_ANCHOR + "  }",
    "static void OpenOneGamepad(int i) {",
    seam.SELECTION + seam.PAD_FOUND + "}",
    "static void OpenOneJoystick(int i) {",
    seam.RAW_SELECTION + seam.RAW_UNSEATED + "}",
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

    def test_spares_are_owned_once_and_closed_on_removal(self):
        staged = self.staged()
        for removed_case in ("case SDL_CONTROLLERDEVICEREMOVED:", "case SDL_JOYDEVICEREMOVED:"):
            removed = staged[staged.index(removed_case):]
            self.assertLess(removed.index("if (!gi) UrSpareRemoved("),
                            removed.index("    if (gi"))
        # An unseated mapped pad and an unseated raw stick are both kept.
        self.assertIn("if (found_idx < 0) UrSpareKeep(joystick_id, controller, NULL);", staged)
        self.assertIn("if (slot < 0) { UrSpareKeep(id, NULL, joystick); return; }", staged)
        self.assertNotIn("if (slot < 0) { SDL_JoystickClose(joystick); return; }", staged)
        keep = staged[staged.index("static void UrSpareKeep"):]
        keep = keep[:keep.index("\n}\n")]
        # A second open of a held spare drops the extra handle.
        self.assertIn("free_slot = -2;", keep)
        self.assertIn("if (pad) SDL_GameControllerClose(pad);", keep)
        self.assertIn("if (raw) SDL_JoystickClose(raw);", keep)
        # Re-seating closes every spare before OpenAllGamepads reopens them.
        reset = staged[staged.index("static void UrSeatReset(void) {"):]
        self.assertIn("for (int i = 0; i < kUrSpareMax; i++) UrSpareClose(i);",
                      reset[:reset.index("\n}\n")])

    def test_a_claiming_press_is_consumed(self):
        staged = self.staged()
        button = staged[staged.index("case SDL_CONTROLLERBUTTONDOWN:"):]
        claim = button.index("UrSeatClaim(")
        # The claim returns before the ordinary routed-pad branch.
        self.assertIn("return true;", button[claim:button.index("    if (gi) {\n", claim)])
        # Only presses claim; only open, non-excluded pads can be seated.
        self.assertIn("if (!gi && event->type == SDL_CONTROLLERBUTTONDOWN)", button)
        self.assertIn("UrSeatClaim(SNESRECOMP_SDL_EVENT_BUTTON_DEVICE(*event), false)", button)
        raw = staged[staged.index("case SDL_JOYBUTTONDOWN:"):]
        self.assertIn("if (!gi && event->type == SDL_JOYBUTTONDOWN &&\n"
                      "        UrSeatClaim(event->jbutton.which, true))\n      return true;", raw)
        claim_fn = staged[staged.index("static int UrSeatClaim"):]
        claim_fn = claim_fn[:claim_fn.index("\n}\n")]
        # A mapped pad's raw joystick events can never claim (and leak the press).
        self.assertIn("(raw ? !g_ur_spare[i].raw : !g_ur_spare[i].pad)", claim_fn)
        self.assertIn("SelftestPadExcludes(id)", claim_fn)

    def test_hotplug_missed_during_the_launcher_is_reconciled(self):
        staged = self.staged()
        back = staged[staged.index("static void RunInGameLauncher(void) {"):]
        self.assertIn('SDL_FlushEvent(SDL_QUIT);\n  UrSeatReconcile("launcher_returned");', back)
        fn = staged[staged.index("static void UrSeatReconcile(const char *why) {"):]
        fn = fn[:fn.index("\n}\n")]
        # Gone seats go through the ordinary release, so held bits are let go
        # and seat memory is kept for the owner's return.
        self.assertLess(fn.index("if (attached) continue;"), fn.index("UrSeatRelease(gi);"))
        self.assertIn("UrSpareRemoved(g_ur_spare[i].id)", fn)
        # Devices already seated, held as spares or excluded are never reopened.
        self.assertIn("if (GetGamepadInfo(id) || UrSpareFind(id) >= 0 || SelftestPadExcludes(id)) continue;", fn)
        self.assertIn("OpenOneGamepad(open_arg);", fn)
        # SDL2 opens by device index, SDL3 by instance id.
        self.assertIn("const int open_arg = (int)id;", fn)
        self.assertIn("const int open_arg = i;", fn)

    def test_keyboard_falls_back_to_p1_only_without_a_seated_pad(self):
        staged = self.staged()
        poll = staged[staged.index("static void PollKeyboardControls"):]
        self.assertIn("uint32 p1 = UrKeyboardDrives(0) ?", poll[:poll.index("\n}\n")])
        active = staged[staged.index("static uint32 GetActiveControllers(void) {"):]
        self.assertIn("(UrKeyboardDrives(0) ? 1u : 0u)", active[:active.index("\n}\n")])
        rule = staged[staged.index("static bool UrKeyboardDrives(int player) {"):]
        rule = rule[:rule.index("\n}\n")]
        # Keyboard-sourced players as before; P1 only on Gamepad with an empty
        # seat, and never while P2 uses the same (default) keys.
        self.assertIn("if (src == 1) return true;", rule)
        self.assertIn("player == 0 && src == 2 && g_gamepad[0].joystick_id == -1", rule)
        self.assertIn("g_config.player_src[1] != 1", rule)

    def test_seat_move_releases_first_and_frees_the_old_seat(self):
        staged = self.staged()
        move = staged[staged.index("int snesrecomp_desktop_product_seat_move(int from, int to) {"):]
        move = move[:move.index("\n}\n")]
        # Refuses bad, occupied or disabled targets.
        self.assertIn("from == to) return 0;", move)
        self.assertIn("dst->joystick_id != -1 ||", move)
        self.assertIn("!g_config.enable_gamepad[to]) return 0;", move)
        # Held bits go before the slot is cleared; nobody is "away" from the
        # old seat; the new seat is recorded through the policy.
        self.assertLess(move.index("HandleGamepadInput(src, b, false)"),
                        move.index("memset(src, 0, sizeof(GamepadInfo));"))
        self.assertIn("g_ur_seats[from].absent_owner_key = 0;", move)
        self.assertIn("ur_controller_seat_taken(g_ur_seats, to, key);", move)

    def test_a_pads_player_number_shows_its_seat(self):
        staged = self.staged()
        assign = staged[staged.index("static int UrSeatAssign("):]
        assign = assign[:assign.index("\n}\n")]
        # Set before an unseated return, so a spare shows -1, then every
        # seated pad SDL may have bumped is told its seat again.
        self.assertLess(assign.index("SDL_JoystickSetPlayerIndex(joystick, choice.seat);"),
                        assign.index("if (choice.seat < 0) return -1;"))
        self.assertLess(assign.index("UrSeatShowPlayerIndex();"),
                        assign.index("if (choice.seat < 0) return -1;"))
        show = staged[staged.index("static void UrSeatShowPlayerIndex(void) {"):]
        show = show[:show.index("\n}\n")]
        self.assertIn("SDL_JoystickSetPlayerIndex(j, i);", show)
        self.assertNotIn("g_config", show)
        move = staged[staged.index("int snesrecomp_desktop_product_seat_move(int from, int to) {"):]
        move = move[:move.index("\n}\n")]
        self.assertLess(move.index("ur_controller_seat_taken(g_ur_seats, to, key);"),
                        move.index("SDL_JoystickSetPlayerIndex(moved, to);"))

    def test_pads_found_together_are_seated_in_player_index_order(self):
        staged = self.staged()
        start = staged[staged.index("static void OpenAllGamepads(void) {"):]
        self.assertIn("SDL_GetJoysticks(&njs);\n  UrSortByPlayerIndex(joysticks, njs);",
                      start[:start.index("\n}")])
        fn = staged[staged.index("static void UrSeatReconcile(const char *why) {"):]
        fn = fn[:fn.index("\n}\n")]
        self.assertIn("SDL_GetJoysticks(&count);\n  UrSortByPlayerIndex(ids, count);", fn)
        sort = staged[staged.index("static void UrSortByPlayerIndex("):]
        sort = sort[:sort.index("\n}\n")]
        rank = staged[staged.index("static uint64_t UrSeatingRank(SDL_JoystickID id) {"):]
        rank = rank[:rank.index("\n}\n")]
        # Gamepads before unmapped sticks; then the index, unsigned so an
        # unknown index (-1) sorts after every real one.
        self.assertIn("(SDL_IsGamepad(id) ? 0u : 1u) << 32", rank)
        self.assertIn("(uint32_t)SDL_GetJoystickPlayerIndexForID(id)", rank)
        self.assertIn("UrSeatingRank(ids[j - 1]) > rank", sort)
        # SDL3 only: SDL2 enumerates by device index.
        before = staged[:staged.index("static void UrSortByPlayerIndex(")]
        self.assertTrue(before.rstrip().endswith("#if SNESRECOMP_SDL3") or
                        before[before.rindex("#if SNESRECOMP_SDL3"):].count("#endif") == 0)

    def test_pads_are_ignored_while_the_window_is_unfocused(self):
        staged = self.staged()
        self.assertNotIn(seam.BACKGROUND, staged)
        self.assertIn('HostGetenv("UR_BACKGROUND_PAD_INPUT")', staged)
        # Off unless a test opts in with a non-zero value.
        self.assertIn('SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, '
                      'bg && atoi(bg) ? "1" : "0");', staged)
        focus = staged[staged.index("if (g_ur_accept_on == 3) {"):]
        focus = focus[:focus.index("g_ur_accept_step = 1000;")]
        # Not exercised unless focus really left, never a silent pass.
        self.assertLess(focus.index("SDL_GetKeyboardFocus() != NULL"),
                        focus.index('"unfocused_press_ignored"'))
        self.assertIn("unfocused_press_ignored not_exercised=1", focus)
        self.assertIn("focused_press_drives not_exercised=1", focus)

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
        production, acceptance = helpers.split("enum { kUrAcceptPads", 1)
        for forbidden in ("RtlRunFrame", "g_ram", "g_sram", "keybinds_",
                          "FindCmdForGamepadButton", "g_input_state",
                          "HandleInput(", "WriteConfigFile"):
            self.assertNotIn(forbidden, production, forbidden)
        # The test-only scenario may read the keyboard word through the host's
        # own poll, and always restores the real keyboard state afterwards.
        for forbidden in ("RtlRunFrame", "g_ram", "g_sram", "keybinds_",
                          "HandleInput(", "WriteConfigFile"):
            self.assertNotIn(forbidden, acceptance, forbidden)
        probe = acceptance[acceptance.index("static uint32 UrAcceptKeyboardWord(void) {"):]
        probe = probe[:probe.index("\n}\n")]
        self.assertIn("PollKeyboardControls(snesrecomp_sdl_get_keyboard_state());", probe)

    def test_acceptance_is_inert_unless_requested_and_fails_closed(self):
        staged = self.staged()
        self.assertIn('HostGetenv("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE")', staged)
        self.assertIn("if (!g_ur_accept_on || g_ur_accept_step < 0) return;", staged)
        self.assertIn('g_ur_accept_failed ? "fail" : "pass"', staged)
        for step in ("no_steal", "p1_reclaimed", "spare_claimed_p2",
                     "held_released_on_remove", "returning_players_not_swapped",
                     "spare_closed_on_remove", "lone_pad_with_p2_index_takes_p1",
                     "enumeration_follows_player_index",
                     "gamepad_seated_before_raw_stick"):
            self.assertIn(f'"{step}"', staged)
        # SDL2 builds get an empty tick: virtual pads there use another API.
        self.assertIn("static void UrControllerLifecycleAcceptanceTick(void) {}", staged)

    def test_a_moved_pinned_host_is_rejected(self):
        for needle in (seam.SELECTION, seam.RAW_SELECTION, seam.PAD_REMOVED,
                       seam.PAD_BUTTON, seam.RAW_REMOVED, seam.REASSIGN,
                       seam.HELPERS_ANCHOR, seam.TICK_ANCHOR, seam.ENUMERATE,
                       seam.BACKGROUND):
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
