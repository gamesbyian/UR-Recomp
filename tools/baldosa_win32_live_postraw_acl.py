#!/usr/bin/env python3
"""Actual Windows NTFS denied typed publication AFTER original native raw SRAM.

This owns no guest code, no save codec and no independent QA result. A gated
source-native post-save callback keeps the canonical selector/catalog/profile
leases alive while a distinct host process installs a real NTFS DACL. The
original native game then attempts its normal typed CAS. No synthetic write
failure, cloned crash image or second save writer is involved.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from baldosa_windows_native_pause_route import verify_named_profile_boot_bytes


def run_native_win32_live_postraw_typed_denial(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    if os.name != "nt":
        raise ValueError("Live original SRAM typed-denial requires real Win32")
    out = root / "native_real_win32_live_postraw_typed_denial"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Exact Original Live SRAM OS Fault With Spaces"
    user_root.mkdir()
    subprocess.run([str(fixture), str(user_root), str(seed)],
                   cwd=out, capture_output=True, text=True,
                   check=True, timeout=timeout)
    profile = user_root / "saves/profile-native-ci-rider"
    files = {
        "raw-sram": profile / "save.srm",
        "typed-profile": profile / "host-profile.txt",
        "selector": user_root / "host-state-v1.txt",
        "roster": user_root / "profiles-v1.txt",
    }
    def read_all() -> dict[str, bytes]:
        for path in files.values():
            if path.is_symlink() or not path.is_file():
                raise ValueError("Native source canonical file missing or redirected")
        return {label: path.read_bytes() for label, path in files.items()}

    before = read_all()
    if before["raw-sram"] != seed.read_bytes() or len(before["raw-sram"]) != 8192:
        raise ValueError("Actual source guest seed is not exact 8192 SRAM")
    pending = profile / "native-sram-checkpoint.pending"
    if pending.exists():
        raise ValueError("Fault seed already has pending native intent")
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    gate = out / "release-real-ntfs-denied-typed-cas.ready"
    log_path = out / "live-original-after-raw-denied-typed.log"
    env = os.environ.copy()
    for key in ("UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE",
                "UR_BALDOSA_QA_LEGACY_UNJOURNALED_CRASH",
                "UR_BALDOSA_QA_CRASH_AFTER_INTENT_BEFORE_RAW",
                "UR_BALDOSA_QA_CRASH_AFTER_TYPED_PROFILE_COMMIT",
                "UR_BALDOSA_RECOVERY_ACTION",
                "UR_BALDOSA_RECOVERY_PROFILE_ID",
                "UR_BALDOSA_PAUSE_QUIT_CONFLICT_GATE"):
        env.pop(key, None)
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "UR_BALDOSA_PAUSE_SMOKE": "1",
        "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1",
        "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "1952",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1",
        "UR_BALDOSA_PAUSE_QUIT_SMOKE": "1",
        "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "0",
        "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
        "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
        "UR_BALDOSA_QA_POSTRAW_TYPED_DENIAL_GATE": str(gate),
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    sid_query = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"], check=True,
        capture_output=True, text=True, timeout=10)
    values = list(csv.reader(sid_query.stdout.splitlines()))
    if len(values) != 1 or not values[0] or not values[0][-1].startswith("S-1-5-"):
        raise ValueError("Current actual Windows user SID could not be identified")
    sid = values[0][-1]
    def acl(*options: str) -> None:
        operation = subprocess.run(
            ["icacls", str(profile), *options, "/T"], capture_output=True,
            text=True, timeout=30)
        if operation.returncode or "Successfully processed" not in operation.stdout:
            raise ValueError("Real Win32 directory ACL operation refused: " +
                             (operation.stdout + operation.stderr)[-1500:])
    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(script), str(rom)]
    armed_marker = ("UR_BALDOSA_NATIVE_PROFILE QA_POSTRAW_TYPED_GATE "
                    "native_raw_written=1 typed_not_attempted=1")
    denied = False
    mid: dict[str, bytes] | None = None
    after: dict[str, bytes] | None = None
    crash_intent: bytes | None = None
    source_log = ""
    return_code: int | None = None
    with log_path.open("wb") as sink:
        original = subprocess.Popen(
            command, cwd=out, env=env, stdout=sink, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                source_log = log_path.read_text(encoding="utf-8", errors="replace")
                if armed_marker in source_log:
                    break
                if original.poll() is not None:
                    raise ValueError("Original game exited before genuine raw save: " +
                                     source_log[-1400:])
                time.sleep(0.02)
            else:
                raise TimeoutError("Original game never reached postraw typed gate")
            if original.poll() is not None or source_log.count(armed_marker) != 1:
                raise ValueError("Original source postraw pause has no unique live process")
            mid = read_all()
            if (len(mid["raw-sram"]) != 8192 or
                mid["raw-sram"] == before["raw-sram"] or
                any(mid[key] != before[key]
                    for key in ("typed-profile", "selector", "roster")) or
                not pending.is_file()):
                raise ValueError("Original SRAM changed no bytes or published metadata early")
            crash_intent = pending.read_bytes()
            if len(crash_intent) < 8192:
                raise ValueError("Source guest reached postraw without durable intent")
            # The actual source guest is still alive holding all three OS
            # leases. These are real NTFS access rights, not test overrides.
            acl("/deny", f"*{sid}:(WD,AD,WEA,WA,DE,DC)")
            denied = True
            probe = profile / "_actual_ntfs_write_deny_NOT_a_save.txt"
            try:
                with probe.open("xb") as fp:
                    fp.write(b"not source SRAM")
            except PermissionError:
                if probe.exists():
                    raise ValueError("ACL denied probe write but created a file")
            else:
                probe.unlink(missing_ok=True)
                raise ValueError("OS DACL did not actually deny file creation")
            gate.write_text("actual-ntfs-write-denied\n", encoding="ascii")
            original.wait(timeout=timeout)
            return_code = original.returncode
            source_log = log_path.read_text(encoding="utf-8", errors="replace")
            after = read_all()
        finally:
            if original.poll() is None:
                original.kill()
                original.wait(timeout=30)
            if denied:
                acl("/remove:d", f"*{sid}")
    if (mid is None or after is None or crash_intent is None or
        after != mid or not pending.is_file() or
        pending.read_bytes() != crash_intent or
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider status=io_error"
        not in source_log or
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider status=committed"
        in source_log or
        source_log.count(armed_marker) != 1 or
        source_log.count("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 "
                         "live_race=1 modern_session=1 physical_sdl=1") != 1 or
        "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1 paused=1 guest_steps=0"
        not in source_log):
        raise ValueError(
            "Live native game did not fail its actual OS-denied typed CAS "
            f"without modifying canonical bytes rc={return_code} "
            f"tail={source_log[-1800:]}")
    if (list(user_root.rglob("*.urrun")) or
        list(user_root.rglob("*.urmatch")) or
        list(user_root.rglob("*.urghost"))):
        raise ValueError("Denied original save fabricated earned Records")
    clear = env.copy()
    for flag in (
        "UR_BALDOSA_QA_POSTRAW_TYPED_DENIAL_GATE",
        "UR_BALDOSA_PAUSE_SMOKE", "UR_BALDOSA_PAUSE_REQUIRE_RACE",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE",
        "UR_BALDOSA_PAUSE_QUIT_SMOKE"):
        clear.pop(flag, None)
    short = out / "short-cold.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    cold_command = [str(exe), "--no-launcher", "--config", str(config),
                    "--script", str(short), str(rom)]
    cold = subprocess.run(
        cold_command, cwd=out, env=clear, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    cold_log = cold.stdout + "\n" + cold.stderr
    (out / "first-clean-cold-replay.log").write_text(cold_log, encoding="utf-8")
    if (cold.returncode or
        cold_log.count("UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED "
                       "exact_staged_guest_sram=1 no_records=1") != 1 or
        "UR_BALDOSA_NATIVE_PROFILE REJECTED" in cold_log):
        raise ValueError("NTFS access restoration failed real guest reconciliation")
    verify_named_profile_boot_bytes(cold_log, mid["raw-sram"])
    recovered = read_all()
    archives = list(profile.glob("native-sram-recovered-*.txt"))
    if (recovered["raw-sram"] != mid["raw-sram"] or
        recovered["typed-profile"] == mid["typed-profile"] or
        any(recovered[key] != mid[key] for key in ("selector", "roster")) or
        pending.exists() or len(archives) != 1 or
        archives[0].read_bytes() != crash_intent):
        raise ValueError("Cold reconciliation did not exact-replay original SRAM")
    again = subprocess.run(
        cold_command, cwd=out, env=clear, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    again_log = again.stdout + "\n" + again.stderr
    (out / "second-clean-cold-replay.log").write_text(again_log, encoding="utf-8")
    second = read_all()
    if (again.returncode or
        "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in again_log or
        second != recovered or pending.exists() or
        archives[0].read_bytes() != crash_intent or
        list(user_root.rglob("*.urrun")) or list(user_root.rglob("*.urmatch"))):
        raise ValueError("Second cold guest replay repeated a typed publication")
    verify_named_profile_boot_bytes(again_log, mid["raw-sram"])
    witness = out / "fault-bytes"
    witness.mkdir()
    receipts = {}
    for stage, fileset in (
        ("before", before), ("native-postraw", mid), ("denied", after),
        ("recovered", recovered), ("second-cold", second),
    ):
        for label, content in fileset.items():
            name = label + "." + stage + ".bin"
            (witness / name).write_bytes(content)
            receipts[name] = {"sha256": hashlib.sha256(content).hexdigest(),
                              "bytes": len(content)}
    for name, content in (
        ("intent.native-postraw.bin", crash_intent),
        ("intent.recovered-receipt.bin", archives[0].read_bytes()),
    ):
        (witness / name).write_bytes(content)
        receipts[name] = {"sha256": hashlib.sha256(content).hexdigest(),
                          "bytes": len(content)}
    if len(receipts) != 22:
        raise ValueError("Incomplete 22-object live postraw NTFS evidence")
    (witness / "hashes.json").write_text(
        json.dumps(receipts, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    outcome = {
        "actual_original_win32_race_frame": 1952,
        "original_RtlWriteSram_completed_before_ntfs_denial": True,
        "canonical_selector_catalog_profile_leases_remained_owned": True,
        "actual_OS_DACL_denied_live_typed_checkpoint": True,
        "original_guest_raw_bytes_changed": sum(
            a != b for a, b in zip(before["raw-sram"], mid["raw-sram"])),
        "raw_intent_typed_catalog_unchanged_on_failure": True,
        "source_cold_recovered_original_guest_SRAM": True,
        "second_original_source_boot_idempotent": True,
        "all_source_bytes_and_receipts_retained": 22,
        "physical_hardware_or_power_cut": False,
        "partial_real_disk_write_or_full_volume": False,
        "independent_QA_credit": 0,
        "native_denied_process_return_code": return_code,
    }
    (out / "os-denial-result.json").write_text(
        json.dumps(outcome, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    return outcome
