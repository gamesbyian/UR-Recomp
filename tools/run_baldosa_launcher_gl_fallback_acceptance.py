#!/usr/bin/env python3
"""The in-game launcher never takes the game down when OpenGL is too old.

Two real launches of the exact built game open the in-game launcher through
the placement smoke's ``launcher`` mode (see
``tools/baldosa_sdl_display_lifecycle_spike.py``), and the game must report
and quit normally afterwards:

1. ``SNESRECOMP_UR_LAUNCHER_GL_VERSION=1.1.0`` (test override) stands in for
   the GDI 1.1 context Windows hands back without a GL driver: the launcher
   must log ``UR_LAUNCHER_GL unusable`` and return UNAVAILABLE (action 2);
2. the machine's own GL: the launcher is either refused the same way or
   opens and closes itself (``LNG_SMOKE_FRAMES``). On a GPU-less hosted
   Windows runner this is the path that crashed (#2272).

Fails closed: a crash, a missing report or a forced run that still opened
the launcher all fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

REPORT = re.compile(r"^UR_DISPLAY_PLACEMENT_SMOKE mode=launcher ", re.MULTILINE)
REFUSED = re.compile(r"UR_LAUNCHER_GL unusable version=(.*)$", re.MULTILINE)
ACTION = re.compile(r"in-game launcher: action=(\d+)")
UNAVAILABLE = "2"
# Audio on (dummy driver) and both players on pads, so committing the
# launcher's settings is not a change that restarts the process.
CONFIG = "[Sound]\nEnableAudio = 1\n\n[Controller]\nSourceP1 = 2\nSourceP2 = 2\n"


def launch(exe: Path, rom: Path, root: Path, label: str, video: str, timeout: int,
           extra: dict) -> str:
    work = root / label
    (work / "user").mkdir(parents=True)
    (work / "config.ini").write_text(CONFIG, encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(work / "user"),
           "SNESRECOMP_UR_DISPLAY_PLACEMENT_SMOKE": "launcher",
           "LNG_SMOKE_FRAMES": "20",
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy", **extra}
    proc = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(work / "config.ini"), str(rom)],
        cwd=work, env=env, timeout=timeout, text=True, capture_output=True,
        errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (work / "game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"{label}: native game exited {proc.returncode}: {log[-1500:]}")
    if len(REPORT.findall(log)) != 1:
        raise ValueError(f"{label}: the game did not carry on after the launcher")
    actions = ACTION.findall(log)
    if len(actions) != 1:
        raise ValueError(f"{label}: expected one in-game launcher return, got {actions}")
    return log


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe, rom, out = exe.resolve(strict=True), rom.resolve(strict=True), out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    out.mkdir(parents=True)

    forced = launch(exe, rom, out, "forced-gl-1.1", video, timeout,
                    {"SNESRECOMP_UR_LAUNCHER_GL_VERSION": "1.1.0"})
    if REFUSED.findall(forced) != ["1.1.0"] or ACTION.findall(forced) != [UNAVAILABLE]:
        raise ValueError("a 1.1 context was not refused as UNAVAILABLE")

    native = launch(exe, rom, out, "machine-gl", video, timeout, {})
    refused = REFUSED.findall(native)
    action = ACTION.findall(native)[0]
    if refused and action != UNAVAILABLE:
        raise ValueError(f"launcher refused GL {refused} but returned action {action}")

    receipt = {
        "forced_gl_1_1": "refused_unavailable",
        "machine_gl": f"refused version={refused[0].strip()}" if refused
                      else f"opened action={action}",
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "the game survives opening the in-game launcher; not a GPU "
                 "driver or remote-desktop acceptance",
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    print(json.dumps(run(args.exe, args.rom, args.out, args.video, args.timeout), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
