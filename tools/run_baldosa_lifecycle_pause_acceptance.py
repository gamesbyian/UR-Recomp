#!/usr/bin/env python3
"""Run the focus-loss / controller-disconnect pause smoke on a real native game.

Launches the exact built Baldosa executable in Modern mode on the pinned
two-player race route with ``UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE=<mode>`` (see
``tools/baldosa_native_pause_lifecycle.cpp``):

* ``disconnect``: an SDL virtual gamepad is hot-plugged during the live race,
  seated by the host, then unplugged;
* ``focus``: the real game window is minimized.

Either must pause through the ordinary Modern session at the next completed
frame with the matching reason, keep guest WRAM frozen while paused, then
resume and advance. Fails closed. ``focus`` may report ``not_exercised`` when
the desktop never gave the window keyboard focus; that is recorded, never
counted as a pass, and accepted only with ``--allow-not-exercised``.

Virtual devices and a scripted minimize are not physical-controller,
alt-tab or hardware acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

REASON = {"disconnect": "controller_disconnect", "focus": "focus_loss"}
SMOKE = re.compile(
    r"^UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE mode=(\w+) result=(\w+) detail=(\w+) "
    r"race_frames=(\d+) paused_ticks=(\d+) frames_after_resume=(\d+)\s*$",
    re.MULTILINE)
PAUSE = re.compile(
    r"^UR_BALDOSA_LIFECYCLE_PAUSE reason=(\w+) seat=(\d+) applied=([01]) notice=(.*?)\s*$",
    re.MULTILINE)


def verify_log(log: str, mode: str, allow_not_exercised: bool = False) -> dict:
    smokes = SMOKE.findall(log)
    if len(smokes) != 1 or smokes[0][0] != mode:
        raise ValueError(f"expected one {mode} smoke result, got {smokes}")
    _, result, detail, race_frames, ticks, after = smokes[0]
    pauses = PAUSE.findall(log)
    if result == "not_exercised":
        if mode != "focus" or not allow_not_exercised:
            raise ValueError(f"{mode} lifecycle pause was not exercised: {detail}")
        if pauses:
            raise ValueError("a lifecycle pause fired although the smoke was not exercised")
        return {"mode": mode, "result": "not_exercised", "detail": detail}
    if result != "pass":
        raise ValueError(f"{mode} lifecycle pause smoke failed: {detail}")
    if len(pauses) != 1:
        raise ValueError(f"expected exactly one lifecycle pause, got {pauses}")
    reason, seat, applied, notice = pauses[0]
    if reason != REASON[mode] or applied != "1":
        raise ValueError(f"wrong lifecycle pause: {pauses[0]}")
    if mode == "disconnect" and (seat not in ("1", "2") or
                                 notice != f"P{seat} CONTROLLER DISCONNECTED"):
        raise ValueError(f"disconnect pause did not name its seat: {pauses[0]}")
    if int(ticks) < 40 or int(after) < 10:
        raise ValueError("pause was not held frozen and then resumed")
    return {"mode": mode, "result": "pass", "reason": reason, "seat": int(seat),
            "notice": notice, "race_frames": int(race_frames),
            "paused_ticks": int(ticks), "frames_after_resume": int(after)}


def run(exe: Path, rom: Path, script: Path, out: Path, mode: str, video: str,
        timeout: int, allow_not_exercised: bool) -> dict:
    exe = exe.resolve(strict=True)
    rom = rom.resolve(strict=True)
    script = script.resolve(strict=True)
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
           "UR_EXECUTION_MODE": "modern",
           "UR_BALDOSA_MODERN_INPUT": "1",
           "UR_BALDOSA_LIFECYCLE_PAUSE_SMOKE": mode,
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(script), str(rom)]
    proc = subprocess.run(command, cwd=out, env=env, timeout=timeout,
                          text=True, capture_output=True, errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (out / "native-game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"native game exited {proc.returncode}: {log[-1500:]}")
    receipt = verify_log(log, mode, allow_not_exercised)
    receipt.update({
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "video_driver": video,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "scope": "SDL virtual gamepad / scripted minimize on the live native "
                 "race; not physical controller, alt-tab or hardware acceptance",
    })
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                      encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=sorted(REASON), required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=200)
    parser.add_argument("--allow-not-exercised", action="store_true")
    args = parser.parse_args()
    receipt = run(args.exe, args.rom, args.script, args.out, args.mode,
                  args.video, args.timeout, args.allow_not_exercised)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
