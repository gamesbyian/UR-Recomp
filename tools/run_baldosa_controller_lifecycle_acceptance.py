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
    "spare_shows_no_player_index",
    "full_no_claim",
    "p1_vacated",
    "p1_reclaimed",
    "reclaimed_pad_shows_its_seat",
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
    "drained_add_unseen",
    "reconcile_seats_new_pad",
    "drained_removal_unseen",
    "reconcile_releases_gone_pad",
    "returning_pad_reclaims_after_reconcile",
    "keyboard_fallback_drives_p1",
    "seated_pad_keeps_p1_exclusive",
    "no_fallback_when_p2_on_keyboard",
    "seat_move_refused_when_target_bad",
    "seat_move_p1_pad_to_p2",
    "moved_pad_drives_p2",
    "moved_pad_shows_p2",
    "moved_pad_reclaims_p2_after_replug",
)
# Second launch: the real in-game launcher drains a hotplug; the seat table
# must catch up when it returns.
LAUNCHER_STEPS = (
    "launcher_pad_seated",
    "launcher_removal_reconciled",
    "launcher_add_reconciled",
)
STEP = re.compile(r"^UR_CONTROLLER_ACCEPT step=(\w+) pass=([01]) ", re.MULTILINE)
RESULT = re.compile(r"^UR_CONTROLLER_LIFECYCLE_ACCEPTANCE result=(\w+)$", re.MULTILINE)


def verify_log(log: str, expected=EXPECTED_STEPS) -> dict:
    steps = STEP.findall(log)
    names = [name for name, _ in steps]
    if names != list(expected):
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


def run(exe: Path, rom: Path, out: Path, video: str, timeout: int,
        real_launcher: bool = False) -> dict:
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
    def launch(mode: str, label: str, extra: dict) -> str:
        env = {**os.environ,
               "SNESRECOMP_USER_DATA_DIR": str(user),
               "SNESRECOMP_UR_CONTROLLER_LIFECYCLE_ACCEPTANCE": mode,
               "SDL_VIDEODRIVER": video,
               "SDL_AUDIODRIVER": "dummy", **extra}
        command = [str(exe), "--no-launcher", "--config", str(config), str(rom)]
        proc = subprocess.run(command, cwd=out, env=env, timeout=timeout,
                              text=True, capture_output=True, errors="replace")
        log = proc.stdout + "\n" + proc.stderr
        (out / f"{label}.log").write_text(log, encoding="utf-8")
        if proc.returncode:
            raise ValueError(f"{label}: native game exited {proc.returncode}: {log[-1500:]}")
        return log

    def finish(receipt: dict) -> dict:
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

    receipt = verify_log(launch("exit", "native-game", {}))
    receipt["real_launcher"] = "not_run"
    if not real_launcher:
        return finish(receipt)
    # The launcher closes itself after ~1.5 s (recomp-ui smoke hook); the
    # scenario's hotplug fires 0.4 s after it opens. Audio stays enabled
    # (dummy driver) so committing the launcher's settings is not an
    # audio change that restarts the process, and both players already use
    # pads, so the commit does not re-seat from scratch (which would clear
    # a stale seat on its own and hide a missing reconcile).
    config.write_text("[Sound]\nEnableAudio = 1\n\n[Controller]\nSourceP1 = 2\nSourceP2 = 2\n",
                      encoding="ascii")
    launcher_log = launch("launcher", "native-game-launcher", {"LNG_SMOKE_FRAMES": "90"})
    receipt["launcher_steps"] = verify_log(launcher_log, LAUNCHER_STEPS)["steps"]
    if len(re.findall(r"UR_CONTROLLER_SEAT reconcile reason=launcher_returned ", launcher_log)) != 2:
        raise ValueError("the in-game launcher return did not reconcile both hotplugs")
    receipt["real_launcher"] = "pass"
    return finish(receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=120)
    # The real in-game launcher needs OpenGL; hosted Windows runners have
    # none (it fails to load GL and crashes), so this second launch is
    # opt-in where a GL context exists.
    parser.add_argument("--real-launcher", action="store_true")
    args = parser.parse_args()
    receipt = run(args.exe, args.rom, args.out, args.video, args.timeout,
                  args.real_launcher)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
