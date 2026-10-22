#!/usr/bin/env python3
"""After a render device reset the game keeps drawing.

SDL3's D3D11 renderer frees every texture's GPU data when the device is
lost (driver update, GPU timeout, hybrid-GPU monitor switch), recovers the
device and sends ``SDL_EVENT_RENDER_DEVICE_RESET``. The host kept locking its
old frame texture, which then fails every frame ("Texture is not currently
available"): a black window for the rest of the run.

One real launch of the exact built game delivers that event through the
placement smoke's ``render_reset`` mode (see
``tools/baldosa_sdl_display_lifecycle_spike.py``) and runs 60 more frames.
It must log the reset, rebuild the frame texture exactly once, never fail a
texture lock, and report and quit normally. Hosted CI cannot remove a real
GPU device, so this checks the host's response to SDL's event, not a
driver-level device loss.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

RESET = re.compile(r"^UR_DISPLAY render_device_reset$", re.MULTILINE)
RECREATED = re.compile(r"^UR_DISPLAY render_device_reset texture_recreated=(\d+)x(\d+)$",
                       re.MULTILINE)
REPORT = re.compile(r"^UR_DISPLAY_PLACEMENT_SMOKE mode=render_reset ", re.MULTILINE)
LOCK_FAILED = "Failed to lock texture"


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe, rom, out = exe.resolve(strict=True), rom.resolve(strict=True), out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    (out / "user").mkdir(parents=True)
    (out / "config.ini").write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(out / "user"),
           "SNESRECOMP_UR_DISPLAY_PLACEMENT_SMOKE": "render_reset",
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    proc = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(out / "config.ini"), str(rom)],
        cwd=out, env=env, timeout=timeout, text=True, capture_output=True,
        errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (out / "game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"native game exited {proc.returncode}: {log[-1500:]}")
    if len(RESET.findall(log)) != 1:
        raise ValueError("the render device reset was not observed exactly once")
    recreated = RECREATED.findall(log)
    if len(recreated) != 1:
        raise ValueError(f"frame texture rebuilt {len(recreated)} times, expected once")
    if LOCK_FAILED in log:
        raise ValueError("a texture lock failed after the reset")
    if len(REPORT.findall(log)) != 1:
        raise ValueError("the game did not keep running after the reset")
    receipt = {
        "render_device_reset": "texture_recreated",
        "texture": f"{recreated[0][0]}x{recreated[0][1]}",
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "the host's response to SDL_EVENT_RENDER_DEVICE_RESET; not a "
                 "driver-level GPU device loss",
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
