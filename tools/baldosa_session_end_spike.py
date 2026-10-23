#!/usr/bin/env python3
"""Stage session-end persistence into the pinned Baldosa host (Windows).

The pinned SNESRecomp host keeps everything only at its ordinary exit: the
cartridge SRAM (with the Modern profile checkpoint around it), the autosave
slot, ``config.ini`` key changes and ``window-placement.txt``. Two ordinary
ways of ending the game never reach that exit on Windows:

* **closing the console window** that ``run-uniracers.cmd`` runs the game in.
  The console delivers ``CTRL_CLOSE_EVENT``; with no handler the default one
  calls ``ExitProcess`` at once (Ctrl+C and Ctrl+Break likewise);
* **shutting down, restarting or signing out** with the game open (including
  a Windows Update restart). SDL3 does not handle ``WM_QUERYENDSESSION`` /
  ``WM_ENDSESSION``; once ``WM_ENDSESSION`` returns the process can be
  terminated at any moment.

Either way every bit of progress since launch was lost. This disposable
checkout patch:

* moves the exit-time persistence block, unchanged, into
  ``UrPersistAtExit``, which runs at most once and is still called from the
  same place in the ordinary exit;
* installs a console control handler. Close, Ctrl+C, Ctrl+Break, log-off and
  shutdown become the host's ordinary ``SDL_QUIT``; the handler then waits
  (bounded, inside the system's five-second allowance) until the main loop
  has run ``UrPersistAtExit``, so a closing console cannot terminate the
  process half way;
* creates a hidden top-level window on the main thread. Windows sends it the
  session messages during SDL's own event pump, between frames.
  ``WM_QUERYENDSESSION`` registers a shutdown-block reason and allows the
  session to end; ``WM_ENDSESSION`` runs ``UrPersistAtExit`` synchronously
  before returning, then asks the loop to quit;
* ``SNESRECOMP_UR_SESSION_END_SMOKE=1`` prints one
  ``UR_SESSION_END ready`` line naming that window once the game is running,
  for ``tools/run_baldosa_session_end_acceptance.py``. ``=close_thread``
  also does what the system does for a console close where a hosted session
  cannot deliver one: call the handler with ``CTRL_CLOSE_EVENT`` on a new
  thread and terminate the process the moment it returns. Inert unless set.

Guest code, input, timing and the content of what is persisted are
untouched. Windows only; every other build is unchanged. Must run after
``baldosa_sdl_display_lifecycle_spike.py``. Guarded, atomic and idempotent.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_SESSION_END"
DISPLAY_MARK = "UR_BALDOSA_SDL_DISPLAY_LIFECYCLE"

# The exit-time persistence block, from the autosave slot to the end of the
# native SRAM save. Its content is moved verbatim.
PERSIST_START = (
    "  if (g_config.autosave && !g_netplay_session)\n"
    "    HandleCommand(kKeys_Save + 0, true);\n"
)
PERSIST_END = (
    "#if defined(SNES_HAS_LOBBY_CLIENT)\n"
    "  /* Reopen the launcher from a clean process."
)
PERSIST_CALL = "  UrPersistAtExit(NULL);  /* " + MARK + ": at most once */\n"
# Everything the block must still contain, so a moved host fails closed.
PERSIST_REQUIRED = (
    "UrSaveWindowPlacement();",
    "WriteConfigFile(g_active_config_file);",
    "ur_baldosa_modern_profile_before_native_save() == 1",
    "int native_saved = RtlWriteSram();",
    "ur_baldosa_modern_profile_finish_native_save(native_saved);",
)

MAIN_ANCHOR = (
    "int snesrecomp_desktop_main(const SnesDesktopHostGame *game, int argc, char **argv) {\n"
)
HELPERS_ANCHOR = "static bool HandleDeviceEvent(const SDL_Event *event) {\n"
TICK_ANCHOR = "    UrDisplayLifecycleAcceptanceTick();  /* " + DISPLAY_MARK + " */\n"
TICK_NEW = TICK_ANCHOR + "    UrSessionEndTick();  /* " + MARK + " */\n"

HELPERS = r'''/* UR_BALDOSA_SESSION_END: the exit-time saves also run when Windows ends
 * the session or the console window closes; see UrPersistAtExit. */
static void UrPersistAtExit(const char *reason);
#if defined(_WIN32) && SNESRECOMP_SDL3
/* Why the loop was asked to quit by Windows, or NULL; set before SDL_QUIT
 * is pushed and read by the main thread after it. */
static const char *volatile g_ur_quit_cause;
static HANDLE g_ur_persisted_event;
static HWND g_ur_session_window;
static void UrSessionEndQuit(const char *cause) {
  if (!g_ur_quit_cause) g_ur_quit_cause = cause;
  SDL_Event quit;
  memset(&quit, 0, sizeof(quit));
  quit.type = SDL_QUIT;
  SDL_PushEvent(&quit);
}
/* Runs on a thread the system creates. The process ends when this returns
 * for close, log-off and shutdown, so wait for the main loop's save (the
 * system allows five seconds; keep inside it). Ctrl+C and Ctrl+Break only
 * ask the game to quit, as closing its window does. */
static BOOL WINAPI UrConsoleControl(DWORD type) {
  const char *cause = type == CTRL_CLOSE_EVENT ? "console_close"
      : type == CTRL_LOGOFF_EVENT ? "console_logoff"
      : type == CTRL_SHUTDOWN_EVENT ? "console_shutdown"
      : type == CTRL_BREAK_EVENT ? "console_break" : "console_ctrl_c";
  printf("UR_SESSION_END console_event=%s\n", cause);
  fflush(stdout);
  UrSessionEndQuit(cause);
  if (type == CTRL_CLOSE_EVENT || type == CTRL_LOGOFF_EVENT || type == CTRL_SHUTDOWN_EVENT) {
    if (g_ur_persisted_event) WaitForSingleObject(g_ur_persisted_event, 4500);
  }
  return TRUE;
}
static HWND UrSessionGameHwnd(void) {
  return g_window ? (HWND)SDL_GetPointerProperty(SDL_GetWindowProperties(g_window),
                                                 SDL_PROP_WINDOW_WIN32_HWND_POINTER, NULL)
                  : NULL;
}
/* Sent by Windows while SDL pumps events on this (the main) thread, so the
 * guest is between frames, exactly as at the ordinary exit. */
static LRESULT CALLBACK UrSessionWindowProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
  if (msg == WM_QUERYENDSESSION) {
    HWND game = UrSessionGameHwnd();
    if (game) ShutdownBlockReasonCreate(game, L"Saving Uniracers progress");
    printf("UR_SESSION_END query_end_session flags=0x%lx\n", (unsigned long)lp);
    fflush(stdout);
    return TRUE;
  }
  if (msg == WM_ENDSESSION) {
    HWND game = UrSessionGameHwnd();
    printf("UR_SESSION_END end_session ending=%d flags=0x%lx\n", wp ? 1 : 0,
           (unsigned long)lp);
    fflush(stdout);
    if (wp) {
      /* Once this returns the process may be terminated at any moment. */
      UrPersistAtExit("session_end");
      UrSessionEndQuit("session_end");
    }
    if (game) ShutdownBlockReasonDestroy(game);
    return 0;
  }
  return DefWindowProcW(hwnd, msg, wp, lp);
}
static void UrSessionEndInstall(void) {
  g_ur_persisted_event = CreateEventW(NULL, TRUE, FALSE, NULL);
  if (!SetConsoleCtrlHandler(UrConsoleControl, TRUE))
    printf("UR_SESSION_END console_handler=0 error=%lu\n", (unsigned long)GetLastError());
  WNDCLASSW wc;
  memset(&wc, 0, sizeof(wc));
  wc.lpfnWndProc = UrSessionWindowProc;
  wc.hInstance = GetModuleHandleW(NULL);
  wc.lpszClassName = L"UrSessionEndWindow";
  RegisterClassW(&wc);
  /* Top-level (message-only windows get no session messages), never shown. */
  g_ur_session_window = CreateWindowExW(0, wc.lpszClassName, L"Uniracers session",
                                        WS_OVERLAPPED, 0, 0, 0, 0, NULL, NULL,
                                        wc.hInstance, NULL);
  printf("UR_SESSION_END installed console_handler=1 window=%d\n",
         g_ur_session_window ? 1 : 0);
  fflush(stdout);
}
static void UrSessionEndPersisted(void) {
  if (g_ur_persisted_event) SetEvent(g_ur_persisted_event);
}
static const char *UrSessionEndCause(void) { return g_ur_quit_cause; }
/* Test only: the system's part of a console close, for a session whose
 * console host cannot deliver one. The handler runs on a new thread and the
 * process ends the moment it returns (STATUS_CONTROL_C_EXIT). */
static DWORD WINAPI UrSessionEndSmokeClose(LPVOID unused) {
  (void)unused;
  UrConsoleControl(CTRL_CLOSE_EVENT);
  TerminateProcess(GetCurrentProcess(), 0xC000013Au);
  return 0;
}
/* Installed on the first main-loop pass. The smoke line tells the runner the
 * game is live and which window to send the session messages to. */
static void UrSessionEndTick(void) {
  static int installed, ticks;
  if (!installed) {
    installed = 1;
    UrSessionEndInstall();
  }
  if (ticks >= 0 && ++ticks == 90) {
    ticks = -1;
    const char *v = HostGetenv("UR_SESSION_END_SMOKE");
    const int close_thread = v && strcmp(v, "close_thread") == 0;
    if (v && (atoi(v) || close_thread)) {
      printf("UR_SESSION_END ready pid=%lu window=%llu\n", (unsigned long)GetCurrentProcessId(),
             (unsigned long long)(uintptr_t)g_ur_session_window);
      fflush(stdout);
    }
    if (close_thread) {
      HANDLE t = CreateThread(NULL, 0, UrSessionEndSmokeClose, NULL, 0, NULL);
      if (t) CloseHandle(t);
    }
  }
}
#else
static void UrSessionEndPersisted(void) {}
static const char *UrSessionEndCause(void) { return NULL; }
static void UrSessionEndTick(void) {}
#endif
'''


def persist_function(block: str) -> str:
    return (
        "/* " + MARK + ": everything the host keeps at exit, exactly once: from\n"
        " * the ordinary exit, or earlier from WM_ENDSESSION. The body is the\n"
        " * pinned host's own exit-time block, unchanged. */\n"
        "static void UrPersistAtExit(const char *reason) {\n"
        "  static int persisted;\n"
        "  if (!reason) reason = UrSessionEndCause() ? UrSessionEndCause() : \"exit\";\n"
        "  if (persisted) {\n"
        "    printf(\"UR_SESSION_END persist reason=%s already=1\\n\", reason);\n"
        "    fflush(stdout);\n"
        "    return;\n"
        "  }\n"
        "  persisted = 1;\n"
        + block +
        "  printf(\"UR_SESSION_END persisted reason=%s\\n\", reason);\n"
        "  fflush(stdout);\n"
        "  UrSessionEndPersisted();\n"
        "}\n"
    )


def once(source: str, needle: str, replacement: str) -> str:
    if source.count(needle) != 1:
        raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    return source.replace(needle, replacement, 1)


def patch_host_main(source: str) -> str:
    if MARK in source:
        return source
    if DISPLAY_MARK not in source:
        raise ValueError("baldosa_sdl_display_lifecycle_spike.py must be staged first")
    for needle in (PERSIST_START, PERSIST_END, MAIN_ANCHOR, HELPERS_ANCHOR, TICK_ANCHOR):
        if source.count(needle) != 1:
            raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    start = source.index(PERSIST_START)
    end = source.index(PERSIST_END)
    main = source.index(MAIN_ANCHOR)
    if not main < start < end:
        raise ValueError("Pinned native Baldosa host diverged: exit block outside the host main")
    block = source[start:end]
    missing = [needle for needle in PERSIST_REQUIRED if needle not in block]
    if missing:
        raise ValueError(f"Pinned native Baldosa host diverged: exit block lacks {missing}")
    if "return" in block or "goto" in block:
        raise ValueError("Pinned native Baldosa host diverged: exit block leaves the host main")
    source = source[:start] + PERSIST_CALL + source[end:]
    source = once(source, MAIN_ANCHOR, persist_function(block) + MAIN_ANCHOR)
    source = once(source, HELPERS_ANCHOR, HELPERS + HELPERS_ANCHOR)
    return once(source, TICK_ANCHOR, TICK_NEW)


def plan(game: Path):
    path = game / "snesrecomp/runner/src/desktop/host_main.c"
    before = path.read_text(encoding="utf-8")
    return [(path, before, patch_host_main(before))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    args = parser.parse_args()
    for path, before, after in plan(args.game.resolve()):
        if before != after:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if before == after else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
