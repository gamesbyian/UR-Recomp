#!/usr/bin/env python3
"""First native Modern controller-semantic racer setup -> new-process boot.

Uses the SAME existing Windows AOT game, profile/catalog codecs and full SRAM
observer. A preset is intentionally a bounded first-run proof; arbitrary
player names, mid-process racer swapping, physical pads and release QA are
not claimed. The old anonymous cartridge is never reidentified in-process.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from baldosa_windows_native_pause_route import USA_SHA256, fnv32, sha256


def assert_created(log: str) -> None:
    required = (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT first_racer_open=1 presets=16",
        "UR_BALDOSA_MODERN_ROOT synthetic_first_racer_x=1",
        "UR_BALDOSA_MODERN_ROOT first_racer_preset=1",
        "UR_BALDOSA_NATIVE_PROFILE CREATED profile=andrew rider=1 "
        "bytes=8192 restart_required=1",
        "UR_BALDOSA_MODERN_ROOT first_racer_created=1 restart_required=1",
    )
    positions = []
    for item in required:
        if log.count(item) != 1:
            raise ValueError("No unique first-run player action: " + item)
        positions.append(log.index(item))
    if positions != sorted(positions):
        raise ValueError("First-run identity committed outside human UI order")
    if ("UR_BALDOSA_MODERN_ROOT stock_requested " in log or
            "UR_BALDOSA_NATIVE_RUN CAPTURED=1" in log or
            "UR_BALDOSA_NATIVE_MATCH CAPTURED=1" in log):
        raise ValueError("Unrebooted guest falsely claimed a named run")


def assert_fresh_named_guest(log: str, raw: bytes) -> None:
    required = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew "
        "root=saves/profile-andrew",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=andrew "
        f"bytes=8192 fnv={fnv32(raw)}",
    )
    positions = []
    for item in required:
        if log.count(item) != 1:
            raise ValueError("New game process didn't boot canonical named SRAM: " + item)
        positions.append(log.index(item))
    if positions != sorted(positions):
        raise ValueError("Native game used player SRAM before canonical activation")
    if ("UR_BALDOSA_NATIVE_PROFILE DEFAULT " in log or
            "UR_BALDOSA_NATIVE_PROFILE REJECTED" in log or
            "UR_BALDOSA_NATIVE_PROFILE CREATED" in log):
        raise ValueError("Fresh process silently recreated or repaired the racer")


def run_guest(exe: Path, rom: Path, user: Path, directory: Path,
              *, smoke: str, timeout: int, video: str) -> str:
    directory.mkdir(parents=True, exist_ok=False)
    route = directory / "input.script"
    route.write_text("turbo on\nwait 1800\nquit\n", encoding="ascii")
    cfg = directory / "config.ini"
    cfg.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = {
        **os.environ,
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": smoke,
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "UR_BALDOSA_PAUSE_SMOKE": "0",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    }
    process = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(cfg), "--script",
         str(route), str(rom)],
        cwd=directory, env=env, text=True, capture_output=True,
        errors="replace", timeout=timeout)
    log = process.stdout + "\n" + process.stderr
    (directory / "log.txt").write_text(log, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(
            f"Native controller-first onboarding guest exited "
            f"{process.returncode}: {log[-3000:]}")
    return log


def run(exe: Path, rom: Path, fixture: Path, output: Path,
        *, video: str, timeout: int) -> dict[str, object]:
    for candidate in (exe, rom, fixture):
        if not candidate.is_file() or candidate.is_symlink():
            raise ValueError(f"Missing exact non-redirected input: {candidate}")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Exact USA retail source ROM required")
    output.mkdir(parents=True, exist_ok=False)
    user = output / "New Modern Gamer With Spaces"
    user.mkdir()
    first = run_guest(exe, rom, user, output / "first_controller_racer",
                      smoke="4", timeout=timeout, video=video)
    assert_created(first)
    profile_dir = user / "saves" / "profile-andrew"
    raw_file = profile_dir / "save.srm"
    typed_file = profile_dir / "host-profile.txt"
    for entry in (profile_dir, raw_file, typed_file,
                  user / "profiles-v1.txt", user / "host-state-v1.txt"):
        if entry.is_symlink() or not entry.exists():
            raise ValueError("Canonical first-racer transaction incomplete: " + str(entry))
    raw = raw_file.read_bytes()
    if len(raw) != 8192 or raw[0x0748] != 1:
        raise ValueError("First controller choice did not seed correct stock rider")
    reread = subprocess.run(
        [str(fixture), str(user), "andrew", "--verify-native-save"],
        text=True, capture_output=True, timeout=timeout)
    if reread.returncode or (
            "UR_BALDOSA_NATIVE_PROFILE VERIFIED profile=andrew sram=8192"
            not in reread.stdout):
        raise ValueError("Existing typed/catalog/raw codec refused created racer")

    second = run_guest(exe, rom, user, output / "fresh_named_game",
                       smoke="0", timeout=timeout, video=video)
    assert_fresh_named_guest(second, raw)
    if raw_file.read_bytes() != raw:
        raise ValueError("Fresh read-only guest boot changed clean racer SRAM")
    if len(list((user / "saves").glob("profile-*"))) != 1:
        raise ValueError("First-run transaction created unintended profile slots")
    return {
        "scope": "new-native-first-run-preset-selection-through-reboot",
        "player_input": "test-only physical-event semantic gamepad X, then SDL keys",
        "created_profile_id": "andrew",
        "created_stock_rider_index": 1,
        "canonical_initial_sram_bytes": len(raw),
        "stock_sram_fingerprint": fnv32(raw),
        "separate_game_booted_newly_committed_profile": True,
        "original_native_event_pass": False,
        "physical_controller_acceptance": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("exe", "rom", "fixture", "out"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=140)
    args = parser.parse_args()
    paths = [getattr(args, n).resolve() for n in ("exe", "rom", "fixture", "out")]
    report = run(*paths, video=args.video, timeout=args.timeout)
    (paths[-1] / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: controller-semantic first racer creation -> canonical "
          "typed/raw/catalog/selector -> fresh native game boot; "
          "no physical/hardware or original-native event credit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
