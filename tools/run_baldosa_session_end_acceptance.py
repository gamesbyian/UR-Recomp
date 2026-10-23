#!/usr/bin/env python3
"""Progress survives Windows ending the session or the console closing.

Three real launches of the exact built game (see
``tools/baldosa_session_end_spike.py``), each in a fresh directory, each
with ``SNESRECOMP_UR_SESSION_END_SMOKE=1`` so the game reports when it is
live and which hidden window receives the session messages:

1. ``session_end``: the runner sends that window the real
   ``WM_QUERYENDSESSION`` then ``WM_ENDSESSION`` (as Windows does at sign-out,
   shutdown or an update restart) and **terminates the process the moment
   ``WM_ENDSESSION`` returns**, as Windows may. The SRAM file and
   ``window-placement.txt`` must already be on disk;
2. ``console_break``: Ctrl+Break delivered to the game's console group must
   quit through the ordinary exit, saves included, with exit code 0;
3. ``console_close``: the game runs in its own console, as under
   ``run-uniracers.cmd``; a helper attached to that console posts ``WM_CLOSE``
   to its window (``CTRL_CLOSE_EVENT``, after which the system ends the
   process). The saves must be on disk. A console host that never delivers
   the event (the game logs no ``console_event`` within 15 s) is recorded as
   ``not_exercised`` with the window's class; a delivered close that does
   not save fails;
4. ``console_close_simulated``: the system's part of a close done in the
   game (test-only ``close_thread``): the handler runs on a new thread and
   the process is terminated the moment it returns. The saves must be on
   disk and the exit status must be that termination's.

Fails closed. Hosted Windows cannot sign out or shut down the runner; a real
shutdown with the game open is physical check S1
(``docs/WINDOWS-HOST-LIFECYCLE-PHYSICAL-CHECKS.md``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

READY = re.compile(r"^UR_SESSION_END ready pid=(\d+) window=(\d+)\s*$", re.MULTILINE)
PERSISTED = re.compile(r"^UR_SESSION_END persisted reason=(\w+)\s*$", re.MULTILINE)
CONSOLE_EVENT = re.compile(r"^UR_SESSION_END console_event=(\w+)\s*$", re.MULTILINE)
END_SESSION = re.compile(r"^UR_SESSION_END end_session ending=([01]) ", re.MULTILINE)
INSTALLED = re.compile(r"^UR_SESSION_END installed console_handler=1 window=1\s*$", re.MULTILINE)

WM_CLOSE, WM_QUERYENDSESSION, WM_ENDSESSION = 0x0010, 0x0011, 0x0016
ENDSESSION_LOGOFF = 0x80000000
SMTO_BLOCK, SMTO_ABORTIFHUNG = 0x0001, 0x0002
CREATE_NEW_CONSOLE, CREATE_NEW_PROCESS_GROUP = 0x00000010, 0x00000200
STATUS_CONTROL_C_EXIT = 0xC000013A
CLOSE_DELIVERY_SECONDS = 15

# Runs in its own process: attaching to the game's console makes this helper
# a target of the same close event, so it reports before acting.
HELPER = r'''
import ctypes, sys
k = ctypes.WinDLL("kernel32", use_last_error=True)
u = ctypes.WinDLL("user32", use_last_error=True)
action, pid, report = sys.argv[1], int(sys.argv[2]), sys.argv[3]
k.FreeConsole()
if not k.AttachConsole(pid):
    open(report, "w").write(f"attach_failed {ctypes.get_last_error()}\n"); sys.exit(2)
if action == "break":
    ok = k.GenerateConsoleCtrlEvent(1, pid)
    open(report, "w").write(f"break sent={int(bool(ok))} error={ctypes.get_last_error()}\n")
    sys.exit(0 if ok else 3)
k.GetConsoleWindow.restype = ctypes.c_void_p
hwnd = k.GetConsoleWindow()
if not hwnd:
    open(report, "w").write("no_console_window\n"); sys.exit(4)
name = ctypes.create_unicode_buffer(256)
u.GetClassNameW(ctypes.c_void_p(hwnd), name, 256)
open(report, "w").write(f"close posted hwnd={hwnd} class={name.value}\n")
u.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)
'''


def one(pattern: re.Pattern, log: str, what: str):
    found = pattern.findall(log)
    if len(found) != 1:
        raise ValueError(f"{what}: expected exactly one match, got {found}")
    return found[0]


def saves_on_disk(root: Path) -> dict:
    srm = sorted(p for p in root.rglob("*.srm") if p.is_file())
    placement = root / "window-placement.txt"
    return {"srm": [str(p.relative_to(root)) for p in srm],
            "placement": placement.is_file()}


def verify(scenario: str, log: str, saves: dict, returncode: int | None) -> dict:
    """Pure check of one scenario's log, files and exit status.
    ``console_close_simulated`` is checked as ``console_close`` plus the
    exit status of the termination that follows the handler."""
    if scenario == "console_close_simulated":
        # Terminated once the handler returned, or the main thread finished its
        # own exit first; without the handler's wait the saves would be absent.
        if returncode is None or returncode & 0xFFFFFFFF not in (STATUS_CONTROL_C_EXIT, 0):
            raise ValueError(f"console_close_simulated: exit {returncode}, not the "
                             "termination after the handler returned")
        return verify("console_close", log, saves, returncode)
    if not INSTALLED.search(log):
        raise ValueError(f"{scenario}: session-end handling was not installed")
    persisted = PERSISTED.findall(log)
    if scenario == "session_end":
        if one(END_SESSION, log, "end_session") != "1":
            raise ValueError("session_end: WM_ENDSESSION was not an ending session")
        if persisted != ["session_end"]:
            raise ValueError(f"session_end: persisted {persisted} before termination")
    else:
        cause = one(CONSOLE_EVENT, log, f"{scenario} console event")
        if cause != scenario:
            raise ValueError(f"{scenario}: console event was {cause}")
        if persisted != [scenario]:
            raise ValueError(f"{scenario}: persisted {persisted}")
        if scenario == "console_break" and returncode != 0:
            raise ValueError(f"console_break: exited {returncode}, not through the ordinary exit")
    if not saves["srm"]:
        raise ValueError(f"{scenario}: no SRAM file on disk")
    if not saves["placement"]:
        raise ValueError(f"{scenario}: no window-placement.txt on disk")
    return {"persisted": persisted[0], "srm": saves["srm"], "returncode": returncode}


def wait_ready(proc: subprocess.Popen, log_path: Path, timeout: int) -> tuple[int, int]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        match = READY.search(text)
        if match:
            return int(match.group(1)), int(match.group(2))
        if proc.poll() is not None:
            raise ValueError(f"game exited {proc.returncode} before it was ready: {text[-1200:]}")
        time.sleep(0.2)
    raise ValueError("game never reported ready")


def launch(exe: Path, rom: Path, root: Path, video: str, flags: int, smoke: str = "1"):
    root.mkdir(parents=True)
    (root / "user").mkdir()
    (root / "config.ini").write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(root / "user"),
           "SNESRECOMP_UR_SESSION_END_SMOKE": smoke,
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    log_path = root / "game.log"
    log = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(exe), "--no-launcher", "--config", str(root / "config.ini"), str(rom)],
        cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
    return proc, log, log_path


def send(hwnd: int, msg: int, wparam: int, lparam: int, timeout_ms: int) -> int:
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SendMessageTimeoutW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
    user32.SendMessageTimeoutW.restype = ctypes.c_size_t
    result = ctypes.c_size_t(0)
    if not user32.SendMessageTimeoutW(hwnd, msg, wparam, lparam,
                                      SMTO_BLOCK | SMTO_ABORTIFHUNG, timeout_ms,
                                      ctypes.byref(result)):
        raise ValueError(f"SendMessageTimeout({msg:#x}) failed: {ctypes.get_last_error()}")
    return result.value


def scenario_session_end(exe, rom, root, video, timeout) -> dict:
    proc, log, log_path = launch(exe, rom, root, video, 0)
    try:
        _, hwnd = wait_ready(proc, log_path, timeout)
        if send(hwnd, WM_QUERYENDSESSION, 0, ENDSESSION_LOGOFF, 10000) != 1:
            raise ValueError("WM_QUERYENDSESSION did not allow the session to end")
        send(hwnd, WM_ENDSESSION, 1, ENDSESSION_LOGOFF, 20000)
        # Windows may end the process the moment WM_ENDSESSION returns.
        proc.kill()
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
        log.close()
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return verify("session_end", text, saves_on_disk(root), None)


def scenario_console(exe, rom, root, video, timeout, action: str) -> dict:
    flags = CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP
    proc, log, log_path = launch(exe, rom, root, video, flags)
    report = root / "helper.txt"
    try:
        pid, _ = wait_ready(proc, log_path, timeout)
        subprocess.run([sys.executable, "-I", "-c", HELPER, action, str(pid), str(report)],
                       timeout=30)
        note = report.read_text(encoding="utf-8").strip() if report.exists() else "no report"
        if action == "close" and note == "no_console_window":
            proc.kill()
            proc.wait(timeout=30)
            return {"not_exercised": note}
        if not note.startswith("close posted" if action == "close" else "break sent=1"):
            raise ValueError(f"console {action} not delivered: {note}")
        if action == "close" and not wait_for(log_path, CONSOLE_EVENT, CLOSE_DELIVERY_SECONDS):
            # The console host never raised CTRL_CLOSE_EVENT in this session.
            proc.kill()
            proc.wait(timeout=30)
            return {"not_exercised": f"console host did not deliver the close ({note})"}
        try:
            returncode = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-1500:]
            raise ValueError(f"console {action}: game still running ({note}): {tail}")
    finally:
        if proc.poll() is None:
            proc.kill()
        log.close()
    text = log_path.read_text(encoding="utf-8", errors="replace")
    name = "console_close" if action == "close" else "console_break"
    return verify(name, text, saves_on_disk(root), returncode)


def wait_for(log_path: Path, pattern: re.Pattern, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if pattern.search(log_path.read_text(encoding="utf-8", errors="replace")):
            return True
        time.sleep(0.2)
    return False


def scenario_close_simulated(exe, rom, root, video, timeout) -> dict:
    proc, log, log_path = launch(exe, rom, root, video, 0, smoke="close_thread")
    try:
        wait_ready(proc, log_path, timeout)
        try:
            returncode = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-1500:]
            raise ValueError(f"console_close_simulated: game still running: {tail}")
    finally:
        if proc.poll() is None:
            proc.kill()
        log.close()
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return verify("console_close_simulated", text, saves_on_disk(root), returncode)


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe, rom, out = exe.resolve(strict=True), rom.resolve(strict=True), out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    receipt = {
        "session_end": scenario_session_end(exe, rom, out / "session-end", video, timeout),
        "console_break": scenario_console(exe, rom, out / "console-break", video, timeout,
                                          "break"),
        "console_close": scenario_console(exe, rom, out / "console-close", video, timeout,
                                          "close"),
        "console_close_simulated": scenario_close_simulated(
            exe, rom, out / "console-close-simulated", video, timeout),
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "real session messages and console events sent to one hosted "
                 "process; not a real sign-out or shutdown",
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    print(json.dumps(run(args.exe, args.rom, args.out, args.video, args.timeout), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
