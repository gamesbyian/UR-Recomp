#!/usr/bin/env python3
"""Capture real packaged Windows Modern Pause->Restart Race stereo output.

Opens the ordinary host-owned pause in a proven original-game 1P race,
then uses the real SDL/Win32 keyboard path (Down then Enter) to activate
Restart. Requires the actual restarted guest to continue advancing.
Only reads SDL disk PCM after the game process releases its Windows lock.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import subprocess
import time

from tools.capture_modern_paused_audio import (
    PAUSE_OPEN, _stop_entire_tree, verify_modern_pause_log,
)
from tools.capture_modern_resume_audio import (
    _find_game_window, read_stereo_window, verify_resume_audio,
)

SELECTED_RESTART = re.compile(
    r"(?m)^UR_PAUSE_SELECTION selected=1 restart=1\s*$")
RESUMED = re.compile(r"(?m)^UR_PAUSE_STATE paused=0 surface=(\d+)\s*$")
GUEST_RESTARTED = re.compile(
    r"(?m)^script f=(\d+) dump audio-restart-guest ok\s*$")
FRAME_BYTES = 4


def verify_restart_log(log: str) -> dict:
    opened = log.find(PAUSE_OPEN)
    if opened < 0:
        raise ValueError("guest never opened the authentic Modern host pause")
    prefix = verify_modern_pause_log(log[:opened + len(PAUSE_OPEN)])
    phases = {
        "selection": SELECTED_RESTART,
        "resume": RESUMED,
        "guest": GUEST_RESTARTED,
    }
    positions = {}
    values = {}
    for name, expression in phases.items():
        matches = list(expression.finditer(log, opened + len(PAUSE_OPEN)))
        if len(matches) != 1:
            raise ValueError(f"missing or duplicate Restart lifecycle marker {name}")
        positions[name] = matches[0].start()
        values[name] = matches[0]
    if not positions["selection"] < positions["resume"] < positions["guest"]:
        raise ValueError("Restart selection, host Resume, and resumed guest out of order")
    if int(values["resume"].group(1)) != prefix["host_pause_surface"]:
        raise ValueError("Restart unpaused a different host surface")
    if int(values["guest"].group(1)) <= 0:
        raise ValueError("restarted guest did not reach valid simulation frame")
    if PAUSE_OPEN in log[opened + len(PAUSE_OPEN):]:
        raise ValueError("duplicate host pause opening")
    if "UR_PAUSE_QUIT REQUESTED" in log:
        raise ValueError("desktop quit contaminated Restart sound capture")
    return {
        "source_race_guest_frame": prefix["guest_race_entered_frame"],
        "restart_guest_resume_frame": int(values["guest"].group(1)),
        "pause_surface": prefix["host_pause_surface"],
        "restart_selected": 1,
        "host_resumed": 1,
        "guest_resumed_after_restart": 1,
    }


def _press_key(hwnd: int, virtual_key: int, scan_code: int,
               *, extended: bool = False) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    base = 1 | (scan_code << 16) | ((1 << 24) if extended else 0)
    if not user32.PostMessageW(hwnd, 0x0100, virtual_key, base):
        raise RuntimeError("failed to send native Win32 keydown to packaged game")
    time.sleep(0.09)
    if not user32.PostMessageW(hwnd, 0x0101, virtual_key,
                               base | (1 << 30) | (1 << 31)):
        raise RuntimeError("failed to send native Win32 keyup to packaged game")


def capture(launcher: Path, script: Path, log: Path, pcm: Path, *,
            deadline_seconds: float = 100,
            paused_hold_seconds: float = 4,
            restarted_hold_seconds: float = 4) -> dict:
    if os.name != "nt":
        raise RuntimeError("audio Restart probe must run on native Windows")
    if (not 30 <= deadline_seconds <= 180 or
        not 3 <= paused_hold_seconds <= 10 or
        not 3 <= restarted_hold_seconds <= 10):
        raise ValueError("invalid bounded Restart audio observation times")
    if not launcher.is_file() or not script.is_file():
        raise ValueError("missing verified Windows package launcher or guest route")
    log.parent.mkdir(parents=True, exist_ok=True)
    quote = lambda path: str(path).replace("'", "''")
    command = f"& '{quote(launcher)}' --script '{quote(script)}'; exit $LASTEXITCODE"
    with log.open("wb") as sink:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            stdout=sink, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        try:
            initial = time.monotonic()
            while time.monotonic() - initial < deadline_seconds:
                if proc.poll() is not None:
                    raise RuntimeError("game exited before real host Pause")
                current = log.read_text(encoding="utf-8", errors="replace")
                if PAUSE_OPEN in current:
                    verify_modern_pause_log(current)
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("timed out waiting for active-race host Pause")

            window = _find_game_window(proc.pid)
            time.sleep(paused_hold_seconds)
            if proc.poll() is not None:
                raise RuntimeError("game exited during frozen pause")
            paused_boundary = pcm.stat().st_size
            if paused_boundary < 44100 * FRAME_BYTES or paused_boundary % FRAME_BYTES:
                raise ValueError("paused device file lacks one aligned S16 stereo window")

            _press_key(window, 0x28, 0x50, extended=True)  # Down -> Restart
            selected_at = time.monotonic()
            while time.monotonic() - selected_at < 7:
                current = log.read_text(encoding="utf-8", errors="replace")
                if SELECTED_RESTART.search(current):
                    break
                if proc.poll() is not None:
                    raise RuntimeError("game exited before Restart was selected")
                time.sleep(0.15)
            else:
                raise RuntimeError("Win32 Down failed to select available Restart")

            _press_key(window, 0x0D, 0x1C)  # Enter activates product Restart
            resumed_at = time.monotonic()
            while time.monotonic() - resumed_at < 20:
                current = log.read_text(encoding="utf-8", errors="replace")
                if RESUMED.search(current) and GUEST_RESTARTED.search(current):
                    verify_restart_log(current)
                    break
                if proc.poll() is not None:
                    raise RuntimeError("game exited before restarted guest resumed")
                time.sleep(0.2)
            else:
                raise RuntimeError("Restart did not restore guest and unpause host")
            time.sleep(restarted_hold_seconds)
            if proc.poll() is not None:
                raise RuntimeError("game exited during restarted race audio")
            resumed_boundary = pcm.stat().st_size
            if (resumed_boundary - paused_boundary < FRAME_BYTES * 44100
                or resumed_boundary % FRAME_BYTES):
                raise ValueError("Restart failed to generate one more second of SDL audio")
        finally:
            _stop_entire_tree(proc)

    # Windows SDL3 disk output remains exclusively locked until game exit.
    paused = read_stereo_window(pcm, paused_boundary)
    resumed = read_stereo_window(pcm, resumed_boundary)
    log_content = log.read_text(encoding="utf-8", errors="replace")
    evidence = verify_restart_log(log_content)
    acoustic = verify_resume_audio(log_content, paused, resumed)
    return {
        "schema_version": 1,
        "authority": "packaged Windows real pause-menu Restart Win32 Down/Enter",
        "device_origin": "sdl3-disk-playback",
        "sample_rate": 44100,
        **evidence,
        "paused_one_second": acoustic["paused_one_second"],
        "restarted_final_one_second": acoustic["resumed_final_one_second"],
        "limits": "device-output recovery and resumed guest; no exact sample parity or click/latency proof",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("windows_launcher", type=Path)
    ap.add_argument("windows_script", type=Path)
    ap.add_argument("capture_log", type=Path)
    ap.add_argument("device_pcm", type=Path)
    ap.add_argument("--json-out", required=True, type=Path)
    a = ap.parse_args()
    evidence = capture(a.windows_launcher, a.windows_script,
                       a.capture_log, a.device_pcm)
    a.json_out.parent.mkdir(parents=True, exist_ok=True)
    a.json_out.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    print("WINDOWS_MODERN_RESTART_AUDIO PASS paused_stereo_silence=1 "
          "restarted_guest=1 resumed_stereo_audible=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
