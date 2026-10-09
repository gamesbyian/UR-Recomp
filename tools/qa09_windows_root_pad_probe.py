#!/usr/bin/env python3
"""Packaged Win32 Modern root acceptance using the existing SDL virtual P1 pad.

Runs a fresh *human*, non--script game session. The game's established
UR_MAIN_MENU_PAD_ACCEPTANCE harness seats the SDL3 virtual gamepad and pulses
its physical X/B/D-pad/A/B controls through normal framework callbacks.
The probe only supervises and checks independent diagnostic witnesses.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import time

from tools.capture_modern_paused_audio import _stop_entire_tree

REQUIRED_IN_ORDER = (
    "UR_MODERN_ROOT PRESENT",
    "UR_MAIN_MENU_PAD_ACCEPTANCE PRESSED button=x step=0",
    "UR_PROFILE_UI OPENED",
    "UR_MAIN_MENU_PAD_ACCEPTANCE PRESSED button=b step=1",
    "UR_MAIN_MENU_PAD_ACCEPTANCE PRESSED button=down step=2",
    "UR_MAIN_MENU_PAD_ACCEPTANCE PRESSED button=a step=3",
    "UR_PRACTICE_PICKER OPENED",
    "UR_MAIN_MENU_PAD_ACCEPTANCE PRESSED button=b step=4",
    "UR_PRACTICE_PICKER CANCELLED",
)


def verify_root_log(contents: str) -> None:
    previous = -1
    for marker in REQUIRED_IN_ORDER:
        position = contents.find(marker, previous + 1)
        if position == -1:
            raise ValueError(f"missing or out-of-order Modern root event: {marker}")
        previous = position
    if "UR_PRACTICE STARTED" in contents:
        raise ValueError("cancelled picker incorrectly launched Practice")
    if "UR_MODERN_ROOT STOCK_ENTRY_UNEXPECTED_MENU" in contents:
        raise ValueError("Modern root unexpectedly transferred into stock guest menu")
    if "UR_MAIN_MENU_PAD_ACCEPTANCE SEAT_TIMEOUT" in contents:
        raise ValueError("virtual pad did not become seated as P1")
    if "UR_FRONTEND_HOLD ENGAGED" not in contents:
        raise ValueError("Modern root never froze the guest main-menu attract timer")


def probe(launcher: Path, log: Path, *, timeout_seconds: int = 100) -> None:
    if os.name != "nt":
        raise RuntimeError("Win32 package acceptance must run on native Windows")
    if not launcher.is_file():
        raise FileNotFoundError(launcher)
    log.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.update({
        "SDL_VIDEODRIVER": "windows",
        "SDL_AUDIODRIVER": "dummy",
        "UR_EXECUTION_MODE": "modern",
        "UR_PRODUCT_DIAGNOSTICS": "1",
        "UR_MAIN_MENU_PAD_ACCEPTANCE": "x,b,down,a,b",
    })
    quote = lambda p: str(p).replace("'", "''")
    command = f"& '{quote(launcher)}'; exit $LASTEXITCODE"
    with log.open("wb") as output:
        process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            env=environment,
            stdout=output, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        try:
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                contents = log.read_text(encoding="utf-8", errors="replace")
                if REQUIRED_IN_ORDER[-1] in contents:
                    verify_root_log(contents)
                    if process.poll() is not None:
                        raise RuntimeError("packaged game exited during root journey")
                    print("UR_WINDOWS_QA09_PAD_ROOT=passed")
                    return
                if process.poll() is not None:
                    raise RuntimeError(
                        "packaged game exited before root journey finished: " +
                        contents[-1500:])
                time.sleep(0.15)
            contents = log.read_text(encoding="utf-8", errors="replace")
            verify_root_log(contents)
            raise TimeoutError("packaged Modern root journey exceeded deadline")
        finally:
            _stop_entire_tree(process)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("launcher", type=Path)
    parser.add_argument("log", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=100)
    args = parser.parse_args()
    if not 15 <= args.timeout_seconds <= 120:
        parser.error("timeout must be between 15 and 120 seconds")
    probe(args.launcher, args.log, timeout_seconds=args.timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
