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
    "static double DisplayRefresh(void) { return 60; }",
    seam.VSYNC + "  return 1;\n}",
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
    "  if (!g_renderer_funcs.Initialize(window)) {}",
    seam.RENDERER_READY,
    "  while (running) {",
    seam.TICK_ANCHOR + "  }\n}",
    seam.PRODUCT_KEY + "  int j = FindCmdForSdlKey(keyCode, (SDL_Keymod)keyMod);\n}",
    "void ChangeWindowScale(int scale_step) {",
    seam.SCALE_STEP + "}",
    "static void RunInGameLauncher(void) {",
    seam.LAUNCHER_RETURN + "}",
    "static void Shutdown(void) {",
    seam.EXIT_SAVE + "  if (g_volume_changed || g_fullscreen_changed) {}\n}",
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
    lines.append("UR_DISPLAY_ACCEPT step=window_scale_step_persisted pass=1 fullscreen=0")
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

    def test_only_an_explicit_window_size_step_is_persisted(self):
        staged = self.staged()
        scale = staged[staged.index("void ChangeWindowScale(int scale_step) {"):]
        scale = scale[:scale.index("\n}")]
        self.assertIn("if (scale_step != 0 && new_scale != g_config.window_scale) {", scale)
        self.assertIn("g_config.window_scale = (uint8)new_scale;", scale)
        # Written by the host's existing exit-time config write.
        self.assertIn("g_fullscreen_changed = true;", scale)

    def test_window_placement_is_restored_after_renderer_and_saved_at_exit(self):
        staged = self.staged()
        # After the renderer: an OpenGL renderer can recreate the window.
        self.assertLess(staged.index("UrRestoreWindowPlacement();"),
                        staged.index(seam.RENDERER_READY))
        self.assertLess(staged.index("g_renderer_funcs.Initialize(window)"),
                        staged.index("UrRestoreWindowPlacement();"))
        shutdown = staged[staged.index("static void Shutdown(void) {"):]
        self.assertLess(shutdown.index("UrSaveWindowPlacement();"),
                        shutdown.index("g_volume_changed || g_fullscreen_changed"))
        restore = staged[staged.index("static void UrRestoreWindowPlacement(void) {"):]
        restore = restore[:restore.index("\nstatic void UrSaveWindowPlacement")]
        # Identity by name + bounds via the policy; a miss stays on primary.
        self.assertIn("ur_display_placement_match(name, bounds, candidates, n)", restore)
        self.assertIn("saved_display_missing", restore)
        self.assertIn('strncmp(line, "ur-window-placement-v1", 22) != 0', restore)
        # A saved windowed position is used only if still reachable.
        self.assertIn("ur_display_window_reachable(want, usable, u, 32)", restore)
        save = staged[staged.index("static void UrSaveWindowPlacement(void) {"):]
        save = save[:save.index("\n#else")]
        # Fullscreen/minimized/maximized never overwrite the windowed spot.
        self.assertIn("SDL_WINDOW_FULLSCREEN | SDL_WINDOW_MINIMIZED | SDL_WINDOW_MAXIMIZED", save)
        # Maximized is its own state; the windowed spot under it is kept.
        self.assertIn('fputs("maximized=1\\n", f);', save)
        self.assertIn('else if (strcmp(line, "maximized=1") == 0)', restore)
        self.assertLess(restore.index("ur_display_window_reachable(want, usable, u, 32)"),
                        restore.index("SDL_MaximizeWindow(g_window);"))
        self.assertIn("*c == '\\r' || *c == '\\n' ? ' ' : *c", save)

    def test_display_changes_missed_during_the_launcher_are_reconciled(self):
        staged = self.staged()
        back = staged[staged.index("static void RunInGameLauncher(void) {"):]
        self.assertIn('SDL_FlushEvent(SDL_QUIT);\n#if SNESRECOMP_SDL3\n  UrDisplayReconcile("launcher_returned");', back)

    def test_vsync_never_waits_on_a_panel_slower_than_the_game(self):
        staged = self.staged()
        vsync = staged[staged.index("static int VSyncInterval(void) {"):]
        vsync = vsync[:vsync.index("\n}\n")]
        # The project policy decides; a slow panel presents without waiting.
        self.assertIn("ur_display_vsync_cannot_carry(panel, g_simulation_hz)", vsync)
        self.assertIn("if (slow) return 0;", vsync)
        # Decoupled presentation and disabled frame delay come first, unchanged.
        self.assertLess(vsync.index("PresentationDecoupled() || g_config.disable_frame_delay"),
                        vsync.index("UrPanelRefresh()"))
        self.assertLess(staged.index(f'#include "{POLICY.as_posix()}"'),
                        staged.index("static int VSyncInterval(void) {"))
        event = staged[staged.index("static void UrDisplayEvent(const SDL_Event *event) {"):]
        event = event[:event.index("\n}\n")]
        for kind in ("SDL_EVENT_WINDOW_DISPLAY_CHANGED", "SDL_EVENT_DISPLAY_DESKTOP_MODE_CHANGED",
                     "SDL_EVENT_WINDOW_ENTER_FULLSCREEN"):
            self.assertIn(kind, event)
        self.assertIn("UrReapplyVsync();", event)

    def test_alt_enter_is_never_a_modern_menu_key(self):
        staged = self.staged()
        handler = staged[staged.index("static void HandleInput(int keyCode"):]
        handler = handler[:handler.index("\n}")]
        command = handler.index("== kKeys_Fullscreen;")
        self.assertLess(command, handler.index("g_game->product_system_key(keyCode"))
        self.assertIn("if (!ur_window_command && g_game->product_system_key &&", handler)

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
        staged = self.staged()
        start = staged.index(f'#include "{POLICY.as_posix()}"')
        end = staged.index("\n}\n", staged.index("static int VSyncInterval(void) {")) + 3
        vsync = staged[start:end]
        helpers = staged.replace(vsync, "").split(seam.HELPERS_ANCHOR)[0]
        for forbidden in ("RtlRunFrame", "g_ram", "g_sram", "g_pad_buttons",
                          "g_input_state", "snes_host_clock", "WriteConfigFile",
                          "g_simulation_hz"):
            self.assertNotIn(forbidden, helpers, forbidden)
        # The swap-interval decision only reads the guest rate; it never
        # changes simulation timing.
        self.assertIn("g_simulation_hz", vsync)
        self.assertNotIn("g_simulation_hz =", vsync)
        self.assertNotIn("snes_host_clock", vsync)

    def test_requires_the_options_seam_and_rejects_a_moved_host(self):
        with self.assertRaisesRegex(ValueError, "options_spike"):
            seam.patch_host_main(HOST_STUB.replace(seam.OPTIONS_MARK, "X"), POLICY)
        for needle in (seam.HELPERS_ANCHOR, seam.DEFAULT_BRANCH, seam.OPTIONS_SDL3,
                       seam.LAUNCHER, seam.HOTKEY, seam.CREATED, seam.TICK_ANCHOR,
                       seam.PRODUCT_KEY, seam.SCALE_STEP, seam.EXIT_SAVE,
                       seam.RENDERER_READY, seam.LAUNCHER_RETURN):
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
            launcher = game / "recomp-ui/src/common/launcher_platform_sdl3.c"
            launcher.parent.mkdir(parents=True)
            launcher_stub = "static bool open(void) {\n" + seam.LAUNCHER_GL + "}\n"
            launcher.write_text(launcher_stub, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "display policy"):
                seam.plan(game, Path(d) / "no-ur-root")
            [(path, before, after), (lpath, lbefore, lafter)] = seam.plan(game, ROOT)
            self.assertEqual((path, before), (host, HOST_STUB))
            self.assertIn(seam.MARK, after)
            self.assertEqual(host.read_text(encoding="utf-8"), HOST_STUB)
            self.assertEqual((lpath, lbefore), (launcher, launcher_stub))
            self.assertEqual(launcher.read_text(encoding="utf-8"), launcher_stub)
            # A context older than GL 3 is torn down and the open fails, so
            # the launcher returns UNAVAILABLE instead of drawing.
            guard = lafter[lafter.index(seam.MARK):]
            self.assertIn('SDL_GL_GetProcAddress("glGetString")', guard)
            self.assertIn("if (major < 3) {", guard)
            self.assertLess(guard.index("SDL_GL_DestroyContext(p->gl);"),
                            guard.index("return false;"))
            self.assertLess(lafter.index(seam.MARK), lafter.index("SDL_GL_SetSwapInterval(1);"))
            self.assertEqual(seam.patch_launcher_platform(lafter), lafter)
            with self.assertRaisesRegex(ValueError, "diverged"):
                seam.patch_launcher_platform("static bool open(void) {}\n")

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
        with self.assertRaisesRegex(ValueError, "menu confirm"):
            runner.verify_log(acceptance_log() +
                              "UR_BALDOSA_MODERN_ROOT stock_requested players=1\n")
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
