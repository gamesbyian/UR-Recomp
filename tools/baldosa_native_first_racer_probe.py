#!/usr/bin/env python3
"""Native first-run stock racer -> canonical next-boot identity, same Windows PE.

This is host-owned onboarding, never a synthetic guest-result or real pad QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess

from baldosa_windows_native_pause_route import (
    USA_SHA256,
    native_modern_race_entry_script,
    sha256,
    fnv32,
)

P1 = "mike"  # Historical first-user default; existing full 1P journey imports this.
STOCK_TEST_PRESETS = ("mike", "andrew", "martin")


def run_game(exe: Path, rom: Path, user: Path, work: Path, smoke: str,
             script: str, video: str, timeout: int,
             *, preset: int = 0) -> str:
    work.mkdir(parents=True, exist_ok=False)
    route = work / "stock-route.txt"
    route.write_text(script, encoding="ascii")
    ini = work / "config.ini"
    ini.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
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
    if smoke == "4" and preset == 1:
        env["UR_BALDOSA_FIRST_RACER_TEST_PRESET"] = "1"
    if smoke == "5" and preset == 2:
        env["UR_BALDOSA_SECOND_RACER_TEST_PRESET"] = "2"
    proc = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(ini),
         "--script", str(route), str(rom)],
        cwd=work, env=env, capture_output=True,
        # Native path receipts are emitted as UTF-8 bytes on every host.
        # Windows' default text codec is its ANSI codepage, which previously
        # mangled genuine non-ACP 漢字/🚲 saved-run path diagnostics.
        text=True, encoding="utf-8", errors="replace", timeout=timeout)
    log = proc.stdout + "\n" + proc.stderr
    (work / "log.txt").write_text(log, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError("Real native first-racer guest returned " +
                           str(proc.returncode) + ": " + log[-2200:])
    return log


def verify_creation(log: str, *, preset: int = 0) -> None:
    if preset not in (0, 1):
        raise ValueError("Unapproved test-only stock rider preset")
    profile = STOCK_TEST_PRESETS[preset]
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE DEFAULT no_host_state=1",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT first_racer_opened=1 activation=next_process",
        *([f"UR_BALDOSA_MODERN_ROOT first_racer_preset={preset}"]
          if preset else []),
        f"UR_BALDOSA_NATIVE_FIRST_RACER status=0 preset={preset} "
        f"id={profile} activation=next_process",
        "UR_BALDOSA_MODERN_ROOT first_racer_created=1 activation=next_process",
    )
    positions = []
    for token in stages:
        if log.count(token) != 1:
            raise ValueError("Missing/duplicated native create stage: " + token)
        positions.append(log.index(token))
    if positions != sorted(positions):
        raise ValueError("Native first-create stages were not ordered")
    if (f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile}" in log or
            "UR_BALDOSA_MODERN_ROOT stock_entered" in log or
            "UR_BALDOSA_NATIVE_RUN CAPTURED=1" in log):
        raise ValueError("First native process hot-swapped guest SRAM")


def verify_boot_sram(log: str, raw: bytes, *, profile: str = P1) -> None:
    if profile not in STOCK_TEST_PRESETS:
        raise ValueError("Unknown exact first-run source rider")
    expected = (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile} "
        f"root=saves/profile-{profile}\n")
    match = re.findall(
        r"(?m)^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
        rf"profile={re.escape(profile)} bytes=8192 fnv=([0-9a-fA-F]{{8}})$", log)
    if (len(raw) != 8192 or expected not in log or len(match) != 1 or
            match[0].lower() != fnv32(raw)):
        raise ValueError("Fresh guest did not load exact first-racer SRAM")


def verify_native_save_codec(fixture: Path, user: Path, timeout: int,
                             *, profile: str = P1) -> None:
    if profile not in STOCK_TEST_PRESETS:
        raise ValueError("Unknown canonical stock rider")
    result = subprocess.run(
        [str(fixture), str(user), profile, "--verify-native-save"],
        capture_output=True, text=True, timeout=timeout)
    if (result.returncode or
            f"UR_BALDOSA_NATIVE_PROFILE VERIFIED profile={profile} sram=8192 "
            not in result.stdout):
        raise ValueError("Canonical native typed/raw first-racer SRAM mismatch: "
                         + result.stdout[-800:] + result.stderr[-800:])


def verify_reboot(log: str, *, profile: str = P1) -> None:
    if profile not in STOCK_TEST_PRESETS:
        raise ValueError("Unknown canonical first racer")
    stages = (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile} ",
        f"UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile={profile} bytes=8192 ",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
    )
    positions = []
    for token in stages:
        if log.count(token) != 1:
            raise ValueError("Fresh native guest did not adopt preset: " + token)
        positions.append(log.index(token))
    if positions != sorted(positions):
        raise ValueError("Next-process profile and stock handoff out of order")
    if ("UR_BALDOSA_MODERN_ROOT first_racer_created=1" in log or
            "UR_BALDOSA_NATIVE_PROFILE DEFAULT" in log):
        raise ValueError("Next launch recreated a second identity")


def run(exe: Path, rom: Path, fixture: Path, out: Path,
        *, video: str, timeout: int, preset: int = 0) -> dict[str, object]:
    if preset not in (0, 1):
        raise ValueError("Unsupported native source proof preset")
    profile_id = STOCK_TEST_PRESETS[preset]
    for path in (exe, rom, fixture):
        if not path.is_file() or path.is_symlink():
            raise ValueError("Exact native input absent or redirected")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Only the exact USA source guest may enter this test")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "Fresh User Data With Spaces"
    user.mkdir()
    if (user / "host-state-v1.txt").exists():
        raise ValueError("Expected genuinely fresh Modern user data")
    created = run_game(
        exe, rom, user, out / "first_anonymous_process", "4",
        "turbo on\nwait 900\nquit\n", video, timeout, preset=preset)
    verify_creation(created, preset=preset)
    profile = user / "saves" / f"profile-{profile_id}"
    raw = profile / "save.srm"
    typed = profile / "host-profile.txt"
    catalog = user / "profiles-v1.txt"
    selector = user / "host-state-v1.txt"
    for path in (raw, typed, catalog, selector):
        if not path.is_file() or path.is_symlink():
            raise ValueError("Native first-racer canonical artifact missing")
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (raw, typed, catalog, selector)}
    if raw.stat().st_size != 8192:
        raise ValueError("Created profile was not stock 8192-byte SRAM")
    verify_native_save_codec(fixture, user, timeout, profile=profile_id)
    original_bytes = raw.read_bytes()
    if original_bytes[0x0748] != preset:
        raise ValueError("Created profile has wrong original stock rider byte")
    restarted = run_game(
        exe, rom, user, out / "fresh_named_process", "1",
        native_modern_race_entry_script(1), video, timeout)
    verify_reboot(restarted, profile=profile_id)
    verify_boot_sram(restarted, original_bytes, profile=profile_id)
    verify_native_save_codec(fixture, user, timeout, profile=profile_id)
    # The native guest may advance its save on shutdown, but its identity,
    # catalog and selected active pointer must not unexpectedly change.
    for path in (typed, catalog, selector):
        if not path.is_file() or path.is_symlink():
            raise ValueError("Named profile's canonical files disappeared")
    if raw.stat().st_size != 8192:
        raise ValueError("Named guest changed raw save format")
    if (user / "saves" / f"profile-{profile_id}-2").exists():
        raise ValueError("Fresh game unexpectedly created duplicate profile")
    return {
        "scope": "first-anonymous-modern-root-stock-racer-next-process-boot",
        "first_native_guest_creation": True,
        "fresh_native_guest_named_profile_applied": True,
        "existing_stock_sram_root": f"saves/profile-{profile_id}",
        "newly_selected_stock_preset_index": preset,
        "stock_rider_boot_verified": True,
        "before_reboot_sha256": before,
        "physical_pad_acceptance": False,
        "independent_original_native_event_pass": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("exe", "rom", "fixture", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--video", default="windows")
    p.add_argument("--timeout", type=int, default=90)
    p.add_argument("--preset", type=int, choices=(0, 1), default=0)
    args = p.parse_args()
    paths = [getattr(args, k).resolve()
             for k in ("exe", "rom", "fixture", "out")]
    report = run(*paths, video=args.video, timeout=args.timeout,
                 preset=args.preset)
    (paths[-1] / "report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("PASS: native empty-root preset creation -> second native Windows "
          "process boots canonical new named racer; no guest hot-swap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
