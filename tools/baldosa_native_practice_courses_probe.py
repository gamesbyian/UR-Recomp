#!/usr/bin/env python3
"""Actual native Practice breadth: original-menu entry of many courses.

Each case is a fresh real native process. The production P1 gamepad handler
opens Practice (DOWN, A), walks the picker with genuine DPAD DOWN edges over
exactly the courses the ORIGINAL game's TOUR_SELECT offers that rider, and
confirms with A. The shared route then drives the unchanged original rider,
tour, track and NOW PLAYING menus; only the decoded original course identity
authorises the handoff. Practice runs in the isolated scratch SRAM, so the
player's save must be byte-identical afterwards and no run is published.

Two stock progression states are exercised:

* a never-played anonymous save (stock tier 0: Crawler, Shuffler, Walker,
  Hopper = 20 courses), and
* a formatted save with the stock tier-2 unlock bytes (40 ordinary courses;
  secret Hunter stays closed), built from the repository's pinned clean
  cartridge image.

Semantic pad edges, not physical-controller acceptance; no release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
from pathlib import Path

from baldosa_windows_native_pause_route import USA_SHA256, sha256

ROOT = Path(__file__).resolve().parents[1]
CLEAN_SRAM = (ROOT / "reference/imported/reverse-engineering/dessyreqt/SRAM/"
              "Clean.srm")
STAY = "turbo on\nwait 5000\nquit\n"

# (label, seed, picker ordinal steps, zero-based track, name, original course)
TIER0 = (
    ("dragster", 0, 0, "DRAGSTER"),
    ("bowl_stunt", 2, 2, "BOWL"),
    ("jumps_stunt", 7, 12, "JUMPS"),
    ("short_cut_circuit", 14, 24, "SHORT CUT"),
    ("east_race", 18, 33, "EAST"),
)
TIER2 = (
    ("wobble_jumper", 5, 5, "WOBBLE"),
    ("last_one_bounder", 15, 15, "LAST ONE"),
    ("down_up_runner", 25, 25, "DOWN+UP"),
    ("vertical_sprinter", 35, 35, "VERTICAL"),
    ("123_jump_last_ordinary", 39, 39, "123 JUMP"),
)


def tier2_seed() -> bytes:
    """Clean formatted cartridge, a valid selected rider and stock tier-2
    bytes. Mirrors what the stock game itself writes after silver medals."""
    data = bytearray(CLEAN_SRAM.read_bytes())
    if len(data) != 8192 or bytes(data[:12]) != b"ASJIver3.30\xff":
        raise ValueError("Pinned clean SRAM image is not the stock format")
    data[0x748] = 0
    for tour in range(8):
        data[0x69C + tour * 16] = 2
    for rider in range(16):
        data[0x10D3 + rider] = 2
        data[0x10FD + rider] = 2
    words = struct.unpack_from("<170H", data, 0x5E8)
    struct.pack_into("<H", data, 0x73C, sum(words) & 0xFFFF)
    return bytes(data)


def run_native(exe: Path, rom: Path, user: Path, work: Path, steps: int,
               video: str, timeout: int, extra_env: dict | None = None) -> str:
    work.mkdir(parents=True, exist_ok=False)
    route = work / "stock-route.txt"
    route.write_text(STAY, encoding="ascii")
    ini = work / "config.ini"
    ini.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = {**os.environ, "SNESRECOMP_USER_DATA_DIR": str(user),
           "UR_EXECUTION_MODE": "modern", "UR_BALDOSA_MODERN_ROOT": "1",
           "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "11",
           "UR_BALDOSA_PRACTICE_TEST_STEPS": str(steps),
           "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
           "UR_BALDOSA_MODERN_INPUT": "1", "UR_BALDOSA_PAUSE_SMOKE": "0",
           "SDL_VIDEODRIVER": video, "SDL_AUDIODRIVER": "dummy",
           **(extra_env or {})}
    proc = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(ini),
         "--script", str(route), str(rom)],
        cwd=work, env=env, capture_output=True, text=True,
        errors="replace", timeout=timeout)
    log = proc.stdout + "\n" + proc.stderr
    (work / "log.txt").write_text(log, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"Practice guest exited {proc.returncode}: "
                           + log[-1800:])
    return log


def verify_case(log: str, track: int, name: str, expected_open: int) -> None:
    opened = re.search(r"practice_opened=1 available=(\d+) course=0 ", log)
    if not opened or int(opened.group(1)) != expected_open:
        raise ValueError(f"Picker offered {opened and opened.group(1)} "
                         f"courses, expected {expected_open}")
    requested = (f"UR_BALDOSA_MODERN_ROOT practice_requested=1 "
                 f"course={track} name={name} source_route=stock")
    entered = (f"UR_BALDOSA_MODERN_ROOT practice_entered=1 course={track} "
               f"original_course={track + 1} race=1 source_identity=verified")
    for token in ("practice_sram_sandbox=1 bytes=8192",
                  requested, entered,
                  "practice_sram_restored=1 bytes=8192"):
        if log.count(token) != 1:
            raise ValueError(f"Practice stage missing/duplicated: {token}")
    if not (log.index(requested) < log.index(entered)
            < log.index("practice_sram_restored=1")):
        raise ValueError("Practice stages were out of order")
    for forbidden in ("practice_rejected=", "stock_entered players=",
                      "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
                      "UR_BALDOSA_NATIVE_RESULT observed=1"):
        if forbidden in log:
            raise ValueError("Practice bypassed a source gate: " + forbidden)


# Real native pause + delayed Restart on top of a Practice race: the shared
# Modern pause authority rewinds the guest to the race-start anchor with the
# (isolated) SRAM unchanged, resumes, and Practice still restores the player's
# stock SRAM at shutdown. Reuses the existing physical-pause smoke switches.
RESTART_ENV = {
    "UR_BALDOSA_PAUSE_SMOKE": "1",
    "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1",
    "UR_BALDOSA_DELAYED_RESTART_SMOKE": "1",
    "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "2500",
    "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1",
}


def verify_restart(log: str) -> None:
    for token in (
            "UR_BALDOSA_MODERN_ROOT practice_entered=1 course=0 ",
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=2500 live_race=1 "
            "modern_session=1 physical_sdl=1",
            "UR_BALDOSA_NATIVE_PAUSE RESUMED previous_guest=2500 ",
            "UR_BALDOSA_MODERN_ROOT practice_sram_restored=1 bytes=8192"):
        if log.count(token) != 1:
            raise ValueError("Practice restart stage missing/duplicated: "
                             + token)
    match = re.search(
        r"UR_BALDOSA_NATIVE_RESTART DELAYED anchor_guest=(\d+) "
        r"request_guest=2500 paused=1 sram_equal=1 wram_rewound=1", log)
    if not match or int(match.group(1)) >= 2500:
        raise ValueError("Practice Restart did not rewind to the race anchor "
                         "with unchanged SRAM")
    if log.index("practice_entered=1") > log.index("NATIVE_RESTART DELAYED") or (
            log.index("NATIVE_RESTART DELAYED") >
            log.index("practice_sram_restored=1")):
        raise ValueError("Practice restart stages were out of order")


def run(exe: Path, rom: Path, out: Path, *, timeout: int, video: str) -> dict:
    for path in (exe, rom, CLEAN_SRAM):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing/redirected Practice probe input {path}")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Practice probe requires the pinned USA retail ROM")
    out.mkdir(parents=True, exist_ok=False)
    cases = []
    for group, seed, expected_open, table in (
            ("tier0_never_played", None, 20, TIER0),
            ("tier2_formatted_save", tier2_seed(), 40, TIER2)):
        for label, steps, track, name in table:
            user = out / f"{group}-{label}-user"
            (user / "saves").mkdir(parents=True)
            save = user / "saves" / "save.srm"
            if seed is not None:
                save.write_bytes(seed)
            log = run_native(exe, rom, user, out / f"{group}-{label}",
                             steps, video, timeout)
            verify_case(log, track, name, expected_open)
            if seed is not None and save.read_bytes() != seed:
                raise ValueError(f"Practice altered the player's save: {label}")
            if list(user.rglob("*.urrun")):
                raise ValueError("Practice published an earned run")
            cases.append({"group": group, "case": label, "track": track,
                          "course": name, "picker_steps": steps})
    user = out / "restart-in-practice-user"
    (user / "saves").mkdir(parents=True)
    restart_log = run_native(exe, rom, user, out / "restart-in-practice", 0,
                             video, timeout, RESTART_ENV)
    verify_restart(restart_log)
    if list(user.rglob("*.urrun")):
        raise ValueError("Practice restart published an earned run")
    return {
        "restart_in_practice": "pause_delayed_restart_rewound_sram_equal",
        "source_binding": {
            "github_sha": os.environ.get("GITHUB_SHA"),
            "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
            "rom_sha256": USA_SHA256,
        },
        "scope": "native-windows-practice-breadth-semantic-pad",
        "cases": cases,
        "courses_admitted": len(cases),
        "available_tier0": 20, "available_tier2": 40,
        "hunter_admitted": False,
        "tier2_seed_sha256": hashlib.sha256(tier2_seed()).hexdigest(),
        "player_save_bytes_unchanged": True,
        "practice_results_published": False,
        "physical_gamepad_certified": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    report = run(args.exe.resolve(), args.rom.resolve(), args.out.resolve(),
                 timeout=args.timeout, video=args.video)
    (args.out.resolve() / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: {report['courses_admitted']} original courses entered "
          "through native Practice with source identity; Hunter closed, "
          "saves unchanged; physical pads and release gates unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
