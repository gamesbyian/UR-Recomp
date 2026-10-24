#!/usr/bin/env python3
"""A panel slower than the game never slows the game through vsync.

The desktop host presents once per simulated frame and drops simulation it
falls behind on, so waiting for a 50 Hz panel ran the game at 50 fps (83%).
``tools/baldosa_sdl_display_lifecycle_spike.py`` turns the wait off where
``ur_display_vsync_cannot_carry`` says the panel cannot carry the guest.

Three real launches of the exact built game report and quit through the
placement smoke; each must log the decision and the renderer's actual
swap interval must match it:

1. ``SNESRECOMP_UR_DISPLAY_REFRESH_OVERRIDE=50`` (test-only): no wait, vsync 0;
2. ``...=60``: the VSync setting (On, 1) is kept;
3. the machine's own panel: recorded, and the interval must match the logged
   decision.

Fails closed. A hosted runner cannot present to a real 50 Hz panel, so the
speed itself is a physical check (D16).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

DECISION = re.compile(r"^UR_DISPLAY vsync panel_hz=([\d.]+) guest_hz=([\d.]+) wait=(no|setting)$",
                      re.MULTILINE)
RENDERER = re.compile(r"^UR_DISPLAY_VSYNC_SMOKE renderer_vsync=(-?\d+)$", re.MULTILINE)
CONFIG = "[Sound]\nEnableAudio = 0\n\n[Graphics]\nVSync = 1\n"


def launch(exe: Path, rom: Path, root: Path, label: str, video: str, timeout: int,
           refresh: str | None) -> tuple[str, str, int]:
    work = root / label
    (work / "user").mkdir(parents=True)
    (work / "config.ini").write_text(CONFIG, encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(work / "user"),
           "SNESRECOMP_UR_DISPLAY_PLACEMENT_SMOKE": "report",
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    env.pop("SNESRECOMP_UR_DISPLAY_REFRESH_OVERRIDE", None)
    if refresh is not None:
        env["SNESRECOMP_UR_DISPLAY_REFRESH_OVERRIDE"] = refresh
    proc = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(work / "config.ini"), str(rom)],
        cwd=work, env=env, timeout=timeout, text=True, capture_output=True,
        errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (work / "game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"{label}: native game exited {proc.returncode}: {log[-1500:]}")
    decisions = DECISION.findall(log)
    renderer = RENDERER.findall(log)
    # One decision: no display change happens during the run.
    if len(decisions) != 1 or len(renderer) != 1:
        raise ValueError(f"{label}: expected one decision and one report, got "
                         f"{decisions} / {renderer}")
    panel, _, wait = decisions[0]
    return panel, wait, int(renderer[0])


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int) -> dict:
    exe, rom, out = exe.resolve(strict=True), rom.resolve(strict=True), out.resolve()
    if out.exists():
        raise ValueError("output directory must not pre-exist")
    out.mkdir(parents=True)

    panel, wait, vsync = launch(exe, rom, out, "panel-50hz", video, timeout, "50")
    if (panel, wait, vsync) != ("50.000", "no", 0):
        raise ValueError(f"50 Hz panel: panel={panel} wait={wait} renderer_vsync={vsync}")
    panel, wait, vsync = launch(exe, rom, out, "panel-60hz", video, timeout, "60")
    if (panel, wait, vsync) != ("60.000", "setting", 1):
        raise ValueError(f"60 Hz panel: panel={panel} wait={wait} renderer_vsync={vsync}")
    panel, wait, vsync = launch(exe, rom, out, "machine-panel", video, timeout, None)
    if vsync != (0 if wait == "no" else 1):
        raise ValueError(f"machine panel {panel} Hz: wait={wait} but renderer_vsync={vsync}")

    receipt = {
        "panel_50hz": "no_wait",
        "panel_60hz": "vsync_setting_kept",
        "machine_panel_hz": float(panel),
        "machine_panel_wait": wait,
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "swap-interval decision and the renderer's applied interval; "
                 "not a real 50 Hz panel or measured game speed",
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
