#!/usr/bin/env python3
"""Focus-loss / disconnect pause in the integrated Baldosa product."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_baldosa_lifecycle_pause_acceptance as runner

LIFECYCLE = ROOT / "tools" / "baldosa_native_pause_lifecycle.cpp"


def body(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


def smoke_log(mode: str, *, result="pass", detail="paused_frozen_resumed",
              reason=None, seat=1, notice=None, ticks=40, after=10,
              pause=True) -> str:
    reason = reason or runner.REASON[mode]
    if notice is None:
        notice = f"P{seat} CONTROLLER DISCONNECTED" if mode == "disconnect" else "-"
    lines = []
    if pause:
        lines.append(f"UR_BALDOSA_LIFECYCLE_PAUSE reason={reason} seat={seat} "
                     f"applied=1 notice={notice}")
    lines.append(f"UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE mode={mode} result={result} "
                 f"detail={detail} race_frames=31 paused_ticks={ticks} "
                 f"frames_after_resume={after}")
    return "\n".join(lines) + "\n"


class BaldosaHostLifecyclePauseTests(unittest.TestCase):
    def test_native_policy_contract(self):
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d) / "lifecycle-pause-test"
            subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(ROOT / "native" / "product"),
                 str(ROOT / "tests" / "native" / "baldosa_host_lifecycle_pause_test.cpp"),
                 "-o", str(exe)],
                check=True)
            subprocess.run([str(exe)], check=True)

    def test_pause_is_decided_at_the_completed_frame_boundary(self):
        source = LIFECYCLE.read_text(encoding="utf-8")
        frame = body(source, 'extern "C" void ur_baldosa_product_after_run_frame(',
                     "\n}\n")
        observe = frame.index("ur_modern_session_observe_race_active(")
        self.assertLess(observe, frame.index("apply_host_lifecycle_pause();"))

    def test_pause_uses_the_ordinary_session_command_only(self):
        source = LIFECYCLE.read_text(encoding="utf-8")
        glue = body(source, "void apply_host_lifecycle_pause() {", "\n}\n")
        self.assertIn("ur_modern_session_pause(g_modern_session)", glue)
        self.assertIn("reset_native_pause_menu_on_open();", glue)
        self.assertIn("in.pause_surface = g_modern_session && g_native_live_race;", glue)
        # Authentic is never Modern, so the shared policies never pause it.
        self.assertIn("physical_modern_enabled() ? ur::product::ExecutionMode::Modern", glue)
        self.assertIn("snesrecomp_desktop_product_seat_source(seat)", glue)
        # Scripted automation has no player to resume a focus pause.
        self.assertIn("!snesrecomp_desktop_product_input_scripted()", glue)
        for forbidden in ("g_ram[", "g_sram", "keybinds_", "RtlRunFrame",
                          "snesrecomp_desktop_product_set_paused"):
            self.assertNotIn(forbidden, glue, forbidden)

    def test_smoke_is_inert_unless_requested(self):
        source = LIFECYCLE.read_text(encoding="utf-8")
        self.assertIn('std::getenv("UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE")', source)
        self.assertIn("if (!lifecycle_smoke_mode() || g_lps_stage == 5) return;", source)
        self.assertIn("if (!lifecycle_smoke_mode() || g_lps_stage != 3) return;", source)
        tick = body(source, 'extern "C" void ur_baldosa_product_host_tick(void) {', "\n}\n")
        self.assertTrue(tick.split("\n", 2)[1].strip() == "lifecycle_pause_smoke_tick();")

    def test_runner_accepts_only_the_matching_pause(self):
        for mode in ("disconnect", "focus"):
            self.assertEqual(runner.verify_log(smoke_log(mode), mode)["result"], "pass")
        with self.assertRaisesRegex(ValueError, "failed"):
            runner.verify_log(smoke_log("disconnect", result="fail",
                                        detail="no_pause_within_60_frames",
                                        pause=False), "disconnect")
        with self.assertRaisesRegex(ValueError, "wrong"):
            runner.verify_log(smoke_log("focus", reason="controller_disconnect"), "focus")
        with self.assertRaisesRegex(ValueError, "name its seat"):
            runner.verify_log(smoke_log("disconnect", notice="-"), "disconnect")
        with self.assertRaisesRegex(ValueError, "frozen"):
            runner.verify_log(smoke_log("focus", ticks=3), "focus")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            runner.verify_log(smoke_log("focus") + smoke_log("focus").splitlines()[0] + "\n",
                              "focus")
        with self.assertRaisesRegex(ValueError, "expected one"):
            runner.verify_log(smoke_log("focus"), "disconnect")

    def test_not_exercised_focus_is_explicit_and_opt_in(self):
        log = smoke_log("focus", result="not_exercised",
                        detail="window_never_focused", pause=False)
        with self.assertRaisesRegex(ValueError, "not exercised"):
            runner.verify_log(log, "focus")
        self.assertEqual(runner.verify_log(log, "focus", True)["result"], "not_exercised")
        # Disconnect never has a not-exercised escape hatch.
        dlog = smoke_log("disconnect", result="not_exercised", detail="x", pause=False)
        with self.assertRaisesRegex(ValueError, "not exercised"):
            runner.verify_log(dlog, "disconnect", True)


if __name__ == "__main__":
    unittest.main()
