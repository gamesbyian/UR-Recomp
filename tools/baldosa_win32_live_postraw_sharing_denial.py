#!/usr/bin/env python3
"""Actual Win32 sharing-denied typed publication AFTER original native raw SRAM.

This owns no guest code, no save codec and no independent QA result. A gated
source-native post-save callback keeps the canonical selector/catalog/profile
leases alive while another process holds a real Win32 no-delete-share handle
on canonical typed metadata. The original game attempts its normal typed CAS. No synthetic write
failure, cloned crash image or second save writer is involved.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
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
    gate = out / "release-real-win32-sharing-denied-typed-cas.ready"
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
    # FILE_SHARE_READ permits the product's old-state CAS verification, but
    # refuses the DELETE access needed for MoveFileExW to atomically replace
    # the typed destination. Confirm that very OS refusal on disposable
    # siblings before applying the same kernel condition to the live profile.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
        wintypes.HANDLE,
    )
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel.CloseHandle.restype = wintypes.BOOL
    invalid = ctypes.c_void_p(-1).value
    def hold_read_without_delete_share(path: Path) -> int:
        handle = kernel.CreateFileW(
            str(path), 0x80000000, 0x00000001, None, 3, 0x80, None)
        if handle in (None, invalid):
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(script), str(rom)]
    armed_marker = ("UR_BALDOSA_NATIVE_PROFILE QA_POSTRAW_TYPED_GATE "
                    "native_raw_written=1 typed_not_attempted=1")
    held_typed_handle: int | None = None
    replace_probe_winerror: int | None = None
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
            # Actively demonstrate the kernel denies an actual same-folder
            # atomic REPLACE when a read-only sharing lease excludes DELETE.
            # Neither probe is a real SRAM/profile file or authority.
            scratch_old = profile / "_typed_replace_probe_old_not_a_save.txt"
            scratch_new = profile / "_typed_replace_probe_new_not_a_save.txt"
            scratch_old.write_bytes(b"existing typed-style destination")
            scratch_new.write_bytes(b"new staged payload")
            disposable_lease = hold_read_without_delete_share(scratch_old)
            try:
                try:
                    os.replace(scratch_new, scratch_old)
                except OSError as exc:
                    replace_probe_winerror = getattr(exc, "winerror", None)
                    if replace_probe_winerror not in (5, 32):
                        raise ValueError(
                            "Wrong Win32 error for denied atomic replace: " +
                            repr(exc)) from exc
                else:
                    raise ValueError(
                        "Win32 kernel allowed replace under no-delete-share lease")
            finally:
                if not kernel.CloseHandle(disposable_lease):
                    raise ctypes.WinError(ctypes.get_last_error())
                scratch_old.unlink(missing_ok=True)
                scratch_new.unlink(missing_ok=True)
            # The real original game remains alive with its selector, roster
            # and profile OS mutex handles. The existing typed state MUST
            # stay readable for optimistic compare; only replacement is
            # refused by the OS.
            held_typed_handle = hold_read_without_delete_share(
                files["typed-profile"])
            if files["typed-profile"].read_bytes() != mid["typed-profile"]:
                raise ValueError("Sharing deny accidentally hid typed read authority")
            gate.write_text("real-win32-delete-share-denied\n", encoding="ascii")
            original.wait(timeout=timeout)
            return_code = original.returncode
            source_log = log_path.read_text(encoding="utf-8", errors="replace")
            after = read_all()
        finally:
            if original.poll() is None:
                original.kill()
                original.wait(timeout=30)
            if held_typed_handle is not None:
                if not kernel.CloseHandle(held_typed_handle):
                    raise ctypes.WinError(ctypes.get_last_error())
    # Preserve immutable CI-owned original source bytes even if the strict
    # live OS-sharing-denial witness fails. This receipt is explicitly
    # PREVALIDATION: no valid publication or release acceptance is implied.
    evidence_root = out / "fault-bytes"
    evidence_root.mkdir(exist_ok=True)
    preliminary = {}
    for stage, snapshot in (("before", before),
                            ("native-postraw", mid),
                            ("denied", after)):
        if snapshot is None:
            continue
        for key, raw_bytes in snapshot.items():
            member = key + "." + stage + ".bin"
            (evidence_root / member).write_bytes(raw_bytes)
            preliminary[member] = {
                "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "bytes": len(raw_bytes),
            }
    if crash_intent is not None:
        member = "intent.native-postraw.bin"
        (evidence_root / member).write_bytes(crash_intent)
        preliminary[member] = {
            "sha256": hashlib.sha256(crash_intent).hexdigest(),
            "bytes": len(crash_intent),
        }
    (evidence_root / "prevalidation-receipt.json").write_text(
        json.dumps({
            "schema": "ur-win32-source-sharing-prevalidation/1",
            "no_validated_save_failure_yet": True,
            "kernel_replace_probe_winerror": replace_probe_winerror,
            "native_exit_code": return_code,
            "exact_source_byte_members": preliminary,
            "qa_gate_credit": 0,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if (return_code != 8 or
        "UR-BALDOSA-SAVE-FAILED: Native save could not complete." not in source_log or
        replace_probe_winerror not in (5, 32) or
        mid is None or after is None or crash_intent is None or
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
            "Live native game did not fail its Win32 sharing-denied typed CAS "
            f"without modifying canonical bytes rc={return_code} "
            f"tail={source_log[-1800:]}")
    if (list(user_root.rglob("*.urrun")) or
        list(user_root.rglob("*.urmatch")) or
        list(user_root.rglob("*.urghost"))):
        raise ValueError("Denied original typed publication fabricated earned Records")
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
        raise ValueError("Win32 handle release did not permit source guest reconciliation")
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
    witness.mkdir(exist_ok=True)
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
        "actual_OS_sharing_denied_live_typed_publication": True,
        "kernel_replace_probe_winerror": replace_probe_winerror,
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
