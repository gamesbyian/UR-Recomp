#!/usr/bin/env python3
"""First named P1 creates a second canonical stock racer, then native 2P GO.

Actual Windows native game processes, same pinned guest, original menus.
Source result publication is NOT claimed until another strictly accepted
complete 2P source race and fresh-game paired Records witness exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from baldosa_native_ci_paired_evidence_export import (
    P2_RECOVERY_FOLDER, P2_RECOVERY_STAGES,
    export_ci_native_p2_recovery_stage,
)
from baldosa_native_first_racer_probe import (
    run_game,
    verify_creation,
    verify_native_save_codec,
)
from baldosa_windows_native_pause_route import (
    USA_SHA256,
    native_modern_race_entry_script,
    sha256,
    verify_native_modern_root_log,
)


def require_p2_creation(log: str, *, preset: int = 1) -> None:
    # Production profile factory's *canonical* original stock identities.
    # Default Andrew mode is the merged #1490 route. Martin mode explicitly
    # presses P1 Down within that same actual P2-creation native modal.
    if preset not in (1, 2):
        raise ValueError("Unsupported source-backed P2 creation test preset")
    profile = "andrew" if preset == 1 else "martin"
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 "
        "activation=next_process",
        *([f"UR_BALDOSA_MODERN_ROOT second_racer_preset={preset}"]
          if preset != 1 else []),
        f"UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset={preset} "
        f"id={profile} activation=next_process",
        "UR_BALDOSA_MODERN_ROOT second_racer_created=1 "
        "activation=next_process",
    )
    positions = []
    for stage in stages:
        if log.count(stage) != 1:
            raise ValueError("No unique canonical P2 creation stage: " + stage)
        positions.append(log.index(stage))
    if positions != sorted(positions):
        raise ValueError("Second racer published out of guest/canonical order")
    forbidden = (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile}",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=",
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
    )
    if any(token in log for token in forbidden):
        raise ValueError("Second-racer creation hot-swapped or minted a guest result")


def require_actual_two_seat_go(log: str) -> None:
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
        "root=saves/profile-mike",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
    )
    ordered = []
    for token in stages:
        if log.count(token) != 1:
            raise ValueError("Missing genuine P1/P2 native handoff: " + token)
        ordered.append(log.index(token))
    if ordered != sorted(ordered):
        raise ValueError("Stock guest 2P was entered before both P1/P2 confirmed")
    if ("UR_BALDOSA_MODERN_ROOT join_unavailable=1" in log or
            "UR_BALDOSA_MODERN_ROOT unbound_2p_consented=1" in log or
            "UR_BALDOSA_NATIVE_MATCH CAPTURED=1" in log or
            "UR_BALDOSA_NATIVE_RUN CAPTURED=1" in log):
        raise ValueError("No canonical bound P1/P2 path or forged completed match")


def run(exe: Path, rom: Path, fixture: Path, out: Path,
        *, timeout: int, video: str) -> dict[str, object]:
    for file in (exe, rom, fixture):
        if file.is_symlink() or not file.is_file():
            raise ValueError("Missing/redirected native runner or source ROM")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Actual USA retail source ROM is mandatory")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "Two Fresh Named Players With Spaces"
    user.mkdir()
    log1 = run_game(
        exe, rom, user, out / "first_P1_mike", "4",
        "turbo on\nwait 900\nquit\n", video, timeout)
    verify_creation(log1, preset=0)
    selector = user / "host-state-v1.txt"
    mike_sram = user / "saves/profile-mike/save.srm"
    first_selected = selector.read_bytes()
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    if len(mike_sram.read_bytes()) != 8192:
        raise ValueError("P1 created invalid guest SRAM")

    # Native *named* game two, with user-confirmed X then A/Enter.
    # P2 is always independently seeded; do not copy current P1's SRAM.
    log2 = run_game(
        exe, rom, user, out / "named_P1_adds_P2", "5",
        "turbo on\nwait 900\nquit\n", video, timeout)
    require_p2_creation(log2)
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="andrew")
    andrew_sram = user / "saves/profile-andrew/save.srm"
    if (len(andrew_sram.read_bytes()) != 8192 or
            andrew_sram.read_bytes()[0x0748] != 1):
        raise ValueError("P2 did not privately seed source rider Andrew")
    if selector.read_bytes() != first_selected:
        raise ValueError("P2 creation silently switched current P1 selector")
    roster = user / "profiles-v1.txt"
    if roster.is_symlink() or not roster.is_file():
        raise ValueError("New P2 was not published through canonical catalog")
    before_roster = hashlib.sha256(roster.read_bytes()).hexdigest()
    before_p2 = hashlib.sha256(andrew_sram.read_bytes()).hexdigest()

    # A THIRD native game now sees a verified two-entry roster. Real SDL
    # root controls confirm BOTH seats, then the unchanged original title
    # runs stock 2P racer/tour/track/GO selection.
    log3 = run_game(
        exe, rom, user, out / "fresh_two_seat_source_go", "3",
        native_modern_race_entry_script(2), video, timeout)
    require_actual_two_seat_go(log3)
    verify_native_modern_root_log(log3, 2)
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="andrew")
    if hashlib.sha256(roster.read_bytes()).hexdigest() != before_roster:
        raise ValueError("Source 2P handoff changed canonical roster")
    if hashlib.sha256(andrew_sram.read_bytes()).hexdigest() != before_p2:
        raise ValueError("Source 2P entry wrote the independent P2 save")
    if (user / "runs").exists() and list((user / "runs").rglob("*.urrun")):
        raise ValueError("A mere source GO was misrepresented as a settled match")
    return {
        "scope": "native-real-first-p1-created-p2-then-both-seats-stock-go",
        "P1_source_profile": "mike",
        "P2_source_profile": "andrew",
        "original_p1_selector_unchanged": True,
        "P2_canonical_raw_bytes": 8192,
        "P2_source_rider": 1,
        "third_native_process_two_named_seats_confirmed": True,
        "actual_stock_two_player_go": True,
        "completed_two_player_result": False,
        "reopened_paired_records": False,
        "strict_original_native_event_pass": False,
        "physical_gamepad_acceptance": False,
        "release_gate_credit": 0,
    }



def require_native_created_p1_pad_handler(log: str, mode: str) -> None:
    """Require all and only the native handler receipts for a source UI create."""
    expected = {
        "8": ["X", "A"],
        "9": ["X", "DPAD_DOWN", "A"],
    }
    if mode not in expected:
        raise ValueError("Unrecognized real native creation pad mode")
    observed = re.findall(
        r"(?m)^UR_BALDOSA_MODERN_ROOT "
        rf"synthetic_profile_gamepad mode={mode} button=([A-Z_]+)\r?$",
        log)
    if observed != expected[mode] or (
            log.count("UR_BALDOSA_MODERN_ROOT synthetic_profile_gamepad ")
            != len(expected[mode])):
        raise ValueError("Missing, duplicated or foreign P1 native pad edges")


def require_native_p2_recovery(log: str) -> None:
    """Admission of real gamepad-handler X/Down/A and catalog-only recovery.

    This is a source log consumer, never the authority for real saved bytes.
    The caller separately rehashes P1/P2/catalog and checks original guest GO.
    """
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike "
        "root=saves/profile-mike",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 "
        "activation=next_process",
        "UR_BALDOSA_MODERN_ROOT second_racer_preset=2",
        "UR_BALDOSA_NATIVE_SECOND_RACER_RECOVERY restored=1 "
        "catalog_only=1 p1_unchanged=1 activation=next_process",
        "UR_BALDOSA_NATIVE_SECOND_RACER status=4 preset=2 "
        "id=martin activation=next_process",
        "UR_BALDOSA_MODERN_ROOT second_racer_created=1 activation=next_process",
    )
    offsets = []
    for value in stages:
        if log.count(value) != 1:
            raise ValueError("Missing/duplicate real P2 recovery stage: " + value)
        offsets.append(log.index(value))
    if offsets != sorted(offsets):
        raise ValueError("P2 recovery not ordered after explicit source modal")
    require_native_created_p1_pad_handler(log, "9")
    for forbidden in (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=martin",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=",
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
        "UR_BALDOSA_NATIVE_SECOND_RACER status=0",
    ):
        if forbidden in log:
            raise ValueError("P2 recovery hot-swapped guest or minted new record")


def run_interrupted_catalog_recovery(exe: Path, rom: Path, fixture: Path,
                                     out: Path, *, timeout: int,
                                     video: str) -> dict[str, object]:
    """Actual native UI-created P2, test-only lost final catalog, UI recovery.

    Only the CI-owned single-row catalog is deliberately restored, between
    fully exited native processes. P1 and P2 are genuinely created using
    the shipping gamepad handler; no fixture creates players/results.
    """
    for path in (exe, rom, fixture):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Source native recovery inputs unavailable")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Source native recovery requires exact USA retail ROM")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "Interrupted Native P2 Catalog Test Only"
    user.mkdir()

    first = run_game(
        exe, rom, user, out / "first_native_mike", "8",
        "turbo on\nwait 900\nquit\n", video, timeout)
    verify_creation(first, preset=0)
    require_native_created_p1_pad_handler(first, "8")
    selector = user / "host-state-v1.txt"
    catalog = user / "profiles-v1.txt"
    if any(not p.is_file() or p.is_symlink() for p in (selector, catalog)):
        raise ValueError("P1 canonical selector/catalog absent or redirected")
    one_entry = catalog.read_bytes()
    selected = selector.read_bytes()
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    export_ci_native_p2_recovery_stage(user, out, "after-p1-created")

    created = run_game(
        exe, rom, user, out / "second_native_martin", "9",
        "turbo on\nwait 900\nquit\n", video, timeout)
    require_p2_creation(created, preset=2)
    require_native_created_p1_pad_handler(created, "9")
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="martin")
    if selector.read_bytes() != selected:
        raise ValueError("Native-created P2 changed active P1")
    two_entries = catalog.read_bytes()
    if two_entries == one_entry:
        raise ValueError("Native P2 did not publish catalog before fault cut")
    typed_p2 = user / "saves/profile-martin/host-profile.txt"
    raw_p2 = user / "saves/profile-martin/save.srm"
    mutex_p2 = user / "saves/profile-martin/host-profile.txt.urmutex"
    if any(not p.is_file() or p.is_symlink() for p in
           (typed_p2, raw_p2, mutex_p2)):
        raise ValueError("Actual native P2 staging files missing")
    before_p2 = (typed_p2.read_bytes(), raw_p2.read_bytes(),
                 mutex_p2.read_bytes())
    if len(before_p2[1]) != 8192 or before_p2[1][0x0748] != 2 or before_p2[2]:
        raise ValueError("P2 original rider or canonical CAS lock bytes wrong")
    export_ci_native_p2_recovery_stage(user, out, "after-p2-created")

    # Test-only fault cut: restore the exact catalog from *native game 1*.
    # No player is created, patched or seeded by the fixture; all source
    # executable processes have exited before this reversible catalog cut.
    if user.parent != out or user.name != "Interrupted Native P2 Catalog Test Only":
        raise ValueError("Refuse fault injection outside disposable CI root")
    catalog.write_bytes(one_entry)
    if catalog.read_bytes() != one_entry or selector.read_bytes() != selected:
        raise ValueError("Fault-cut catalog restoration changed selector")
    if (typed_p2.read_bytes(), raw_p2.read_bytes(),
            mutex_p2.read_bytes()) != before_p2:
        raise ValueError("Fault cut changed original native-created P2 bytes")
    export_ci_native_p2_recovery_stage(user, out, "catalog-row-lost")

    recovered = run_game(
        exe, rom, user, out / "third_native_p2_recovers", "9",
        "turbo on\nwait 900\nquit\n", video, timeout)
    require_native_p2_recovery(recovered)
    if catalog.read_bytes() != two_entries or selector.read_bytes() != selected:
        raise ValueError("Native recovery did not publish only original P2 catalog")
    if (typed_p2.read_bytes(), raw_p2.read_bytes(),
            mutex_p2.read_bytes()) != before_p2:
        raise ValueError("Recovery rewrote the actual P2 identity or SRAM")
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="martin")
    export_ci_native_p2_recovery_stage(user, out, "after-p2-recovered")

    joined = run_game(
        exe, rom, user, out / "fourth_native_two_seat_go", "3",
        native_modern_race_entry_script(2), video, timeout)
    require_actual_two_seat_go(joined)
    verify_native_modern_root_log(joined, 2)
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="martin")
    if catalog.read_bytes() != two_entries or selector.read_bytes() != selected:
        raise ValueError("Original stock two-seat guest mutated recovered authority")
    if (typed_p2.read_bytes(), raw_p2.read_bytes(),
            mutex_p2.read_bytes()) != before_p2:
        raise ValueError("Recovered P2 leaked into original native session")
    match_archive = user / "multiplayer-runs"
    if match_archive.exists():
        if match_archive.is_symlink() or not match_archive.is_dir() or any(
                file.name.endswith((".urrun", ".urmatch"))
                for file in match_archive.iterdir()):
            raise ValueError("Recovery/GO published a false paired record")
    one_player_archive = user / "runs"
    if one_player_archive.exists() and (
            one_player_archive.is_symlink() or
            list(one_player_archive.rglob("*.urrun"))):
        raise ValueError("Recovery/GO manufactured an unearned run")
    export_ci_native_p2_recovery_stage(user, out, "after-source-go")
    return {
        "scope": "four-real-windows-games-native-created-martin-recovered-catalog",
        "raw_source_archive": P2_RECOVERY_FOLDER,
        "source_stage_manifest_names": list(P2_RECOVERY_STAGES),
        "fault_cut": "ci-only-restore-original-single-row-catalog",
        "source_created_named_profiles": ["mike", "martin"],
        "first_and_second_real_p1_pad_handler": True,
        "third_real_p1_pad_handler_catalog_only_recovery": True,
        "fourth_real_guest_two_seat_stock_go": True,
        "unmodified_p2_typed_raw_mutex": True,
        "original_p1_selector_unchanged": True,
        "physical_os_crash_proven": False,
        "genuine_completed_match_proven_by_this_route": False,
        "physical_controller_hardware_proven": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("exe", "rom", "fixture", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--recover-interrupted-catalog", action="store_true")
    args = parser.parse_args()
    paths = [getattr(args, name).resolve()
             for name in ("exe", "rom", "fixture", "out")]
    report = (run_interrupted_catalog_recovery if args.recover_interrupted_catalog
              else run)(*paths, timeout=args.timeout, video=args.video)
    (paths[-1] / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    if args.recover_interrupted_catalog:
        print("PASS: actual native UI-created P2, lost-catalog fault-cut, "
              "controller-recovered original P2 catalog and real next-boot "
              "stock 2P GO. No physical OS crash or release credit.")
    else:
        print("PASS: real native P1 creation, named P1 adds private P2, "
              "a third native game confirms both genuine seats and source 2P GO. "
              "No result/parity/physical pad release credit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
