#!/usr/bin/env python3
"""Run the staged SDL3 display-lifecycle scenario on a real native game.

Launches the exact built Baldosa executable with
``SNESRECOMP_UR_DISPLAY_LIFECYCLE_ACCEPTANCE=exit`` (see
``tools/baldosa_sdl_display_lifecycle_spike.py``). The scenario drives the
product Options seam and the framework's Alt+Enter command through windowed,
borderless and exclusive fullscreen, then an unreachable-window rescue, and
checks the real SDL window after each step. Fails closed: every transition
step must pass, in order, with exactly one ``result=pass``.

``offscreen_rescue`` is the one step a desktop may decline to set up (some
window managers refuse to move a window off every display). The scenario then
prints ``not_exercised=1``; the receipt records that explicitly and it is
never counted as a pass.

One hosted display, no monitor hot-plug and no physical DPI change: this is
not multi-monitor or hardware display acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

TRANSITION_STEPS = (
    "start_windowed",
    "borderless",
    "borderless_to_exclusive",
    "exclusive_to_borderless",
    "borderless_to_windowed",
    "windowed_to_exclusive",
    "hotkey_leaves_fullscreen",
    "hotkey_enters_borderless",
    "windowed_again",
)
RESCUE_STEP = "offscreen_rescue"
SCALE_STEP = "window_scale_step_persisted"
STEP = re.compile(r"^UR_DISPLAY_ACCEPT step=(\w+) pass=([01]) (.*)$", re.MULTILINE)
NOT_EXERCISED = re.compile(
    r"^UR_DISPLAY_ACCEPT step=offscreen_rescue not_exercised=1", re.MULTILINE)
RESULT = re.compile(
    r"^UR_DISPLAY_LIFECYCLE_ACCEPTANCE result=(\w+) reconciles=(\d+)$", re.MULTILINE)
EXCLUSIVE = re.compile(r"^UR_DISPLAY fullscreen_mode=exclusive display=\d+ mode=(\S+)$",
                       re.MULTILINE)


def verify_log(log: str) -> dict:
    steps = STEP.findall(log)
    names = [name for name, _, _ in steps]
    skipped = len(NOT_EXERCISED.findall(log))
    expected = (list(TRANSITION_STEPS) + ([] if skipped else [RESCUE_STEP]) +
                [SCALE_STEP])
    if skipped > 1 or names != expected:
        raise ValueError(f"display acceptance steps differ: {names} skipped={skipped}")
    failed = [name for name, ok, _ in steps if ok != "1"]
    if failed:
        raise ValueError(f"display acceptance steps failed: {failed}")
    results = RESULT.findall(log)
    if [r for r, _ in results] != ["pass"]:
        raise ValueError(f"display acceptance result is not a single pass: {results}")
    if "UR_BALDOSA_MODERN_ROOT stock_requested" in log:
        raise ValueError("Alt+Enter reached the Modern root as a menu confirm")
    modes = EXCLUSIVE.findall(log)
    if len(modes) < 2:
        raise ValueError("exclusive fullscreen mode was not applied twice")
    return {
        "steps": names,
        "offscreen_rescue": "not_exercised" if skipped else "pass",
        "exclusive_modes": modes,
        "reconciles": int(results[0][1]),
        "rescues": len(re.findall(r"UR_DISPLAY reconcile reason=\w+ action=rescue", log)),
    }


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe = exe.resolve(strict=True)
    rom = rom.resolve(strict=True)
    out = out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    out.mkdir(parents=True)
    user = out / "fresh-test-user"
    user.mkdir()
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(user),
           "SNESRECOMP_UR_DISPLAY_LIFECYCLE_ACCEPTANCE": "exit",
           # The visible Modern root must not take Alt+Enter as CONFIRM.
           "UR_EXECUTION_MODE": "modern",
           "UR_BALDOSA_MODERN_ROOT": "1",
           "UR_BALDOSA_MODERN_INPUT": "1",
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    command = [str(exe), "--no-launcher", "--config", str(config), str(rom)]
    proc = subprocess.run(command, cwd=out, env=env, timeout=timeout,
                          text=True, capture_output=True, errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (out / "native-game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"native game exited {proc.returncode}: {log[-1500:]}")
    receipt = verify_log(log)
    receipt.update({
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "one hosted display through the product Options seam and "
                 "Alt+Enter; not multi-monitor, DPI or hardware acceptance",
    })
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                      encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    receipt = run(args.exe, args.rom, args.out, args.video, args.timeout)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
