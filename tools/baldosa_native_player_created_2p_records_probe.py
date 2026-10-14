#!/usr/bin/env python3
"""Real Win32 new-user P1+P2 creation, earned guest match and both Records.

The two player profiles MUST come from actual native Modern root SDL events.
The fixture may read canonical codecs or select an EXISTING next-boot
profile, but must never create a profile, result, or archival pair here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from baldosa_native_first_racer_probe import (
    run_game, verify_creation, verify_boot_sram, verify_native_save_codec,
)
from baldosa_native_second_racer_probe import require_p2_creation
from baldosa_native_2p_records_probe import (
    SOURCE_TWO_PLAYER_DRIVE, AFTER_DRIVE_WAIT, run_guest,
    source_match_published, source_paired_records_reopened,
)
from baldosa_windows_native_pause_route import (
    USA_SHA256, native_modern_race_entry_script, sha256,
    verify_native_modern_root_log,
)

P1 = "mike"
P2 = "andrew"


def source_andrew_match_script() -> str:
    """Original 2P source route with the second stock rider LEFT at Andrew.

    The old fixture-specific route presses P2 Down to rider 2. This newly
    created P2 has authentic rider index 1; changing the source picker there
    would make the host's authoritative pair binder correctly reject it.
    """
    base = native_modern_race_entry_script(2)
    down = "press p2:down 2\nwait 30\n"
    end = "dump go\nquit\n"
    if base.count(down) != 1 or not base.endswith(end):
        raise ValueError("Original 2P stock route changed: re-evaluate picker")
    base = base.replace(down, "", 1)
    return (base[:-len(end)] + "dump go\n" +
            "\n".join(SOURCE_TWO_PLAYER_DRIVE) +
            f"\nwait {AFTER_DRIVE_WAIT}\ndump played-2p-source\nquit\n")


def exact_pair_digest(archive: Path) -> dict[str, str]:
    if archive.is_symlink() or not archive.is_dir():
        raise ValueError("Canonical source-backed 2P archive absent")
    entries = sorted(archive.iterdir())
    runs = [p for p in entries if p.name.endswith(".urrun")]
    if (len(entries) != 2 or len(runs) != 1 or
            {p.name for p in entries} !=
            {runs[0].name, runs[0].name + ".urmatch"} or
            any(p.is_symlink() or not p.is_file() or p.stat().st_size == 0
                for p in entries)):
        raise ValueError("Expected exactly one published .urrun/.urmatch pair")
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in entries}


def profile_sram(user: Path, name: str) -> bytes:
    if name not in (P1, P2):
        raise ValueError("Unexpected stock racer")
    file = user / "saves" / ("profile-" + name) / "save.srm"
    if file.is_symlink() or not file.is_file():
        raise ValueError("Missing separately created profile SRAM: " + name)
    data = file.read_bytes()
    if len(data) != 8192 or data[0x0748] != (0 if name == P1 else 1):
        raise ValueError("Incorrect guest racer byte / length: " + name)
    return data


def run(exe: Path, rom: Path, fixture: Path, out: Path,
        *, timeout: int, video: str) -> dict[str, object]:
    for file in (exe, rom, fixture):
        if file.is_symlink() or not file.is_file():
            raise ValueError("Source ROM or exact native executable unavailable")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Source must be the exact retail USA ROM")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "New Player-Created Named Racers"
    user.mkdir()

    # Game 1: an anonymous user explicitly creates Mike P1 via X/A.
    first = run_game(exe, rom, user, out / "first_P1_mike", "4",
                     "turbo on\nwait 900\nquit\n", video, timeout)
    verify_creation(first, preset=0)
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    catalog = user / "profiles-v1.txt"
    selector = user / "host-state-v1.txt"
    before_selector = selector.read_bytes()
    original_p1 = profile_sram(user, P1)

    # Game 2: named P1 explicitly creates Andrew P2 via the SAME native root.
    second = run_game(exe, rom, user, out / "named_P1_adds_P2", "5",
                      "turbo on\nwait 900\nquit\n", video, timeout)
    require_p2_creation(second)
    if selector.read_bytes() != before_selector:
        raise ValueError("P2 publication illegally switched active P1")
    original_p2 = profile_sram(user, P2)
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    verify_native_save_codec(fixture, user, timeout, profile=P2)
    before_catalog = catalog.read_bytes()

    # Game 3: genuine separately confirmed root seats, real stock source
    # menus and a settled 2P Race, not a synthetic GO/result or seeded data.
    played = run_guest(
        exe, rom, out / "played_native_2p", user,
        script=source_andrew_match_script(), smoke="3",
        timeout=timeout, video=video)
    verify_boot_sram(played, original_p1, profile=P1)
    verify_native_modern_root_log(played, 2)
    source_result = source_match_published(
        played, p1_profile=P1, p2_profile=P2, p1_rider=0, p2_rider=1)
    if catalog.read_bytes() != before_catalog or selector.read_bytes() != before_selector:
        raise ValueError("Played game changed verified profile authority")
    if profile_sram(user, P2) != original_p2:
        raise ValueError("P1 guest leaked into independently initialized P2 SRAM")
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    verify_native_save_codec(fixture, user, timeout, profile=P2)
    paired = exact_pair_digest(user / "multiplayer-runs")

    # Game 4: P1 views the source-earned pair in an independent fresh
    # game process without publishing, mutating or duplicating that pair.
    next_mike_bytes = profile_sram(user, P1)
    mike_view = run_guest(
        exe, rom, out / "fresh_mike_records", user,
        script="turbo on\nwait 1800\nquit\n", smoke="1",
        timeout=timeout, video=video)
    verify_boot_sram(mike_view, next_mike_bytes, profile=P1)
    source_paired_records_reopened(mike_view, selected_profile=P1)
    if exact_pair_digest(user / "multiplayer-runs") != paired:
        raise ValueError("P1 viewing Records mutated the committed match")
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    verify_native_save_codec(fixture, user, timeout, profile=P2)

    # The existing next-process selector backend validates both profiles
    # under OS-handle locks. Its test-only CLI caller makes no claim that
    # the player-facing profile-switch UI has shipped.
    old_selector = selector.read_bytes()
    old_catalog = catalog.read_bytes()
    old_p1 = profile_sram(user, P1)
    old_p2 = profile_sram(user, P2)
    switched = subprocess.run(
        [str(fixture), str(user), P1, P2, "--select-existing-next-boot"],
        text=True, capture_output=True, timeout=timeout)
    if (switched.returncode or
            "existing_next_boot=andrew previous=mike no_guest_swap=1"
            not in switched.stdout or selector.read_bytes() == old_selector):
        raise ValueError("Safe next-boot selector rejected: " +
                         switched.stdout[-700:] + switched.stderr[-700:])
    if (catalog.read_bytes() != old_catalog or profile_sram(user, P1) != old_p1 or
            profile_sram(user, P2) != old_p2 or
            exact_pair_digest(user / "multiplayer-runs") != paired):
        raise ValueError("Existing P1 switch modified other participant data")

    # Game 5: native guest *boots* Andrew's own bytes and its Records
    # includes the same one original-played match as Mike's did.
    andrew_view = run_guest(
        exe, rom, out / "fresh_andrew_records", user,
        script="turbo on\nwait 1800\nquit\n", smoke="1",
        timeout=timeout, video=video)
    verify_boot_sram(andrew_view, old_p2, profile=P2)
    source_paired_records_reopened(andrew_view, selected_profile=P2)
    if (exact_pair_digest(user / "multiplayer-runs") != paired or
            catalog.read_bytes() != old_catalog or
            profile_sram(user, P1) != old_p1):
        raise ValueError("P2 viewing Records mutated the match or Mike")
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    verify_native_save_codec(fixture, user, timeout, profile=P2)
    if (user / "saves" / "save.srm").exists():
        raise ValueError("Guest created forbidden shared anonymous SRAM")

    return {
        "scope": "two-native-controller-created-profiles-played-source-2p-and-both-records",
        "actual_frontend_created_profiles": [P1, P2],
        "observed_stock_riders": [0, 1],
        "observed_source_guest_result": source_result,
        "canonical_one_pair_sha256": paired,
        "fresh_native_records_for_each": True,
        "p2_existing_profile_select_via_fixture_not_player_UI": True,
        "native_existing_p1_profile_selector_UI_proved": False,
        "physical_pad_hardware_accepted": False,
        "original_native_strict_event_accepted": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("exe", "rom", "fixture", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=220)
    args = parser.parse_args()
    paths = [getattr(args, arg).resolve()
             for arg in ("exe", "rom", "fixture", "out")]
    report = run(*paths, timeout=args.timeout, video=args.video)
    (paths[-1] / "report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("PASS: native-created Mike/Andrew -> played original 2P source match "
          "-> exactly one paired record -> both fresh native Records views. "
          "No independent original parity or physical pad claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
