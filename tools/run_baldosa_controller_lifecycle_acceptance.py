#!/usr/bin/env python3
"""Run the staged SDL3 controller-lifecycle scenario on a real native game.

Launches the exact built Baldosa executable with
``SNESRECOMP_UR_CONTROLLER_LIFECYCLE_ACCEPTANCE=exit`` (see
``tools/baldosa_sdl_controller_lifecycle_spike.py``). SDL virtual gamepads are
attached, re-plugged and pressed through the host's ordinary event loop; the
seat table is checked after each step. Fails closed: every expected step must
appear exactly once with ``pass=1`` and the final result must be ``pass``.

Virtual SDL devices exercise the host's seat/hotplug logic, not physical
controllers, drivers or XInput slot behaviour. This is not hardware acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

EXPECTED_STEPS = (
    "two_pads_seated",
    "no_steal",
    "full_no_claim",
    "p1_vacated",
    "p1_reclaimed",
    "spare_claimed_p2",
    "held_released_on_remove",
    "replacement_takes_absent_seat",
    "returning_players_not_swapped",
    "spare_unseated",
    "spare_closed_on_remove",
    "raw_spare_kept",
    "raw_spare_reopen_not_duplicated",
    "raw_spare_claimed_p2",
    "raw_seat_released_on_remove",
)
STEP = re.compile(r"^UR_CONTROLLER_ACCEPT step=(\w+) pass=([01]) ", re.MULTILINE)
RESULT = re.compile(r"^UR_CONTROLLER_LIFECYCLE_ACCEPTANCE result=(\w+)$", re.MULTILINE)


def verify_log(log: str) -> dict:
    steps = STEP.findall(log)
    names = [name for name, _ in steps]
    if names != list(EXPECTED_STEPS):
        raise ValueError(f"controller acceptance steps differ: {names}")
    failed = [name for name, ok in steps if ok != "1"]
    if failed:
        raise ValueError(f"controller acceptance steps failed: {failed}")
    results = RESULT.findall(log)
    if results != ["pass"]:
        raise ValueError(f"controller acceptance result is not a single pass: {results}")
    return {
        "steps": names,
        "seat_assignments": len(re.findall(r"UR_CONTROLLER_SEAT assign ", log)),
        "seat_claims": len(re.findall(r"UR_CONTROLLER_SEAT claim ", log)),
        "seat_vacates": len(re.findall(r"UR_CONTROLLER_SEAT vacate ", log)),
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
           "SNESRECOMP_UR_CONTROLLER_LIFECYCLE_ACCEPTANCE": "exit",
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
        "scope": "SDL virtual gamepads through the native host event loop; "
                 "not physical controller acceptance",
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
