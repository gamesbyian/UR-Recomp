#!/usr/bin/env python3
"""The SDL3 display-lifecycle seam is narrow, guarded and idempotent."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_sdl_display_lifecycle_spike as seam
import run_baldosa_display_lifecycle_acceptance as runner

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / seam.POLICY

HOST_STUB = "\n".join((
    "/* " + seam.OPTIONS_MARK + " */",
    "static void ApplyLiveSettings(const Config *before) {",
    seam.LAUNCHER + "}",
    seam.HELPERS_ANCHOR + "  switch (event->type) {",
    seam.DEFAULT_BRANCH + "  }\n}",
    "int snesrecomp_desktop_product_apply_display(int fullscreen, int vsync) {",
    "#if SNESRECOMP_SDL3",
    seam.OPTIONS_SDL3 + "#endif\n}",
    "int main(void) {",
    seam.CREATED,
    "  while (running) {",
    seam.TICK_ANCHOR + "  }\n}",
    "static void HandleCommand(uint32 j, bool pressed) {",
    "    case kKeys_Fullscreen:",
    seam.HOTKEY + "}",
))


def acceptance_log(*, skip_rescue=False, fail=None, result="pass") -> str:
    lines = ["UR_DISPLAY fullscreen_mode=exclusive display=1 mode=1920x1080@60.000"] * 2
    for step in runner.TRANSITION_STEPS:
        ok = 0 if step == fail else 1
        lines.append(f"UR_DISPLAY_ACCEPT step={step} pass={ok} fullscreen=0")
    if skip_rescue:
        lines.append("UR_DISPLAY_ACCEPT step=offscreen_rescue not_exercised=1")
    else:
        lines.append("UR_DISPLAY_ACCEPT step=offscreen_rescue pass=1 fullscreen=0")
    lines.append(f"UR_DISPLAY_LIFECYCLE_ACCEPTANCE result={result} reconciles=1")
    return "\n".join(lines) + "\n"


class BaldosaSdlDisplayLifecycleSpikeTests(unittest.TestCase):
    def staged(self) -> str:
        return seam.patch_host_main(HOST_STUB, POLICY)

    def test_seam_is_idempotent_and_marks_every_site(self):
        staged = self.staged()
        self.assertEqual(seam.patch_host_main(staged, POLICY), staged)
        self.assertGreaterEqual(staged.count(seam.MARK), 7)
        self.assertIn(f'#include "{POLICY.as_posix()}"', staged)

    def test_every_sdl3_fullscreen_transition_decides_the_mode_first(self):
        staged = self.staged()
        options = staged[staged.index("snesrecomp_desktop_product_apply_display(int"):]
        self.assertLess(options.index("UrApplyFullscreenMode(g_config.fullscreen)"),
                        options.index("SDL_SetWindowFullscreen(g_window, want != 0)"))
        launcher = staged[staged.index("static void ApplyLiveSettings"):]
        self.assertLess(launcher.index("UrApplyFullscreenMode(g_config.fullscreen);"),
                        launcher.index("SDL_SetWindowFullscreen(g_window, want);"))
        hotkey = staged[staged.index("case kKeys_Fullscreen:"):]
        # Alt+Enter is windowed<->borderless: always clear an exclusive mode.
        self.assertLess(hotkey.index("UrApplyFullscreenMode(1);"),
                        hotkey.index("SDL_SetWindowFullscreen(g_window, g_win_flags"))
        created = staged[staged.index(seam.CREATED):]
        self.assertIn("if (g_config.fullscreen == 2 && !UrApplyFullscreenMode(2))", created)

    def test_exclusive_uses_the_displays_own_desktop_mode(self):
        staged = self.staged()
        self.assertIn("SDL_GetClosestFullscreenDisplayMode(display, desktop->w, desktop->h", staged)
        self.assertIn("SDL_SetWindowFullscreenMode(g_window, &mode)", staged)
        self.assertIn("SDL_SetWindowFullscreenMode(g_window, NULL)", staged)
        # An unavailable exclusive mode is a refusal, never silently borderless.
        apply = staged[staged.index("static int UrApplyFullscreenMode"):]
        apply = apply[:apply.index("\n}\n")]
        self.assertIn("exclusive_unavailable", apply)
        self.assertIn("return 0;", apply)

    def test_display_events_are_observed_in_every_pump_and_never_consumed(self):
        staged = self.staged()
        default = staged[staged.index("  default:\n    UrDisplayEvent(event);"):]
        self.assertTrue(default.split("\n", 2)[2].startswith("    return false;"))
        for event in ("SDL_EVENT_WINDOW_DISPLAY_CHANGED",
                      "SDL_EVENT_WINDOW_DISPLAY_SCALE_CHANGED",
                      "SDL_EVENT_DISPLAY_DESKTOP_MODE_CHANGED",
                      "SDL_EVENT_DISPLAY_ADDED", "SDL_EVENT_DISPLAY_REMOVED"):
            self.assertIn(f"case {event}:", staged)
        # The event we cause ourselves when moding the window is not watched.
        self.assertNotIn("SDL_EVENT_DISPLAY_CURRENT_MODE_CHANGED", staged)
        reconcile = staged[staged.index("static void UrDisplayReconcile"):]
        reconcile = reconcile[:reconcile.index("\nstatic void UrDisplayEvent")]
        self.assertIn("ur_display_window_reachable(win, usable, n, 32)", reconcile)
        self.assertIn("ur_display_window_rescue(", reconcile)
        self.assertIn("ChangeWindowScale(0);", reconcile)

    def test_no_guest_input_or_timing_code_is_reachable(self):
        helpers = self.staged().split(seam.HELPERS_ANCHOR)[0]
        for forbidden in ("RtlRunFrame", "g_ram", "g_sram", "g_pad_buttons",
                          "g_input_state", "snes_host_clock", "WriteConfigFile",
                          "g_simulation_hz"):
            self.assertNotIn(forbidden, helpers, forbidden)

    def test_requires_the_options_seam_and_rejects_a_moved_host(self):
        with self.assertRaisesRegex(ValueError, "options_spike"):
            seam.patch_host_main(HOST_STUB.replace(seam.OPTIONS_MARK, "X"), POLICY)
        for needle in (seam.HELPERS_ANCHOR, seam.DEFAULT_BRANCH, seam.OPTIONS_SDL3,
                       seam.LAUNCHER, seam.HOTKEY, seam.CREATED, seam.TICK_ANCHOR):
            with self.assertRaisesRegex(ValueError, "diverged"):
                seam.patch_host_main(HOST_STUB.replace(needle, ""), POLICY)
        with self.assertRaisesRegex(ValueError, "diverged"):
            seam.patch_host_main(HOST_STUB + seam.CREATED, POLICY)

    def test_plan_requires_the_project_policy_and_never_writes(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d) / "game"
            host = game / "snesrecomp/runner/src/desktop/host_main.c"
            host.parent.mkdir(parents=True)
            host.write_text(HOST_STUB, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "display policy"):
                seam.plan(game, Path(d) / "no-ur-root")
            [(path, before, after)] = seam.plan(game, ROOT)
            self.assertEqual((path, before), (host, HOST_STUB))
            self.assertIn(seam.MARK, after)
            self.assertEqual(host.read_text(encoding="utf-8"), HOST_STUB)

    def test_runner_is_fail_closed(self):
        self.assertEqual(runner.verify_log(acceptance_log())["offscreen_rescue"], "pass")
        skipped = runner.verify_log(acceptance_log(skip_rescue=True))
        self.assertEqual(skipped["offscreen_rescue"], "not_exercised")
        with self.assertRaisesRegex(ValueError, "failed"):
            runner.verify_log(acceptance_log(fail="borderless_to_exclusive"))
        with self.assertRaisesRegex(ValueError, "single pass"):
            runner.verify_log(acceptance_log(result="fail"))
        with self.assertRaisesRegex(ValueError, "differ"):
            runner.verify_log(acceptance_log().replace("step=borderless pass", "step=x pass"))
        with self.assertRaisesRegex(ValueError, "exclusive"):
            runner.verify_log("\n".join(
                l for l in acceptance_log().splitlines()
                if "fullscreen_mode=exclusive" not in l))

    def test_policy_contract_compiles_as_c_and_cpp(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "display-policy-test"
            subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(ROOT / "native" / "product"),
                 str(ROOT / "tests" / "native" / "display_window_lifecycle_policy_test.cpp"),
                 "-o", str(exe)],
                check=True)
            subprocess.run([str(exe)], check=True)
            c_file = Path(d) / "c99.c"
            c_file.write_text(
                '#include "display_window_lifecycle_policy.h"\n'
                "int main(void) {\n"
                "  UrDisplayRect d = {0, 0, 100, 100}, w = {0, 0, 50, 50};\n"
                "  return ur_display_window_reachable(w, &d, 1, 32) ? 0 : 1;\n"
                "}\n", encoding="utf-8")
            subprocess.run(
                ["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-Wconversion", "-I", str(ROOT / "native" / "product"),
                 str(c_file), "-o", str(Path(d) / "c99")],
                check=True)
            subprocess.run([str(Path(d) / "c99")], check=True)


if __name__ == "__main__":
    unittest.main()
