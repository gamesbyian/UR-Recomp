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
from pathlib import Path

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


def require_p2_creation(log: str) -> None:
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=mike root=saves/profile-mike",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT second_racer_opened=1 preset=1 "
        "activation=next_process",
        "UR_BALDOSA_NATIVE_SECOND_RACER status=0 preset=1 id=andrew "
        "activation=next_process",
        "UR_BALDOSA_MODERN_ROOT second_racer_created=1 "
        "activation=next_process",
    )
    offsets = []
    for stage in stages:
        if log.count(stage) != 1:
            raise ValueError("No unique canonical P2 creation stage: " + stage)
        offsets.append(log.index(stage))
    if offsets != sorted(offsets):
        raise ValueError("Second racer published out of guest/canonical order")
    forbidden = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=andrew",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("exe", "rom", "fixture", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    paths = [getattr(args, name).resolve()
             for name in ("exe", "rom", "fixture", "out")]
    report = run(*paths, timeout=args.timeout, video=args.video)
    (paths[-1] / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print("PASS: real native P1 creation, named P1 adds private P2, "
          "a third native game confirms both genuine seats and source 2P GO. "
          "No result/parity/physical pad release credit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
