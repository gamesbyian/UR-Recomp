#!/usr/bin/env python3
"""Controller-only Modern named-P1 switch using actual fresh Win32 guests.

Real frontend creates both stock racers. Two independent X/A root actions
switch the canonical NEXT-boot selector in both directions; no live guest
SRAM switch, synthesized race/Records, or new user-profile serializer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from baldosa_native_first_racer_probe import (
    run_game, verify_creation, verify_boot_sram, verify_native_save_codec,
)
from baldosa_native_second_racer_probe import require_p2_creation
from baldosa_windows_native_pause_route import USA_SHA256, sha256


def require_switch(log: str, current: str, next_id: str) -> None:
    steps = (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={current} ",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        f"UR_BALDOSA_MODERN_ROOT existing_p1_opened=1 "
        f"from={current} to={next_id} activation=next_process",
        f"UR_BALDOSA_NATIVE_P1_SWITCH status=0 from={current} "
        f"to={next_id} activation=next_process",
        "UR_BALDOSA_MODERN_ROOT existing_p1_saved=1 activation=next_process",
        "UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1",
    )
    offsets = []
    for step in steps:
        if log.count(step) != 1:
            raise ValueError("Missing or duplicated actual next-boot UI step: " + step)
        offsets.append(log.index(step))
    if offsets != sorted(offsets):
        raise ValueError("Next P1 selector published before actual native UI approval")
    for rejected in (
        "UR_BALDOSA_MODERN_ROOT stock_entered players=",
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={next_id}",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1",
        "UR_BALDOSA_NATIVE_MATCH CAPTURED=1",
        "UR_BALDOSA_NATIVE_RESULT observed=1",
    ):
        if rejected in log:
            raise ValueError("UI selector hot-swapped guest or minted event: " + rejected)


def profile_bytes(user: Path, name: str) -> bytes:
    f = user / "saves" / ("profile-" + name) / "save.srm"
    if f.is_symlink() or not f.is_file():
        raise ValueError("Missing exact private SRAM")
    data = f.read_bytes()
    if len(data) != 8192 or data[0x0748] != (0 if name == "mike" else 1):
        raise ValueError("Wrong real original rider in named SRAM")
    return data


def run(exe: Path, rom: Path, fixture: Path, out: Path,
        *, timeout: int, video: str) -> dict[str, object]:
    for f in (exe, rom, fixture):
        if f.is_symlink() or not f.is_file():
            raise ValueError("Missing source ROM or pinned native game/codec")
    if sha256(rom) != USA_SHA256:
        raise ValueError("Source guest must be the exact USA retail ROM")
    out.mkdir(parents=True, exist_ok=False)
    user = out / "Switch Two Real Stock Racers"
    user.mkdir()
    first = run_game(
        exe, rom, user, out / "first_creates_mike", "4",
        "turbo on\nwait 900\nquit\n", video, timeout)
    verify_creation(first)
    second = run_game(
        exe, rom, user, out / "named_mike_adds_andrew", "5",
        "turbo on\nwait 900\nquit\n", video, timeout)
    require_p2_creation(second)
    roster = user / "profiles-v1.txt"
    selector = user / "host-state-v1.txt"
    before_catalog = roster.read_bytes()
    selector_before = selector.read_bytes()
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="andrew")
    before_mike = profile_bytes(user, "mike")
    before_andrew = profile_bytes(user, "andrew")

    # Third guest loads Mike; genuine native root X then A chooses Andrew.
    to_andrew = run_game(
        exe, rom, user, out / "mike_switches_to_andrew_next_boot", "6",
        "turbo on\nwait 900\nquit\n", video, timeout)
    verify_boot_sram(to_andrew, before_mike, profile="mike")
    require_switch(to_andrew, "mike", "andrew")
    if selector.read_bytes() == selector_before or roster.read_bytes() != before_catalog:
        raise ValueError("Native P1 switch failed to publish selector-only change")
    if profile_bytes(user, "andrew") != before_andrew:
        raise ValueError("Mike's running guest polluted Andrew's profile")
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="andrew")
    selected_andrew = selector.read_bytes()

    # Fourth genuine guest loads Andrew and explicitly switches BACK via X/A.
    before_andrew_boot = profile_bytes(user, "andrew")
    to_mike = run_game(
        exe, rom, user, out / "andrew_switches_to_mike_next_boot", "6",
        "turbo on\nwait 900\nquit\n", video, timeout)
    verify_boot_sram(to_mike, before_andrew_boot, profile="andrew")
    require_switch(to_mike, "andrew", "mike")
    if (selector.read_bytes() == selected_andrew or
            roster.read_bytes() != before_catalog):
        raise ValueError("Return-to-Mike selection failed or changed catalog")
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="andrew")

    # Fifth fresh guest must actually load Mike again, with full raw SRAM.
    final_mike_sram = profile_bytes(user, "mike")
    fresh_mike = run_game(
        exe, rom, user, out / "fresh_mike_reboot", "1",
        "turbo on\nwait 1800\nquit\n", video, timeout)
    verify_boot_sram(fresh_mike, final_mike_sram, profile="mike")
    if ("UR_BALDOSA_NATIVE_MATCH CAPTURED=1" in fresh_mike or
            "UR_BALDOSA_NATIVE_RUN CAPTURED=1" in fresh_mike or
            roster.read_bytes() != before_catalog):
        raise ValueError("A read-only fresh profile reboot invented a result")
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="andrew")

    return {
        "scope": "native-p1-existing-profile-selector-real-controller-root-next-boot",
        "created_in_actual_frontend": ["mike", "andrew"],
        "controller_root_p1_switches": ["mike->andrew", "andrew->mike"],
        "fresh_native_boot_restored_mike": True,
        "source_guest_hot_swap": False,
        "canonical_catalog_sha256": hashlib.sha256(before_catalog).hexdigest(),
        "physical_gamepad_hardware_accepted": False,
        "paired_guest_result_accepted_by_this_probe": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("exe", "rom", "fixture", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--video", default="windows")
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()
    paths = [getattr(args, key).resolve()
             for key in ("exe", "rom", "fixture", "out")]
    report = run(*paths, timeout=args.timeout, video=args.video)
    (paths[-1] / "report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("PASS: two actual named racers, controller X/A next-boot P1 selector "
          "in both directions and actual fresh guest SRAM boot. "
          "No physical hardware or source result claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
