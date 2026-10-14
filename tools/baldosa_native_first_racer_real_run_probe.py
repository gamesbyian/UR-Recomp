#!/usr/bin/env python3
"""Native first-user Windows Modern journey: create -> played 1P -> Records.

Runs three genuinely separate instances of the *same* pinned Windows Baldosa
executable, with the existing exact Modern codecs and stock source route.
The only test-synthetic actions are frontend SDL edges and guest controller
inputs. The original guest must publish an actual settled Race result.

This witness does not claim physical pads, original-emulator parity, or
independent release acceptance. It never embeds or uploads ROM/SRAM bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from baldosa_native_first_racer_probe import (
    P1,
    run_game,
    verify_boot_sram,
    verify_creation,
    verify_native_save_codec,
    verify_reboot,
)
from baldosa_native_1p_records_probe import (
    native_records_reopened,
    source_finish_script,
    source_result_published,
)
from baldosa_windows_native_pause_route import (
    USA_SHA256,
    sha256,
    verify_named_profile_boot_bytes,
    verify_native_profile_checkpoint,
)


def require_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing/redirected canonical " + label)
    return path.read_bytes()


def assert_exact_one_named_run(user: Path, profile: str) -> tuple[Path, str]:
    root = user / "runs" / profile
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Played native event lost isolated Records root")
    # The product may legitimately attach .urghost or future immutable
    # sidecars. Require exactly one canonical .urrun, never demand an
    # otherwise empty directory or suppress unrelated replay artifacts.
    runs = list(root.glob("*.urrun"))
    if (len(runs) != 1 or runs[0].is_symlink() or
            not runs[0].is_file() or runs[0].suffix != ".urrun"):
        raise ValueError("Real 1P source result must publish one .urrun")
    content = runs[0].read_bytes()
    if not content:
        raise ValueError("Played guest produced an empty run")
    return runs[0], hashlib.sha256(content).hexdigest()


def run(exe: Path, rom: Path, fixture: Path, output: Path,
        *, video: str, timeout: int) -> dict[str, object]:
    for candidate in (exe, rom, fixture):
        if not candidate.is_file() or candidate.is_symlink():
            raise ValueError("Missing verified native executable/ROM/codec fixture")
    if sha256(rom) != USA_SHA256:
        raise ValueError("This test requires exact retail USA source ROM")
    output.mkdir(parents=True, exist_ok=False)
    user = output / "Brand New Player With Spaces"
    user.mkdir()

    # Game one: the REAL Modern root creates a named stock rider. The
    # cartridge continues anonymously until it exits. Source result credit
    # is forbidden before the next native process activates the new profile.
    created = run_game(
        exe, rom, user, output / "new_user_creates_first_racer", "4",
        "turbo on\nwait 900\nquit\n", video, timeout)
    verify_creation(created)
    profile = user / "saves" / f"profile-{P1}"
    raw_path = profile / "save.srm"
    typed_path = profile / "host-profile.txt"
    selector_path = user / "host-state-v1.txt"
    catalog_path = user / "profiles-v1.txt"
    seed = require_regular_file(raw_path, "first racer raw SRAM")
    if len(seed) != 8192:
        raise ValueError("First racer did not seed exact 8192-byte SRAM")
    for path in (typed_path, selector_path, catalog_path):
        require_regular_file(path, path.name)
    selectors = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (selector_path, catalog_path)
    }
    verify_native_save_codec(fixture, user, timeout)
    old_anonymous = user / "saves" / "save.srm"
    anonymous_digest = (
        hashlib.sha256(old_anonymous.read_bytes()).hexdigest()
        if old_anonymous.is_file() and not old_anonymous.is_symlink() else None
    )

    # Game two: fresh native after_config must preflight the existing named
    # profile and load the original 8 KiB snapshot BEFORE a single source
    # guest frame. Drive actual source 1P Race controls past GO to settled
    # results. A script-only entry or a synthetic result cannot pass.
    race = run_game(
        exe, rom, user, output / "fresh_named_player_completes_race", "1",
        source_finish_script(), video, timeout)
    verify_reboot(race)
    verify_boot_sram(race, seed)
    source_result_published(race, profile=P1)
    verify_native_profile_checkpoint(fixture, user, P1, race, timeout)
    run_path, run_digest = assert_exact_one_named_run(user, P1)
    saved_after_race = require_regular_file(raw_path, "post-race named SRAM")
    if len(saved_after_race) != 8192:
        raise ValueError("Guest checkpoint truncated new named save")
    if old_anonymous.exists() and (
        old_anonymous.is_symlink() or
        hashlib.sha256(old_anonymous.read_bytes()).hexdigest() != anonymous_digest
    ):
        raise ValueError("Played named event overwrote anonymous SRAM")

    # Game three: the SAME game executable opens Records in a truly new
    # process, with exact source-saved SRAM at boot. Records must display
    # exactly the ONE run earned by the game-two guest and never mint another.
    fresh = run_game(
        exe, rom, user, output / "new_game_reopens_earned_records", "1",
        "turbo on\nwait 1800\nquit\n", video, timeout)
    verify_named_profile_boot_bytes(fresh, saved_after_race)
    native_records_reopened(fresh, profile=P1)
    verify_native_profile_checkpoint(fixture, user, P1, fresh, timeout)
    newest_path, newest_digest = assert_exact_one_named_run(user, P1)
    if newest_path != run_path or newest_digest != run_digest:
        raise ValueError("Fresh-game Records mutated, replaced or duplicated run")
    for path in (selector_path, catalog_path):
        if (path.is_symlink() or
                hashlib.sha256(require_regular_file(path, path.name)).hexdigest() !=
                selectors[path.name]):
            raise ValueError("Played race or Records mutated selected profile authority")
    if not typed_path.is_file() or typed_path.is_symlink():
        raise ValueError("Native typed save no longer has canonical owner")
    if old_anonymous.exists() and (
        old_anonymous.is_symlink() or
        hashlib.sha256(old_anonymous.read_bytes()).hexdigest() != anonymous_digest
    ):
        raise ValueError("Fresh-game Records overwrote anonymous SRAM")
    return {
        "scope": "actual-native-windows-first-racer-to-earned-one-player-records",
        "first_game_created_first_named_racer": True,
        "second_game_loaded_named_sram_and_finished_real_source_race": True,
        "one_canonical_run_sha256": run_digest,
        "third_game_reopened_exact_earned_run_read_only": True,
        "active_selector_and_catalog_preserved": True,
        "anonymous_sram_preserved": True,
        "physical_gamepad_verified": False,
        "strict_original_native_event_pass": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("exe", "rom", "fixture", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--video", default="windows")
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    args_list = [getattr(args, key).resolve()
                 for key in ("exe", "rom", "fixture", "out")]
    result = run(*args_list, video=args.video, timeout=args.timeout)
    (args_list[-1] / "report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: empty native first-user root -> named rider -> real played "
          "1P finish -> canonical .urrun -> third game Records readback; "
          "no original/native parity or physical-pad release credit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
