#!/usr/bin/env python3
"""Bounded Windows SDL3 capture after the *Modern host-owned* pause opens.

The canonical guest script intentionally stops advancing when this pause
freezes the guest. Wait for native product diagnostics in real wall time,
hold the already-running SDL device for several seconds, then terminate
the entire launched process tree. This is NOT a test of stock guest Start.
No artificial guest frames, keys or audio bytes are injected.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PAUSE_OPEN = "UR_PAUSE_ACCEPTANCE OPENED"
PAUSED = re.compile(r"(?m)^UR_PAUSE_STATE paused=1 surface=(\d+)\s*$")
RACE = re.compile(r"(?m)^script f=(\d+) dump race-entered ok\s*$")


def verify_modern_pause_log(text: str) -> dict:
    if text.count(PAUSE_OPEN) != 1:
        raise ValueError("expected exactly one Modern host-owned pause-open event")
    matches = PAUSED.findall(text)
    if len(matches) != 1:
        raise ValueError("missing or ambiguous Modern paused=1 product state")
    races = RACE.findall(text)
    if len(races) != 1 or int(races[0]) <= 0:
        raise ValueError("missing or ambiguous canonical active-race checkpoint")
    race_offset = text.index("dump race-entered ok")
    state_offset = text.index("UR_PAUSE_STATE paused=1")
    opened_offset = text.index(PAUSE_OPEN)
    if not race_offset < state_offset < opened_offset:
        raise ValueError("guest-race, host-paused and opened events out of order")
    if re.search(r"(?m)^UR_PAUSE_STATE paused=0\b", text[opened_offset:]):
        raise ValueError("Modern host pause unexpectedly resumed during held capture")
    if "UR_PAUSE_QUIT REQUESTED" in text[opened_offset:]:
        raise ValueError("Modern host pause unexpectedly requested exit during hold")
    return {
        "guest_race_entered_frame": int(races[0]),
        "host_pause_state": 1,
        "host_pause_surface": int(matches[0]),
        "event": PAUSE_OPEN,
    }


def _stop_entire_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=15, check=False,
        )
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass
    if proc.poll() is None:
        try:
            proc.kill()
        except (ProcessLookupError, PermissionError):
            # On Windows a process can terminate between poll and kill.
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("failed to stop native paused Windows process") from error


def capture(
    launcher: Path, script: Path, log: Path, *,
    deadline_seconds: float = 80.0, hold_seconds: float = 4.0,
) -> dict:
    if (not 20 <= deadline_seconds <= 120
        or not 2 <= hold_seconds <= 10
        or hold_seconds >= deadline_seconds):
        raise ValueError("invalid bounded host pause capture timing")
    if os.name != "nt":
        raise RuntimeError("Modern pause SDL capture requires native Windows")
    if not launcher.is_file() or not script.is_file():
        raise ValueError("missing real Windows launcher or canonical guest script")
    log.parent.mkdir(parents=True, exist_ok=True)
    literal = lambda path: str(path).replace("'", "''")
    shell_command = (
        f"& '{literal(launcher)}' --script '{literal(script)}'; "
        "exit $LASTEXITCODE"
    )
    started = time.monotonic()
    observed = None
    log_text = ""
    with log.open("wb") as sink:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", shell_command],
            stdout=sink, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        try:
            while time.monotonic() - started < deadline_seconds:
                if proc.poll() is not None:
                    raise RuntimeError("native Windows game exited before Modern host pause")
                log_text = log.read_text(encoding="utf-8", errors="replace")
                if PAUSE_OPEN in log_text:
                    observed = verify_modern_pause_log(log_text)
                    break
                time.sleep(0.2)
            if observed is None:
                raise RuntimeError("timed out before Modern host pause opened")
            # Host presentation/event pumping continues while guest simulation
            # is frozen. This pause interval is wall-clock-only, intentionally.
            until = time.monotonic() + hold_seconds
            while time.monotonic() < until:
                if proc.poll() is not None:
                    raise RuntimeError("native Windows game exited while Modern host paused")
                time.sleep(0.2)
        finally:
            _stop_entire_tree(proc)

    final = verify_modern_pause_log(log.read_text(encoding="utf-8", errors="replace"))
    print(
        "WINDOWS_MODERN_HOST_PAUSE_CAPTURE PASS "
        f"race_entered_frame={final['guest_race_entered_frame']} "
        f"surface={final['host_pause_surface']} "
        f"post_open_held_seconds={hold_seconds:.1f} "
        "termination=intentional_process_tree_stop"
    )
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("windows_launcher", type=Path)
    parser.add_argument("windows_script", type=Path)
    parser.add_argument("capture_log", type=Path)
    parser.add_argument("--deadline-seconds", type=float, default=80.0)
    parser.add_argument("--hold-seconds", type=float, default=4.0)
    args = parser.parse_args()
    capture(args.windows_launcher, args.windows_script, args.capture_log,
            deadline_seconds=args.deadline_seconds, hold_seconds=args.hold_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
