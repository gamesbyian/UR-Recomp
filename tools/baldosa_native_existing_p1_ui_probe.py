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
import os
from pathlib import Path
import subprocess
import time

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
        "UR_BALDOSA_MODERN_ROOT existing_p1_queued=1 activation=next_process",
        "UR_BALDOSA_MODERN_ROOT existing_p1_stale_race_blocked=1",
        f"UR_BALDOSA_NATIVE_PROFILE NEXT_BOOT_COMMITTED from={current} "
        f"to={next_id} original_raw_typed_saved=1",
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
        "UR-BALDOSA-SAVE-FAILED:",
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

    # Independent adversarial management process wins the next-boot
    # selector AFTER the game's authentic source raw+typed checkpoint and
    # BEFORE its queued P1 change. This is NOT a synthetic dirty-save
    # refusal: old racer data is saved and should be reported as saved,
    # while the stale second selector transaction must refuse as EXIT 9.
    denied = out / "postsave_selector_conflict"
    denied.mkdir()
    gate = denied / "external-selector-committed.ready"
    route = denied / "stock-route.txt"
    route.write_text("turbo on\nwait 900\nquit\n", encoding="ascii")
    config = denied / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    source_log_path = denied / "original-game.log"
    witness = denied / "fault-bytes"
    witness.mkdir()
    canonical = {
        "mike-raw": user / "saves/profile-mike/save.srm",
        "mike-typed": user / "saves/profile-mike/host-profile.txt",
        "andrew-raw": user / "saves/profile-andrew/save.srm",
        "andrew-typed": user / "saves/profile-andrew/host-profile.txt",
        "selector": selector, "catalog": roster,
    }
    receipts = {}
    def snapshot(stage: str) -> dict[str, bytes]:
        state = {}
        for key, path in canonical.items():
            if path.is_symlink() or not path.is_file():
                raise ValueError("Postsave source authority missing or redirected")
            value = path.read_bytes()
            if key.endswith("-raw") and len(value) != 8192:
                raise ValueError("Original source SRAM wrong size")
            state[key] = value
            member = f"{stage}.{key}.bin"
            (witness / member).write_bytes(value)
            receipts[member] = {"sha256": hashlib.sha256(value).hexdigest(),
                                "bytes": len(value)}
        return state
    before_fault = snapshot("before")
    actor_log = ""
    old_before = profile_bytes(user, "mike")
    old_roster = roster.read_bytes()
    old_andrew = profile_bytes(user, "andrew")
    env = {**os.environ,
           "SNESRECOMP_USER_DATA_DIR": str(user),
           "UR_EXECUTION_MODE": "modern",
           "UR_BALDOSA_MODERN_ROOT": "1",
           "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "6",
           "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
           "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
           "UR_BALDOSA_MODERN_INPUT": "1",
           "UR_BALDOSA_PAUSE_SMOKE": "0",
           "UR_BALDOSA_QA_POSTSAVE_NEXT_BOOT_GATE": str(gate),
           "SDL_VIDEODRIVER": video,
           "SDL_AUDIODRIVER": "dummy"}
    with source_log_path.open("wb") as log_fp:
        proc = subprocess.Popen(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(route), str(rom)],
            cwd=denied, env=env, stdout=log_fp, stderr=subprocess.STDOUT)
        try:
            marker = ("UR_BALDOSA_NATIVE_PROFILE QA_POSTSAVE_NEXT_BOOT_GATE "
                      "source_raw_typed_saved=1 selector_not_yet_committed=1")
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if marker in source_log_path.read_text(
                        encoding="utf-8", errors="replace"):
                    break
                if proc.poll() is not None:
                    raise ValueError("Original guest exited before post-save gate")
                time.sleep(0.025)
            else:
                raise ValueError("Original source guest did not reach post-save gate")
            # The original guest has written its OWN stock SRAM and typed
            # profile via production RtlWriteSram/CAS. Independently verify
            # this producer's canonical 8192 SRAM before any outside change.
            verify_native_save_codec(fixture, user, timeout, profile="mike")
            changed_saved_raw = profile_bytes(user, "mike")
            source_saved_fault = snapshot("after-source-save")
            if selector.read_bytes() != selector_before:
                raise ValueError("Queued switch wrote selector before source save")
            external = subprocess.run(
                [str(fixture), str(user), "mike", "andrew",
                 "--select-existing-next-boot"],
                capture_output=True, text=True, timeout=timeout)
            actor_log = external.stdout + "\n" + external.stderr
            (denied / "external-selector-actor.log").write_text(
                actor_log, encoding="utf-8")
            if (external.returncode != 0 or
                "existing_next_boot=andrew previous=mike" not in actor_log):
                raise ValueError("Independent canonical selector transaction failed")
            outside_won_fault = snapshot("after-external-selector")
            gate.write_text("external selector committed\n", encoding="ascii")
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Original guest blocked after selector gate") from exc
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=30)
    final_fault = snapshot("after-original-refusal")
    if (not all(before_fault[k] == source_saved_fault[k]
                for k in ("andrew-raw", "andrew-typed", "selector", "catalog")) or
        not all(source_saved_fault[k] == outside_won_fault[k]
                for k in canonical if k != "selector") or
        outside_won_fault["selector"] == source_saved_fault["selector"] or
        final_fault != outside_won_fault):
        raise ValueError("Postsave selector race mutated canonical source bytes")
    if len(receipts) != 24:
        raise ValueError("Incomplete 24-object post-save binary witness")
    (witness / "hashes.json").write_text(json.dumps({
        "schema": "ur-win32-postsave-selector-snapshots/1",
        "read_only_source_snapshots": receipts, "independent_qa_credit": 0,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    saved_source_log = source_log_path.read_text(
        encoding="utf-8", errors="replace")
    if (proc.returncode != 9 or
        saved_source_log.count("existing_p1_queued=1") != 1 or
        saved_source_log.count("CHECKPOINT profile=mike status=") != 1 or
        not ("CHECKPOINT profile=mike status=committed" in saved_source_log or
             "CHECKPOINT profile=mike status=unchanged" in saved_source_log) or
        marker not in saved_source_log or
        "NEXT_BOOT_COMMIT_FAILED from=mike to=andrew" not in saved_source_log or
        "saved_old_racer=1" not in saved_source_log or
        "UR-BALDOSA-SWITCH-FAILED: Current racer save completed" not in saved_source_log or
        "UR-BALDOSA-SAVE-FAILED:" in saved_source_log or
        "NEXT_BOOT_COMMITTED" in saved_source_log):
        raise ValueError("Real post-save selector race did not report saved-old exit9")
    if not (saved_source_log.index("CHECKPOINT profile=mike status=") <
            saved_source_log.index(marker) <
            saved_source_log.index("NEXT_BOOT_COMMIT_FAILED")):
        raise ValueError("Source raw+typed save was not before external selector")
    if (selector.read_bytes() == selector_before or
        roster.read_bytes() != old_roster or
        profile_bytes(user, "mike") != changed_saved_raw or
        profile_bytes(user, "andrew") != old_andrew or
        list(user.rglob("native-sram-checkpoint.pending"))):
        raise ValueError("Post-save selector race corrupted a profile or journal")
    verify_native_save_codec(fixture, user, timeout, profile="mike")
    verify_native_save_codec(fixture, user, timeout, profile="andrew")
    (denied / "result.json").write_text(json.dumps({
        "scope": "two-real-win32-process-postsave-selector-conflict",
        "authentic_source_guest_queued_p1_switch": True,
        "original_raw_typed_checkpoint_before_external_selector": True,
        "external_actor_used_original_canonical_product_transaction": True,
        "source_native_process_exit_code": proc.returncode,
        "old_8192_sram_before_sha256": hashlib.sha256(old_before).hexdigest(),
        "old_8192_sram_saved_sha256": hashlib.sha256(changed_saved_raw).hexdigest(),
        "old_sram_and_typed_codec_revalidated": True,
        "alternate_racer_raw_unchanged": True,
        "journal_retired": True,
        "player_facing_save_success_switch_failure": True,
        "source_exact_binary_witness_count": len(receipts),
        "physical_hardware_or_os_power_cut": False,
        "independent_QA_credit": 0,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    return {
        "scope": "native-p1-existing-profile-selector-real-controller-root-next-boot",
        "created_in_actual_frontend": ["mike", "andrew"],
        "controller_root_p1_switches": ["mike->andrew", "andrew->mike"],
        "fresh_native_boot_restored_mike": True,
        "real_two_process_postsave_selector_conflict_returned_distinct_exit9": True,
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
