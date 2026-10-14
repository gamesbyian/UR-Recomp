#!/usr/bin/env python3
"""Real Win32 Baldosa two-profile 2P result -> canonical paired Records -> fresh game.

Reuse the same built AOT game/Modern profile fixture and stock script grammar
as the proven 1P producer. A finite ~40k-frame source race is permitted to
report *no result*: that is a useful failure, never synthetic match credit.
Physical pads, original-emulator parity and independent release QA are not
claimed by this controlled SDL semantic-drive test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from baldosa_windows_native_pause_route import (
    USA_SHA256,
    native_modern_race_entry_script,
    sha256,
    verify_named_profile_boot_bytes,
    verify_native_profile_checkpoint,
)

P1 = "native-ci-rider"
P2 = "native-ci-second"
# Original pinned Baldosa race_2p.txt GO-relative human input, downstream of
# Modern's actual stock-menu handoff. P1 rider 0, P2 rider 2 from the
# already-existing P2 Down picker movement; confirmed by first Win32 trace.
SOURCE_TWO_PLAYER_DRIVE = (
    "press right+p2:right 800",
    "press right+a+p2:right+p2:b 30",
    "press right+p2:right 800",
    "press right+up+p2:right+p2:down 60",
    "press right+p2:right 1500",
)
# First real pinned Win32 producer independently observed the original
# 2P result at host frame 4377, while the stock GO-relative inputs themselves
# continue to ~5542. Never burn 38,500 additional empty simulation frames
# after a result already settled *during* the driven route. Stop after a
# short, bounded guest grace window and require the actual 2P result log,
# exact paired writer and fresh game readback for success.
AFTER_DRIVE_WAIT = 120


def source_match_script() -> str:
    base = native_modern_race_entry_script(2)
    end = "dump go\nquit\n"
    if not base.endswith(end):
        raise ValueError("Existing native 2P root->GO route changed")
    return (base[:-len(end)] + "dump go\n" +
            "\n".join(SOURCE_TWO_PLAYER_DRIVE) +
            f"\nwait {AFTER_DRIVE_WAIT}\ndump after-source-2p-drive\nquit\n")


def source_match_published(
    log: str, *, p1_profile: str = P1, p2_profile: str = P2,
    p1_rider: int = 0, p2_rider: int = 2,
) -> dict[str, int]:
    stages = (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={p1_profile} ",
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1 "
        f"profile1={p1_profile} profile2={p2_profile} course=course:01 ",
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p ",
    )
    positions = []
    for stage in stages:
        if log.count(stage) != 1:
            raise ValueError(f"Missing/duplicate genuine 2P source stage: {stage}")
        positions.append(log.index(stage))
    if positions != sorted(positions):
        # Match writer emits before the native observer's summary. Both are
        # after settled source SRAM, never before stock handoff or GO.
        raise ValueError("2P identities, guest result or record out of order")
    match = re.search(
        r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-2p "
        r"race_host=(\d+) result_host=(\d+) riders=(\d+),(\d+) "
        r"hundredths=(\d+),(\d+) winner=(\d+) "
        r"input_frames=(\d+) input_runs=(\d+) published=(\d+)$", log)
    if not match:
        raise ValueError("Actual settled original 2P SRAM was not observed")
    (first, last, p1, p2, time1, time2, winner, frames, runs, published) = (
        int(n) for n in match.groups())
    if (first <= 0 or last <= first or p1 != p1_rider or p2 != p2_rider or
            time1 > 60000 or time2 > 60000 or
            winner not in (0, 1, 2) or frames <= 0 or runs <= 0 or
            published != 1 or
            "UR_BALDOSA_NATIVE_MATCH SAVE_PENDING=1" in log or
            "UR_BALDOSA_NATIVE_MATCH PUBLISH_REJECTED" in log):
        raise ValueError("Native 2P settled result lacked a committed exact match")
    return {"source_result_host": last, "source_input_frames": frames,
            "p1_hundredths": time1, "p2_hundredths": time2, "winner": winner}


def source_paired_records_reopened(
    log: str, *, selected_profile: str = P1,
) -> None:
    ordered = (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={selected_profile} ",
        "UR_BALDOSA_MODERN_ROOT records_page=1p",
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected",
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 "
        "unavailable=0 selected=1",
        "UR_BALDOSA_MODERN_ROOT records_page=2p",
        "UR_BALDOSA_MODERN_ROOT records_page=1p",
        "UR_BALDOSA_MODERN_ROOT records_closed=1",
    )
    positions = []
    after = 0
    for token in ordered:
        pos = log.find(token, after)
        if pos < 0:
            raise ValueError(f"Fresh native game did not show 2P Records: {token}")
        positions.append(pos)
        after = pos + len(token)
    if ("UR_BALDOSA_NATIVE_MATCH CAPTURED=1" in log or
            "UR_BALDOSA_NATIVE_RESULT observed=1" in log or
            log.count("UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 ") != 1 or
            log.count("UR_BALDOSA_MODERN_ROOT records_last_2p=") != 1):
        raise ValueError("Read-only Records invented or duplicated guest match")


def run_guest(exe: Path, rom: Path, work: Path, user: Path,
              *, script: str, smoke: str, timeout: int, video: str) -> str:
    work.mkdir(parents=True, exist_ok=False)
    route = work / "source-route.txt"
    route.write_text(script, encoding="ascii")
    cfg = work / "config.ini"
    cfg.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(user),
           "UR_EXECUTION_MODE": "modern",
           "UR_BALDOSA_MODERN_ROOT": "1",
           "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": smoke,
           "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
           "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
           "UR_BALDOSA_MODERN_INPUT": "1",
           "UR_BALDOSA_PAUSE_SMOKE": "0",
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    process = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(cfg), "--script",
         str(route), str(rom)], cwd=work, env=env, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    log = process.stdout + "\n" + process.stderr
    (work / "log.txt").write_text(log, encoding="utf-8")
    if process.returncode:
        raise RuntimeError("Native 2P or fresh Records game rejected " +
                           str(process.returncode) + ": " + log[-2500:])
    return log


def run(exe: Path, rom: Path, fixture: Path, seed: Path, out: Path,
        *, video: str, timeout: int) -> dict[str, object]:
    for path in (exe, rom, fixture, seed):
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing or redirected input: " + str(path))
    if sha256(rom) != USA_SHA256 or seed.stat().st_size != 8192:
        raise ValueError("Expected exact retail USA and actual 8192-byte SRAM")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "Two Distinct Modern Player Profiles"
    user.mkdir()
    first = subprocess.run(
        [str(fixture), str(user), str(seed)], cwd=out,
        capture_output=True, text=True, timeout=timeout)
    if first.returncode:
        raise RuntimeError("Failed original native Modern P1 fixture: " +
                           first.stderr[-1500:])
    second = subprocess.run(
        [str(fixture), str(user), str(seed), "--add-second-keep-first"],
        cwd=out, capture_output=True, text=True, timeout=timeout)
    if (second.returncode or
            "registered=native-ci-second selected=native-ci-rider "
            not in second.stdout):
        raise RuntimeError("Canonical two-profile P1 preservation failed: " +
                           second.stderr[-1500:] + second.stdout[-1000:])
    p1raw = user / "saves/profile-native-ci-rider/save.srm"
    p2raw = user / "saves/profile-native-ci-second/save.srm"
    p2_original = p2raw.read_bytes()
    if len(p2_original) != 8192 or p1raw.read_bytes() == p2_original:
        raise ValueError("Two-player Modern SRAM identity was not isolated")
    boot = p1raw.read_bytes()
    match_log = run_guest(
        exe, rom, out / "played_native_2p", user,
        script=source_match_script(), smoke="3", video=video, timeout=timeout)
    verify_named_profile_boot_bytes(match_log, boot)
    source = source_match_published(match_log)
    archive = user / "multiplayer-runs"
    if not archive.is_dir():
        raise ValueError("Real native guest has no canonical match directory")
    pair = sorted(archive.iterdir())
    if (len(pair) != 2 or
            any(not p.is_file() or p.is_symlink() or p.stat().st_size == 0
                for p in pair)):
        raise ValueError("Exactly two immutable 2P artifacts were not published")
    runs = [p for p in pair if p.name.endswith(".urrun")]
    if (len(runs) != 1 or
            pair[0].name not in (runs[0].name, runs[0].name + ".urmatch") or
            set(p.name for p in pair) !=
            {runs[0].name, runs[0].name + ".urmatch"}):
        raise ValueError("One source-bound .urrun/.urmatch pair is mandatory")
    original = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in pair}
    verify_native_profile_checkpoint(fixture, user, P1, match_log, timeout)
    if p2raw.read_bytes() != p2_original:
        raise ValueError("Played 2P game leaked P1 SRAM to P2 profile")
    fresh_boot_sram = p1raw.read_bytes()
    fresh = run_guest(
        exe, rom, out / "fresh_game_2p_records", user,
        script="turbo on\nwait 1800\nquit\n", smoke="1",
        video=video, timeout=timeout)
    verify_named_profile_boot_bytes(fresh, fresh_boot_sram)
    source_paired_records_reopened(fresh)
    reread = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in archive.iterdir()}
    if reread != original or p2raw.read_bytes() != p2_original:
        raise ValueError("Fresh native Records mutated a paired match or P2 SRAM")
    if (user / "saves/save.srm").exists():
        raise ValueError("Native 2P invented an anonymous default save")
    verify_native_profile_checkpoint(fixture, user, P1, fresh, timeout)
    return {
        "scope": "actual-source-2p-baldosa-modern-records-integration",
        "p1_profile": P1, "p2_profile": P2,
        "played_guest_2p_result_published": True,
        "canonical_match_artifact_sha256": original,
        "new_native_process_reopened_paired_2p_records": True,
        "p2_named_profile_sram_preserved": True,
        "source_result": source,
        "original_native_strict_event_pass": False,
        "physical_gamepads_tested": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("exe", "rom", "fixture", "seed", "out"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=360)
    args = parser.parse_args()
    paths = [getattr(args, name).resolve()
             for name in ("exe", "rom", "fixture", "seed", "out")]
    result = run(*paths, video=args.video, timeout=args.timeout)
    (paths[-1] / "report.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("PASS: actual original 2P native result -> paired modern Records "
          "-> freshly booted game readback; no independent event or hardware credit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
