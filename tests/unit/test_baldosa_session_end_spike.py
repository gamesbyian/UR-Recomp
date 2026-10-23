#!/usr/bin/env python3
"""The session-end seam is narrow, guarded and idempotent; its runner fails closed."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import baldosa_session_end_spike as seam
import run_baldosa_session_end_acceptance as runner

EXIT_BLOCK = (
    seam.PERSIST_START +
    "  UrSaveWindowPlacement();  /* UR_BALDOSA_SDL_DISPLAY_LIFECYCLE */\n"
    "  if (g_volume_changed || g_fullscreen_changed)\n"
    "    WriteConfigFile(g_active_config_file);\n"
    "\n"
    "  if (!g_netplay_session) {\n"
    "    if (ur_baldosa_modern_profile_before_native_save() == 1) {\n"
    "      int native_saved = RtlWriteSram();\n"
    "      int finish = ur_baldosa_modern_profile_finish_native_save(native_saved);\n"
    "      if (!finish) exit(8);\n"
    "    } else {\n"
    "      exit(8);\n"
    "    }\n"
    "  }\n"
)

# Every pinned anchor, in host order, with filler between them.
HOST_STUB = "\n".join((
    "/* UR_BALDOSA_SDL_DISPLAY_LIFECYCLE staged */",
    "static void Earlier(void) {}",
    seam.HELPERS_ANCHOR + "  return false;\n}",
    seam.MAIN_ANCHOR + "  while (running) {",
    seam.TICK_ANCHOR + "  }",
    EXIT_BLOCK + seam.PERSIST_END + " */\n#endif\n  return 0;\n}",
))


class BaldosaSessionEndSpikeTests(unittest.TestCase):
    def staged(self) -> str:
        return seam.patch_host_main(HOST_STUB)

    def test_seam_is_idempotent_and_marks_every_site(self):
        staged = self.staged()
        self.assertEqual(seam.patch_host_main(staged), staged)
        self.assertGreaterEqual(staged.count(seam.MARK), 4)

    def test_exit_block_moves_verbatim_and_runs_once(self):
        staged = self.staged()
        fn = staged[staged.index("static void UrPersistAtExit(const char *reason) {"):]
        fn = fn[:fn.index("\n}\n") + 3]
        # The pinned block is inside the function, byte for byte.
        self.assertIn(EXIT_BLOCK, fn)
        # Guarded: the second caller does nothing.
        self.assertLess(fn.index("if (persisted) {"), fn.index(seam.PERSIST_START))
        self.assertLess(fn.index("persisted = 1;"), fn.index(seam.PERSIST_START))
        # The waiting console handler is released only after the save.
        self.assertLess(fn.index("RtlWriteSram()"), fn.index("UrSessionEndPersisted();"))
        # The ordinary exit still calls it from the same place, once.
        main = staged[staged.index(seam.MAIN_ANCHOR):]
        self.assertNotIn("RtlWriteSram()", main)
        self.assertEqual(main.count(seam.PERSIST_CALL), 1)
        self.assertLess(main.index(seam.PERSIST_CALL), main.index(seam.PERSIST_END))
        # Defined before the host main, declared before the helpers use it.
        self.assertLess(staged.index("static void UrPersistAtExit(const char *reason) {"),
                        staged.index(seam.MAIN_ANCHOR))
        self.assertLess(staged.index("static void UrPersistAtExit(const char *reason);"),
                        staged.index('UrPersistAtExit("session_end");'))

    def test_session_end_saves_before_returning(self):
        staged = self.staged()
        proc = staged[staged.index("static LRESULT CALLBACK UrSessionWindowProc("):]
        proc = proc[:proc.index("\n}\n")]
        end = proc[proc.index("if (msg == WM_ENDSESSION) {"):]
        # Only an ending session saves, synchronously, before returning 0.
        self.assertLess(end.index("if (wp) {"), end.index('UrPersistAtExit("session_end");'))
        self.assertLess(end.index('UrPersistAtExit("session_end");'), end.index("return 0;"))
        query = proc[proc.index("if (msg == WM_QUERYENDSESSION) {"):proc.index("if (msg == WM_ENDSESSION)")]
        # The session is never vetoed.
        self.assertIn("return TRUE;", query)
        self.assertIn("ShutdownBlockReasonCreate(", query)
        # Top-level and hidden: message-only windows get no session messages.
        self.assertNotIn("HWND_MESSAGE", staged)
        self.assertIn("WS_OVERLAPPED, 0, 0, 0, 0, NULL, NULL,", staged)

    def test_console_close_waits_for_the_ordinary_exit(self):
        staged = self.staged()
        handler = staged[staged.index("static BOOL WINAPI UrConsoleControl(DWORD type) {"):]
        handler = handler[:handler.index("\n}\n")]
        # The ordinary quit, then a bounded wait inside the five seconds.
        self.assertLess(handler.index("UrSessionEndQuit(cause);"),
                        handler.index("WaitForSingleObject(g_ur_persisted_event, 4500);"))
        self.assertIn("type == CTRL_CLOSE_EVENT || type == CTRL_LOGOFF_EVENT", handler)
        self.assertIn("return TRUE;", handler)
        # The handler never saves on its own thread.
        self.assertNotIn("UrPersistAtExit", handler)
        quit_fn = staged[staged.index("static void UrSessionEndQuit(const char *cause) {"):]
        quit_fn = quit_fn[:quit_fn.index("\n}\n")]
        self.assertLess(quit_fn.index("g_ur_quit_cause = cause;"),
                        quit_fn.index("SDL_PushEvent(&quit);"))

    def test_windows_only_and_inert_smoke(self):
        staged = self.staged()
        helpers = staged[:staged.index(seam.HELPERS_ANCHOR)]
        self.assertIn("#if defined(_WIN32) && SNESRECOMP_SDL3", helpers)
        other = helpers[helpers.index("#else\nstatic void UrSessionEndPersisted(void) {}"):]
        self.assertIn("static void UrSessionEndTick(void) {}", other)
        self.assertIn('HostGetenv("UR_SESSION_END_SMOKE")', helpers)
        for forbidden in ("RtlRunFrame", "g_ram", "g_sram", "keybinds_", "g_pad_buttons"):
            self.assertNotIn(forbidden, seam.HELPERS, forbidden)
        tick = staged[staged.index(seam.TICK_ANCHOR):]
        self.assertTrue(tick.startswith(seam.TICK_NEW))

    def test_a_moved_pinned_host_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "display_lifecycle_spike"):
            seam.patch_host_main(HOST_STUB.replace(seam.DISPLAY_MARK, "X"))
        for needle in (seam.PERSIST_START, seam.PERSIST_END, seam.MAIN_ANCHOR,
                       seam.HELPERS_ANCHOR, seam.TICK_ANCHOR):
            with self.assertRaisesRegex(ValueError, "diverged"):
                seam.patch_host_main(HOST_STUB.replace(needle, ""))
        for required in seam.PERSIST_REQUIRED:
            with self.assertRaisesRegex(ValueError, "lacks"):
                seam.patch_host_main(HOST_STUB.replace(required, "/* gone */"))
        with self.assertRaisesRegex(ValueError, "leaves the host main"):
            seam.patch_host_main(HOST_STUB.replace("exit(8);\n    } else",
                                                   "return 8;\n    } else"))
        moved = HOST_STUB.replace(seam.MAIN_ANCHOR, "") + seam.MAIN_ANCHOR + "}\n"
        with self.assertRaisesRegex(ValueError, "outside the host main"):
            seam.patch_host_main(moved)

    def test_plan_never_writes(self):
        with tempfile.TemporaryDirectory() as d:
            host = Path(d) / "snesrecomp/runner/src/desktop/host_main.c"
            host.parent.mkdir(parents=True)
            host.write_text(HOST_STUB, encoding="utf-8")
            [(path, before, after)] = seam.plan(Path(d))
            self.assertEqual((path, before), (host, HOST_STUB))
            self.assertIn(seam.MARK, after)
            self.assertEqual(host.read_text(encoding="utf-8"), HOST_STUB)


def log(*lines: str) -> str:
    return "\n".join(("UR_SESSION_END installed console_handler=1 window=1",
                      "UR_SESSION_END ready pid=7 window=1234") + lines) + "\n"


SAVED = {"srm": ["saves/save.srm"], "placement": True}


class SessionEndRunnerTests(unittest.TestCase):
    def test_session_end_needs_the_save_before_termination(self):
        good = log("UR_SESSION_END query_end_session flags=0x80000000",
                   "UR_SESSION_END end_session ending=1 flags=0x80000000",
                   "UR_SESSION_END persisted reason=session_end")
        self.assertEqual(runner.verify("session_end", good, SAVED, None)["persisted"],
                         "session_end")
        for bad, files, why in (
                (good.replace("persisted reason=session_end", "x"), SAVED, "persisted"),
                (good.replace("ending=1", "ending=0"), SAVED, "not an ending"),
                (good, {"srm": [], "placement": True}, "SRAM"),
                (good, {"srm": ["save.srm"], "placement": False}, "placement"),
                (good.replace("installed console_handler=1", "installed console_handler=0"),
                 SAVED, "not installed")):
            with self.assertRaisesRegex(ValueError, why):
                runner.verify("session_end", bad, files, None)

    def test_console_events_must_name_their_cause_and_save(self):
        close = log("UR_SESSION_END console_event=console_close",
                    "UR_SESSION_END persisted reason=console_close")
        self.assertEqual(runner.verify("console_close", close, SAVED, -1073741510)["persisted"],
                         "console_close")
        brk = close.replace("console_close", "console_break")
        self.assertEqual(runner.verify("console_break", brk, SAVED, 0)["returncode"], 0)
        with self.assertRaisesRegex(ValueError, "ordinary exit"):
            runner.verify("console_break", brk, SAVED, 3)
        with self.assertRaisesRegex(ValueError, "console event was"):
            runner.verify("console_close", brk, SAVED, 0)
        with self.assertRaisesRegex(ValueError, "persisted"):
            runner.verify("console_close", close.replace("persisted reason=console_close",
                                                         "persisted reason=exit"), SAVED, 0)
        twice = close + "UR_SESSION_END persisted reason=console_close\n"
        with self.assertRaisesRegex(ValueError, "persisted"):
            runner.verify("console_close", twice, SAVED, 0)

    def test_simulated_close_needs_the_termination_status(self):
        close = log("UR_SESSION_END console_event=console_close",
                    "UR_SESSION_END persisted reason=console_close")
        ok = runner.verify("console_close_simulated", close, SAVED, 0xC000013A)
        self.assertEqual(ok["persisted"], "console_close")
        # Python on Windows may report the NTSTATUS as a negative int.
        runner.verify("console_close_simulated", close, SAVED, 0xC000013A - (1 << 32))
        runner.verify("console_close_simulated", close, SAVED, 0)
        for code in (1, 3, None):
            with self.assertRaisesRegex(ValueError, "termination"):
                runner.verify("console_close_simulated", close, SAVED, code)
        with self.assertRaisesRegex(ValueError, "SRAM"):
            runner.verify("console_close_simulated", close,
                          {"srm": [], "placement": True}, 0xC000013A)

    def test_close_thread_smoke_terminates_only_after_the_handler(self):
        staged = BaldosaSessionEndSpikeTests().staged()
        smoke = staged[staged.index("static DWORD WINAPI UrSessionEndSmokeClose("):]
        smoke = smoke[:smoke.index("\n}\n")]
        self.assertLess(smoke.index("UrConsoleControl(CTRL_CLOSE_EVENT);"),
                        smoke.index("TerminateProcess(GetCurrentProcess(), 0xC000013Au);"))
        tick = staged[staged.index("static void UrSessionEndTick(void) {"):]
        tick = tick[:tick.index("\n}\n")]
        self.assertIn('strcmp(v, "close_thread") == 0', tick)

    def test_ready_line_names_pid_and_window(self):
        m = runner.READY.search(log())
        self.assertEqual((m.group(1), m.group(2)), ("7", "1234"))


if __name__ == "__main__":
    unittest.main()
