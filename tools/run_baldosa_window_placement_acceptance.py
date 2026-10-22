#!/usr/bin/env python3
"""Window placement survives a relaunch; a missing display falls back.

Three real launches of the exact built game share one config directory
(see the placement code in ``tools/baldosa_sdl_display_lifecycle_spike.py``):

1. ``SNESRECOMP_UR_DISPLAY_PLACEMENT_SMOKE=move:X,Y`` moves the window and
   quits through the ordinary exit, which writes ``window-placement.txt``;
2. ``report`` must open at that position on that display;
3. after renaming the saved display to one that is not connected, ``report``
   must log ``saved_display_missing`` and stay where SDL put it (primary).

Fails closed. One hosted display: moving between real monitors is a physical
check (``docs/WINDOWS-HOST-LIFECYCLE-PHYSICAL-CHECKS.md``), not covered here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

SMOKE = re.compile(
    r"^UR_DISPLAY_PLACEMENT_SMOKE mode=(move|report) window=(-?\d+),(-?\d+) "
    r"fullscreen=([01]) display=(.*?)\s*$", re.MULTILINE)
SAVED = re.compile(r"^UR_DISPLAY placement saved=([01]) display=", re.MULTILINE)
RESTORED = re.compile(r"^UR_DISPLAY placement restored display=", re.MULTILINE)
MISSING = re.compile(r"^UR_DISPLAY placement saved_display_missing name=", re.MULTILINE)
GONE = "UR placement test display that is not connected"


def one(pattern: re.Pattern, log: str, what: str):
    found = pattern.findall(log)
    if len(found) != 1:
        raise ValueError(f"{what}: expected exactly one match, got {found}")
    return found[0]


def launch(exe: Path, rom: Path, root: Path, smoke: str, label: str,
           video: str, timeout: int) -> str:
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(root / "user"),
           "SNESRECOMP_UR_DISPLAY_PLACEMENT_SMOKE": smoke,
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    proc = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(root / "config.ini"), str(rom)],
        cwd=root, env=env, timeout=timeout, text=True, capture_output=True,
        errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (root / f"{label}.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"{label}: native game exited {proc.returncode}: {log[-1200:]}")
    return log


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int,
        launcher=launch) -> dict:
    exe, rom, out = exe.resolve(strict=True), rom.resolve(strict=True), out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    (out / "user").mkdir(parents=True)
    (out / "config.ini").write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    placement = out / "window-placement.txt"

    # A target well inside any desktop large enough to run the game, and
    # off-centre so a restored position cannot be mistaken for the default.
    target = (37, 53)
    moved_log = launcher(exe, rom, out, f"move:{target[0]},{target[1]}", "1-move",
                       video, timeout)
    _, mx, my, mfull, mdisplay = one(SMOKE, moved_log, "move report")
    if one(SAVED, moved_log, "placement save") != "1" or not placement.is_file():
        raise ValueError("placement was not saved at exit")
    saved = placement.read_text(encoding="utf-8")
    if f"window={mx},{my}," not in saved:
        raise ValueError(f"saved windowed position differs from the moved window: {saved!r}")

    report_log = launcher(exe, rom, out, "report", "2-relaunch", video, timeout)
    one(RESTORED, report_log, "placement restore")
    _, rx, ry, rfull, rdisplay = one(SMOKE, report_log, "relaunch report")
    if (rx, ry, rdisplay) != (mx, my, mdisplay):
        raise ValueError(f"relaunch at {rx},{ry} on {rdisplay!r}, saved {mx},{my} on {mdisplay!r}")

    lines = [f"display_name={GONE}" if l.startswith("display_name=") else l
             for l in saved.splitlines()]
    placement.write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing_log = launcher(exe, rom, out, "report", "3-missing-display", video, timeout)
    one(MISSING, missing_log, "missing-display fallback")
    if RESTORED.search(missing_log):
        raise ValueError("a placement for a display that is not connected was applied")
    _, fx, fy, _, fdisplay = one(SMOKE, missing_log, "fallback report")
    if (fx, fy) == (mx, my):
        raise ValueError("fallback launch reused the position of a missing display")

    receipt = {
        "moved_window": [int(mx), int(my)],
        "relaunched_window": [int(rx), int(ry)],
        "display": mdisplay,
        "fallback_window": [int(fx), int(fy)],
        "fallback_display": fdisplay,
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "one hosted display: restore and missing-display fallback; "
                 "not multi-monitor acceptance",
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
