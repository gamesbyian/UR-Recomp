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
    source_match_script, run_guest,
    source_match_published, source_paired_records_reopened,
)
from baldosa_windows_native_pause_route import (
    USA_SHA256, sha256,
    verify_native_modern_root_log,
)

P1 = "mike"
P2 = "martin"


def source_martin_match_script() -> str:
    """The EXACT existing original stock 2P route, picker and scored drive.

    P2 must have been selected via the real Modern stock-racer modal to
    canonical Martin index 2, which the unchanged original picker chooses.
    No guessed script modifications or guest memory writes are permitted.
    """
    return source_match_script()

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
    if len(data) != 8192 or data[0x0748] != (0 if name == P1 else 2):
        raise ValueError("Incorrect guest racer byte / length: " + name)
    return data


def anonymous_bootstrap_sram(user: Path) -> bytes | None:
    """Observe the legacy anonymous save from process 1, never authorize it.

    The unprofiled guest may checkpoint an 8KiB default SRAM on its first
    exit, even after the user created a NEW profile for NEXT process. This
    is historical fallback data, never a source of named racer authority.
    Every subsequent named game must leave these exact bytes unchanged.
    """
    file = user / "saves" / "save.srm"
    if file.is_symlink():
        raise ValueError("Anonymous stock SRAM redirected by a symlink")
    if not file.exists():
        return None
    if not file.is_file():
        raise ValueError("Anonymous stock save replaced with non-file")
    raw = file.read_bytes()
    if len(raw) != 8192:
        raise ValueError("Anonymous bootstrap SRAM is not 8192 bytes")
    return raw


def require_legacy_untouched(user: Path, initial: bytes | None) -> None:
    if anonymous_bootstrap_sram(user) != initial:
        raise ValueError(
            "Named game wrote or created shared anonymous SRAM after bootstrap")


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
    # A source guest with NO selected profile may create the historical
    # anonymous save at its own first shutdown; capture it once, then ban
    # any further writes while verified named racers own the save root.
    legacy_bootstrap = anonymous_bootstrap_sram(user)
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    catalog = user / "profiles-v1.txt"
    selector = user / "host-state-v1.txt"
    before_selector = selector.read_bytes()
    # This first-game image may receive a legitimate native checkpoint
    # when game 2 boots P1 to create P2. Compare the LAST committed image.

    # Game 2: named P1 explicitly creates Martin P2 via the SAME native root.
    second = run_game(exe, rom, user, out / "named_P1_adds_P2", "5",
                      "turbo on\nwait 900\nquit\n", video, timeout,
                      preset=2)
    require_p2_creation(second, preset=2)
    require_legacy_untouched(user, legacy_bootstrap)
    if selector.read_bytes() != before_selector:
        raise ValueError("P2 publication illegally switched active P1")
    original_p2 = profile_sram(user, P2)
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    verify_native_save_codec(fixture, user, timeout, profile=P2)
    # Native game 2 writes Mike's own post-boot checkpoint at exit.
    # Exact guest BOOT_SRAM must match THIS pre-game-3 canonical image,
    # not game 1's obsolete snapshot. Verify full typed/raw identity first.
    original_p1 = profile_sram(user, P1)
    before_catalog = catalog.read_bytes()

    # Game 3: genuine separately confirmed root seats, real stock source
    # menus and a settled 2P Race, not a synthetic GO/result or seeded data.
    played = run_guest(
        exe, rom, out / "played_native_2p", user,
        script=source_martin_match_script(), smoke="3",
        timeout=timeout, video=video)
    verify_boot_sram(played, original_p1, profile=P1)
    require_legacy_untouched(user, legacy_bootstrap)
    verify_native_modern_root_log(played, 2)
    source_result = source_match_published(
        played, p1_profile=P1, p2_profile=P2, p1_rider=0, p2_rider=2)
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
    require_legacy_untouched(user, legacy_bootstrap)
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
            "existing_next_boot=martin previous=mike no_guest_swap=1"
            not in switched.stdout or selector.read_bytes() == old_selector):
        raise ValueError("Safe next-boot selector rejected: " +
                         switched.stdout[-700:] + switched.stderr[-700:])
    if (catalog.read_bytes() != old_catalog or profile_sram(user, P1) != old_p1 or
            profile_sram(user, P2) != old_p2 or
            exact_pair_digest(user / "multiplayer-runs") != paired):
        raise ValueError("Existing P1 switch modified other participant data")

    # Game 5: native guest *boots* Martin's own bytes and its Records
    # includes the same one original-played match as Mike's did.
    martin_view = run_guest(
        exe, rom, out / "fresh_martin_records", user,
        script="turbo on\nwait 1800\nquit\n", smoke="1",
        timeout=timeout, video=video)
    verify_boot_sram(martin_view, old_p2, profile=P2)
    source_paired_records_reopened(martin_view, selected_profile=P2)
    require_legacy_untouched(user, legacy_bootstrap)
    if (exact_pair_digest(user / "multiplayer-runs") != paired or
            catalog.read_bytes() != old_catalog or
            profile_sram(user, P1) != old_p1):
        raise ValueError("P2 viewing Records mutated the match or Mike")
    verify_native_save_codec(fixture, user, timeout, profile=P1)
    verify_native_save_codec(fixture, user, timeout, profile=P2)
    require_legacy_untouched(user, legacy_bootstrap)

    return {
        "scope": "two-native-controller-created-profiles-played-source-2p-and-both-records",
        "actual_frontend_created_profiles": [P1, P2],
        "observed_stock_riders": [0, 2],
        "observed_source_guest_result": source_result,
        "canonical_one_pair_sha256": paired,
        "anonymous_first_boot_sram_present": legacy_bootstrap is not None,
        "anonymous_bootstrap_bytes_unchanged_by_all_named_games": True,
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
    print("PASS: native-created Mike/Martin -> played original 2P source match "
          "-> exactly one paired record -> both fresh native Records views. "
          "No independent original parity or physical pad claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
