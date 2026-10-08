#!/usr/bin/env python3
"""Probe real Windows Modern pause -> Resume audio through the packaged game.

Uses the existing host pause-open acceptance and sends Escape through the
native Win32 window-message path, without touching guest/APU state. Measures
the SDL3 device stream before and after real product-host Resume.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import time

from tools.capture_modern_paused_audio import (
    PAUSE_OPEN, _stop_entire_tree, verify_modern_pause_log,
)
from tools.analyze_sdl_disk_audio import parse_disk_format

RESUMED = re.compile(r"(?m)^UR_PAUSE_STATE paused=0 surface=(\d+)\s*$")
FRAME_BYTES = 4


def verify_resume_log(log: str) -> dict:
    opened_at = log.find(PAUSE_OPEN)
    if opened_at < 0:
        raise ValueError("Modern host never opened pause")
    original = verify_modern_pause_log(log[:opened_at + len(PAUSE_OPEN)])
    following = log[opened_at + len(PAUSE_OPEN):]
    if PAUSE_OPEN in following:
        raise ValueError("duplicate Modern host pause-open marker")
    matches = RESUMED.findall(following)
    if len(matches) != 1 or int(matches[0]) != original["host_pause_surface"]:
        raise ValueError("missing, duplicate or wrong-surface host Resume acknowledgement")
    if re.search(r"(?m)^UR_PAUSE_STATE paused=1\b", following):
        raise ValueError("host re-entered pause during Resume audio capture")
    if "UR_PAUSE_QUIT REQUESTED" in following:
        raise ValueError("desktop quit interfered with Resume capture")
    return {
        "guest_race_entered_frame": original["guest_race_entered_frame"],
        "host_pause_surface": original["host_pause_surface"],
        "pause_open_count": 1,
        "resume_count": 1,
    }


def read_stereo_window(pcm: Path, end_bytes: int, *, rate: int = 44100) -> dict:
    if (not isinstance(end_bytes, int) or end_bytes % FRAME_BYTES
        or end_bytes < FRAME_BYTES * rate):
        raise ValueError("SDL PCM boundary lacks a complete one-second stereo window")
    with pcm.open("rb") as inp:
        inp.seek(0, 2)
        if inp.tell() < end_bytes:
            raise ValueError("SDL PCM device output was truncated")
        inp.seek(end_bytes - FRAME_BYTES * rate)
        raw = inp.read(FRAME_BYTES * rate)
    if len(raw) != FRAME_BYTES * rate:
        raise ValueError("short SDL stereo window")
    sums = [0, 0]
    nonzero = [0, 0]
    for left, right in struct.iter_unpack("<hh", raw):
        for channel, sample in enumerate((left, right)):
            sums[channel] += sample * sample
            nonzero[channel] += int(sample != 0)
    return {
        "channel_rms": [round(math.sqrt(x / rate), 6) for x in sums],
        "combined_rms": round(math.sqrt(sum(sums) / (2 * rate)), 6),
        "channel_nonzero_fraction": [round(n / rate, 8) for n in nonzero],
        "frames": rate,
    }


def verify_resume_audio(log: str, paused: dict, resumed: dict) -> dict:
    evidence = verify_resume_log(log)
    if (paused.get("frames") != 44100 or resumed.get("frames") != 44100
        or paused.get("combined_rms") != 0
        or paused.get("channel_rms") != [0.0, 0.0]
        or paused.get("channel_nonzero_fraction") != [0.0, 0.0]):
        raise ValueError("Modern host pause was not literally silent before Resume")
    levels = resumed.get("channel_rms")
    fractions = resumed.get("channel_nonzero_fraction")
    if (not isinstance(levels, list) or not isinstance(fractions, list)
        or len(levels) != 2 or len(fractions) != 2
        or any(not isinstance(x, (int, float)) or isinstance(x, bool)
                   or not math.isfinite(x) for x in levels + fractions)
        or min(levels) < 50 or min(fractions) < 0.001
        or any(x > 1 or x < 0 for x in fractions)
        or not isinstance(resumed.get("combined_rms"), (int, float))
        or not math.isfinite(resumed["combined_rms"])
        or resumed["combined_rms"] < 50):
        raise ValueError("real Modern Resume failed to restore audible stereo SDL output")
    return {
        "schema_version": 1,
        "authority": "real Windows product host-owned pause and Win32 Escape Resume",
        "device_origin": "sdl3-disk-playback",
        "device_rate": 44100,
        **evidence,
        "paused_one_second": paused,
        "resumed_final_one_second": resumed,
        "limits": "device PCM windows, not sample/guest-aligned; no click or speaker latency certification",
    }


def _find_game_window(root_pid: int) -> int:
    # Launcher is PowerShell -> .cmd -> shipping EXE; never inject other apps.
    command = ("Get-CimInstance Win32_Process | "
               "Select-Object ProcessId,ParentProcessId,Name | ConvertTo-Json -Compress")
    report = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        text=True, timeout=15,
    )
    entries = json.loads(report)
    if isinstance(entries, dict):
        entries = [entries]
    descendants = {root_pid}
    changed = True
    while changed:
        before = len(descendants)
        descendants.update(int(p["ProcessId"]) for p in entries
                           if int(p["ParentProcessId"]) in descendants)
        changed = len(descendants) != before

    # The Windows package contract pins this executable name. Select its PID
    # within *this* launch tree, rather than trusting an arbitrary window title
    # (which can be localized or changed by the framework).
    game_pids = {int(p["ProcessId"]) for p in entries
                 if int(p["ProcessId"]) in descendants
                 and str(p.get("Name", "")).lower() == "uniracerssnesrecomp.exe"}
    if len(game_pids) != 1:
        raise RuntimeError(
            f"expected one packaged Uniracers executable in launch tree; got {len(game_pids)}"
        )
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    candidates = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    # HWND is pointer-sized on Win64. Bare ctypes calls default to 32-bit
    # integers and can silently truncate handles, defeating real input.
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.WCHAR), ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL

    @callback_type
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in game_pids and user32.IsWindowVisible(hwnd):
            # A zero-title helper window is not the primary game window.
            if user32.GetWindowTextLengthW(hwnd) > 0:
                candidates.append(int(hwnd))
        return True

    user32.EnumWindows(visit, 0)
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected exactly one visible Uniracers window in launch tree; got {len(candidates)}"
        )
    return candidates[0]


def _press_resume(hwnd: int) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    # The ordinary SDL Windows event pump interprets Escape, not this tool.
    VK_ESCAPE, WM_KEYDOWN, WM_KEYUP = 0x1B, 0x0100, 0x0101
    down = 1 | (0x01 << 16)
    up = down | (1 << 30) | (1 << 31)
    if not user32.PostMessageW(hwnd, WM_KEYDOWN, VK_ESCAPE, down):
        raise RuntimeError("failed to deliver native Windows Escape keydown")
    time.sleep(0.07)
    if not user32.PostMessageW(hwnd, WM_KEYUP, VK_ESCAPE, up):
        raise RuntimeError("failed to deliver native Windows Escape keyup")


def capture(launcher: Path, script: Path, log: Path, pcm: Path, *,
            deadline_seconds: float = 90, paused_hold_seconds: float = 4,
            resumed_hold_seconds: float = 4) -> dict:
    if os.name != "nt":
        raise RuntimeError("Modern Resume PCM probe requires native Windows")
    if (not 20 <= deadline_seconds <= 180 or not 3 <= paused_hold_seconds <= 10
        or not 3 <= resumed_hold_seconds <= 10):
        raise ValueError("invalid bounded Modern Resume capture times")
    if not launcher.is_file() or not script.is_file():
        raise ValueError("missing real packaged Windows launcher or script")
    log.parent.mkdir(parents=True, exist_ok=True)
    literal = lambda path: str(path).replace("'", "''")
    command = f"& '{literal(launcher)}' --script '{literal(script)}'; exit $LASTEXITCODE"
    with log.open("wb") as sink:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            stdout=sink, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        try:
            start = time.monotonic()
            while time.monotonic() - start < deadline_seconds:
                if proc.poll() is not None:
                    raise RuntimeError("packaged Windows game quit before Modern pause")
                current = log.read_text(encoding="utf-8", errors="replace")
                if PAUSE_OPEN in current:
                    verify_modern_pause_log(current)
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("timed out before real Modern pause")
            window = _find_game_window(proc.pid)
            time.sleep(paused_hold_seconds)
            if proc.poll() is not None:
                raise RuntimeError("packaged Windows game quit during held pause")
            capture_format = parse_disk_format(log)
            if (Path(capture_format["destination"]).resolve() != pcm.resolve()
                or capture_format["sample_rate"] != 44100):
                raise ValueError("unexpected SDL3 stereo output path or sample rate")
            paused_bytes = pcm.stat().st_size
            paused = read_stereo_window(pcm, paused_bytes)
            if paused["combined_rms"] != 0:
                raise ValueError("Modern host did not reach literal PCM silence before Resume")
            _press_resume(window)
            started_resume = time.monotonic()
            while time.monotonic() - started_resume < 10:
                if proc.poll() is not None:
                    raise RuntimeError("packaged Windows game quit before Resume acknowledgement")
                current = log.read_text(encoding="utf-8", errors="replace")
                if RESUMED.search(current[current.index(PAUSE_OPEN):]):
                    verify_resume_log(current)
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("timed out waiting for actual host Resume acknowledgement")
            time.sleep(resumed_hold_seconds)
            if proc.poll() is not None:
                raise RuntimeError("packaged Windows game quit during resumed playback")
            end_bytes = pcm.stat().st_size
            resumed = read_stereo_window(pcm, end_bytes)
        finally:
            _stop_entire_tree(proc)
    return verify_resume_audio(
        log.read_text(encoding="utf-8", errors="replace"), paused, resumed
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("windows_launcher", type=Path)
    parser.add_argument("windows_script", type=Path)
    parser.add_argument("capture_log", type=Path)
    parser.add_argument("device_pcm", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    result = capture(
        args.windows_launcher, args.windows_script, args.capture_log, args.device_pcm
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("WINDOWS_MODERN_RESUME_AUDIO PASS paused_digital_silence=1 "
          "resume_both_channels_audible=1 source=packaged_SDL3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
