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

A second launch repeats the scenario with a test-only desktop refresh of
144 Hz. Exclusive FULLSCREEN must then ask for an even refresh (a whole
multiple of the guest rate) at the desktop resolution when the display offers
one; with none on offer that check is recorded ``not_exercised``.

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
REFRESH = re.compile(
    r"^UR_DISPLAY exclusive_refresh choice=(even|desktop) desktop_hz=([\d.]+) "
    r"guest_hz=([\d.]+) chosen_hz=([\d.]+) candidates=(\d+)$", re.MULTILINE)
FORCED_DESKTOP_HZ = "144"


def refresh_even(hz: float, guest_hz: float) -> bool:
    """Mirror of ur_display_refresh_even."""
    return hz > 0 and guest_hz > 0 and any(
        guest_hz * k * 0.99 <= hz <= guest_hz * k * 1.01 for k in range(1, 9))


def verify_refresh(log: str, forced: bool) -> str:
    """Every exclusive mode states its refresh choice; under a juddering
    (forced 144 Hz) desktop, an even refresh must be chosen when offered."""
    choices = REFRESH.findall(log)
    if len(choices) != len(EXCLUSIVE.findall(log)):
        raise ValueError(f"exclusive modes without a refresh choice: {choices}")
    outcome = "desktop"
    for choice, desktop, guest, chosen, _ in choices:
        desktop_hz, guest_hz, chosen_hz = float(desktop), float(guest), float(chosen)
        if forced and desktop != f"{float(FORCED_DESKTOP_HZ):.3f}":
            raise ValueError(f"forced desktop refresh not used: {desktop}")
        if refresh_even(desktop_hz, guest_hz) and choice != "desktop":
            raise ValueError(f"an even desktop refresh was replaced: {choices}")
        if choice == "even":
            if not refresh_even(chosen_hz, guest_hz):
                raise ValueError(f"chosen refresh {chosen_hz} is not even for {guest_hz}")
            outcome = "even"
        elif forced:
            outcome = "not_exercised"
    return outcome


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
    verify_refresh(log, forced=False)
    return {
        "steps": names,
        "offscreen_rescue": "not_exercised" if skipped else "pass",
        "exclusive_modes": modes,
        "reconciles": int(results[0][1]),
        "rescues": len(re.findall(r"UR_DISPLAY reconcile reason=\w+ action=rescue", log)),
    }


def launch(exe: Path, rom: Path, out: Path, video: str, timeout: int,
           extra_env: dict | None = None) -> str:
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
           "SDL_AUDIODRIVER": "dummy",
           **(extra_env or {})}
    command = [str(exe), "--no-launcher", "--config", str(config), str(rom)]
    proc = subprocess.run(command, cwd=out, env=env, timeout=timeout,
                          text=True, capture_output=True, errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (out / "native-game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"native game exited {proc.returncode}: {log[-1500:]}")
    return log


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe = exe.resolve(strict=True)
    rom = rom.resolve(strict=True)
    out = out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    receipt = verify_log(launch(exe, rom, out, video, timeout))
    forced_log = launch(exe, rom, out / "forced-144hz-desktop", video, timeout,
                        {"SNESRECOMP_UR_DISPLAY_DESKTOP_HZ_OVERRIDE": FORCED_DESKTOP_HZ})
    verify_log(forced_log)
    receipt["juddering_desktop_refresh"] = verify_refresh(forced_log, forced=True)
    receipt["forced_exclusive_modes"] = EXCLUSIVE.findall(forced_log)
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
