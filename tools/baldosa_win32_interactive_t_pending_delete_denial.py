#!/usr/bin/env python3
"""Original Win32 CMD T: OS-held journal denies retirement AFTER raw restore.

A distinct bounded producer witness for the operator warning. Real Windows
kernel sharing denial; NOT a power cut, physical torn write, human operator
or independent release acceptance. Never add to canonical R/T/Q envelopes.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from assemble_baldosa_windows_candidate import ROM, USA_SHA256
from baldosa_win32_interactive_recovery_q import digest, snapshot
from baldosa_win32_interactive_recovery_rt import (
    forced_stop_tree, launch_until_first_frame, retain, stock_sram,
)


def hold_pending_delete_denied(pending: Path) -> tuple[object, int]:
    """Keep an actual Win32 read handle without FILE_SHARE_DELETE."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(
        str(pending), 0x80000000, 0x00000001 | 0x00000002,
        None, 3, 0x80, None)
    if handle in (None, ctypes.c_void_p(-1).value):
        raise ctypes.WinError(ctypes.get_last_error())
    return kernel, handle


def original_t_declined(
    launcher: Path, user: Path, root: Path, timeout: int,
) -> tuple[str, bool]:
    """Operate real unmodified CMD with an injected Win32 T console event."""
    name = "locked-pending-T"
    transcript = root / (name + ".log")
    wrapper = root / (name + ".cmd")
    wrapper.write_text(
        "@echo off\n"
        + f'call "{launcher}" >"{transcript}" 2>&1\n'
        + "exit /b %ERRORLEVEL%\n", encoding="utf-8")
    env = os.environ.copy()
    for inherited in (
        "UR_BALDOSA_NO_HOLD", "UR_BALDOSA_RECOVERY_ACTION",
        "UR_BALDOSA_RECOVERY_PROFILE_ID"):
        env.pop(inherited, None)
    env.update({
        "UR_RECOMP_USER_DATA_ROOT": str(user),
        "SDL_AUDIODRIVER": "dummy",
        "SDL_VIDEODRIVER": "windows",
    })
    proc = subprocess.Popen(
        ["cmd.exe", "/d", "/c", "call", str(wrapper)],
        cwd=launcher.parent, env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE)
    injected = False
    refused = False
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            content = (transcript.read_text(
                encoding="utf-8", errors="replace")
                if transcript.is_file() else "")
            if ("Explicit recovery choice [R/T/S/Q]:" in content
                    and not injected):
                injector = subprocess.run(
                    [sys.executable, str(Path(__file__).with_name(
                        "baldosa_win32_interactive_recovery_q.py")),
                     "--inject-console-key", "T", str(proc.pid)],
                    cwd=root, capture_output=True, text=True, timeout=25)
                (root / (name + ".key.log")).write_text(
                    f"exit={injector.returncode}\n" + injector.stdout
                    + "\n" + injector.stderr, encoding="utf-8")
                if injector.returncode != 0:
                    raise ValueError("Actual original console T key refused")
                injected = True
            if "UR-BALDOSA-RECOVERY-REFUSED:" in content:
                refused = True
                break
            if proc.poll() is not None:
                raise ValueError(
                    "Original game ended without safe-refusal warning: "
                    + content[-1600:])
            time.sleep(0.03)
        if not refused:
            raise TimeoutError("Original CMD did not refuse held journal T")
    finally:
        forced_stop_tree(proc)
    text = transcript.read_text(encoding="utf-8", errors="replace")
    if (not injected or not refused or
        text.count("Explicit recovery choice [R/T/S/Q]:") != 1 or
        text.count("UR-BALDOSA-RECOVERY-REFUSED:") != 1 or
        "UR_BALDOSA_RECOVERY_CHOICE choice=typed status=4" not in text or
        "Recovery did not complete; no safe relaunch was authorized"
            not in text or
        "Some files may already have been archived or restored"
            not in text or
        "UR-BALDOSA-RECOVERY-COMMITTED:" in text or
        "first frame simulated" in text):
        raise ValueError("Original T did not report truthful partial failure")
    return text, injected


def run_case(launcher: Path, rom: Path, fixture: Path, seed: Path,
             root: Path, timeout: int) -> dict:
    if os.name != "nt" or root.exists() or not all(
        p.is_file() and not p.is_symlink()
        for p in (launcher, rom, fixture, seed)
    ) or digest(rom.read_bytes()) != USA_SHA256:
        raise ValueError("Fresh exact original Win32/USA ROM required")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("ROM-free candidate already contains a ROM")
    root.mkdir(parents=True)
    try:
        shutil.copyfile(rom, installed)
        if digest(installed.read_bytes()) != USA_SHA256:
            raise ValueError("Temporary USA source ROM verification failed")
        user = root / "Original Player With Spaces"
        user.mkdir()
        fixture_log = subprocess.run(
            [str(fixture), str(user), str(seed)],
            capture_output=True, text=True, check=True, timeout=timeout)
        (root / "fixture.log").write_text(
            fixture_log.stdout + "\n" + fixture_log.stderr,
            encoding="utf-8")
        profile = user / "saves/profile-native-ci-rider"
        raw = profile / "save.srm"
        pending = profile / "native-sram-checkpoint.pending"
        original = snapshot(user)
        if stock_sram(original["typed"]) != original["raw"]:
            raise ValueError("Source typed and raw not initially identical")
        changed = bytearray(original["raw"])
        changed[256] ^= 1
        raw.write_bytes(changed)
        untrusted = b"INVALID\x00held-pending\xff"
        pending.write_bytes(untrusted)
        before = snapshot(user)
        if (before["raw"] != changed or
            any(before[k] != original[k]
                for k in ("selector", "catalog", "typed"))):
            raise ValueError("Failed to construct untrusted source fixture")
        receipts: dict[str, dict] = {}
        folder = root / "source-bytes"
        retain(folder, "before", before, receipts)

        kernel, handle = hold_pending_delete_denied(pending)
        try:
            _, injected = original_t_declined(
                launcher, user, root, timeout)
            failed = snapshot(user)
            retain(folder, "after-denial", failed, receipts)
            if (not injected or failed != original or
                pending.read_bytes() != untrusted):
                raise ValueError(
                    "Denied retirement did not preserve restored raw and pending")
            manual = sorted(profile.glob(
                "native-sram-manual-archive-*.bin"))
            suspect = sorted(profile.glob(
                "native-sram-untrusted-intent-*.bin"))
            if len(manual) != 1 or len(suspect) != 1:
                raise ValueError("Archive-first T did not preserve two receipts")
            old_manual = manual[0].read_bytes()
            old_suspect = suspect[0].read_bytes()
            expected_manual = (
                b"UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n"
                + str(len(before["typed"])).encode("ascii")
                + b"\n1\n8192\n" + before["typed"] + before["raw"])
            expected_suspect = (
                b"UR-BALDOSA-UNTRUSTED-SRAM-INTENT/1\n"
                + str(len(untrusted)).encode("ascii")
                + b"\n" + untrusted)
            if (old_manual != expected_manual or
                old_suspect != expected_suspect):
                raise ValueError("First failed T lost exact original archives")
            for name, data in (
                ("first-manual.bin", old_manual),
                ("untrusted-intent.bin", old_suspect),
                ("pending-denied.bin", untrusted),
            ):
                (folder / name).write_bytes(data)
                receipts[name] = {"bytes": len(data), "sha256": digest(data)}
        finally:
            if not kernel.CloseHandle(ctypes.c_void_p(handle)):
                raise ctypes.WinError(ctypes.get_last_error())

        # A new explicit player decision, never automated by the original
        # launcher, may finish recovery after the OS denial is removed.
        _, confirmed = launch_until_first_frame(
            launcher, user, root, "explicit-T-after-release",
            key="T", timeout=timeout)
        restored = snapshot(user)
        retain(folder, "after-explicit-T", restored, receipts)
        if (not confirmed or restored != original or pending.exists() or
            manual[0].read_bytes() != old_manual or
            suspect[0].read_bytes() != old_suspect or
            len(list(profile.glob("native-sram-manual-archive-*.bin"))) != 2):
            raise ValueError("Fresh explicit T did not clear retained journal")
        newer = [p for p in profile.glob("native-sram-manual-archive-*.bin")
                 if p != manual[0]]
        if len(newer) != 1:
            raise ValueError("Expected separate second archive")
        second = newer[0].read_bytes()
        (folder / "second-manual.bin").write_bytes(second)
        receipts["second-manual.bin"] = {
            "bytes": len(second), "sha256": digest(second)}
        for i in (1, 2):
            launch_until_first_frame(
                launcher, user, root, f"cold-{i}", key=None, timeout=timeout)
            cold = snapshot(user)
            retain(folder, f"cold{i}", cold, receipts)
            if (cold != original or pending.exists() or
                manual[0].read_bytes() != old_manual or
                suspect[0].read_bytes() != old_suspect or
                newer[0].read_bytes() != second):
                raise ValueError("Original cold process mutated recovery receipts")
        if list(user.rglob("*.urrun")) or list(user.rglob("*.urmatch")):
            raise ValueError("Recovery synthesized a run or match")
        result = {
            "schema": "ur-win32-interactive-t-pending-delete-denied/1",
            "candidate_cmd_sha256": digest(launcher.read_bytes()),
            "original_console_t_injected_not_human": injected and confirmed,
            "real_windows_nonshare_delete_handle_held": True,
            "raw_restored_before_pending_retirement_failed": True,
            "original_cmd_refused_without_guest_boot": True,
            "raw_already_restored_despite_exit7": True,
            "archive_first_old_raw_and_typed_and_pending": True,
            "new_explicit_t_after_unlock": True,
            "two_original_windows_cold_guest_boots": True,
            "physical_torn_write_or_power_cut": False,
            "independent_release_gate_credit": 0,
            "original_binary_receipts": receipts,
        }
        (root / "result.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        return result
    finally:
        installed.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("launcher", "rom", "fixture", "seed", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    print(json.dumps(run_case(
        args.launcher.resolve(), args.rom.resolve(),
        args.fixture.resolve(), args.seed.resolve(),
        args.out.resolve(), args.timeout), sort_keys=True))


if __name__ == "__main__":
    main()
