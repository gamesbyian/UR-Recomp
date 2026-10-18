#!/usr/bin/env python3
"""Original packaged Win32 R refusal then explicit T for a SHORT raw SRAM file.

This is a deliberately truncated fixture, NOT an actual torn OS disk write.
Only a new, disposable user-data root is used. One real original Windows CMD
rejects console R without mutation; a separate real CMD accepts console T,
archives the original 513-byte raw and committed typed data, then two fresh
original game processes cold boot the restored profile. No release QA credit.
"""
from __future__ import annotations

import argparse
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


def reject_raw_with_actual_console(launcher: Path, user: Path, root: Path,
                                   timeout: int) -> tuple[str, bool]:
    transcript = root / "reject-short-raw-r.log"
    wrapper = root / "reject-short-raw-r.cmd"
    wrapper.write_text(
        '@echo off\n'
        + f'call "{launcher}" >"{transcript}" 2>&1\n'
        + 'exit /b %ERRORLEVEL%\n', encoding="utf-8")
    env = os.environ.copy()
    for inherited in ("UR_BALDOSA_NO_HOLD", "UR_BALDOSA_RECOVERY_ACTION",
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
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            content = (transcript.read_text(encoding="utf-8", errors="replace")
                       if transcript.is_file() else "")
            if "Explicit recovery choice [R/T/S/Q]:" in content and not injected:
                injector = subprocess.run(
                    [sys.executable, str(
                        Path(__file__).with_name(
                            "baldosa_win32_interactive_recovery_q.py")),
                     "--inject-console-key", "R", str(proc.pid)],
                    cwd=root, capture_output=True, text=True, timeout=25)
                (root / "reject-short-raw-r.key.log").write_text(
                    f"exit={injector.returncode}\n" + injector.stdout +
                    "\n" + injector.stderr, encoding="utf-8")
                if injector.returncode != 0:
                    raise ValueError("Original Windows CMD refused real console R")
                injected = True
            if "UR-BALDOSA-RECOVERY-REFUSED:" in content:
                refused = True
                break
            if proc.poll() is not None:
                raise ValueError("Source game exited without visible refusal: "
                                 + content[-1200:])
            time.sleep(.03)
        if not refused:
            raise TimeoutError("Original packaged game never refused short R")
    finally:
        forced_stop_tree(proc)
    full_log = transcript.read_text(encoding="utf-8", errors="replace")
    if (not injected or not refused or
        full_log.count("Explicit recovery choice [R/T/S/Q]:") != 1 or
        full_log.count("UR-BALDOSA-RECOVERY-REFUSED:") != 1 or
        "UR_BALDOSA_RECOVERY_CHOICE choice=raw status=3" not in full_log or
        "UR-BALDOSA-RECOVERY-COMMITTED:" in full_log or
        "first frame simulated" in full_log):
        raise ValueError("Original R refusal lacked exact fail-closed evidence")
    return full_log, injected


def run_case(launcher: Path, fixture: Path, seed: Path,
             root: Path, timeout: int) -> dict:
    root.mkdir(parents=True)
    user = root / "Original Player With Spaces"
    user.mkdir()
    init = subprocess.run([str(fixture), str(user), str(seed)],
                          capture_output=True, text=True, check=True,
                          timeout=timeout)
    (root / "fixture.log").write_text(init.stdout + "\n" + init.stderr,
                                      encoding="utf-8")
    original = snapshot(user)
    if stock_sram(original["typed"]) != original["raw"]:
        raise ValueError("Source fixture lacked exact typed/raw authority")
    raw = user / "saves/profile-native-ci-rider/save.srm"
    raw.write_bytes(original["raw"][:513])
    before = snapshot(user)
    if (len(before["raw"]) != 513 or
        before["raw"] != original["raw"][:513] or
        any(before[k] != original[k]
            for k in ("selector", "catalog", "typed")) or
        list(user.rglob("native-sram-checkpoint.pending"))):
        raise ValueError("Unjournaled short original raw was not constructed")

    byte_root = root / "source-bytes"
    receipts: dict[str, dict] = {}
    retain(byte_root, "before-r", before, receipts)
    reject_log, injected = reject_raw_with_actual_console(
        launcher, user, root, timeout)
    refused = snapshot(user)
    retain(byte_root, "after-refused-r", refused, receipts)
    if (not injected or refused != before or
        list(user.rglob("native-sram-manual-archive-*")) or
        list(user.rglob("native-sram-checkpoint.pending"))):
        raise ValueError("Refused R mutated or archived original damaged files")
    _, admitted_t = launch_until_first_frame(
        launcher, user, root, "explicit-T", key="T", timeout=timeout)
    restored = snapshot(user)
    retain(byte_root, "after-t", restored, receipts)
    if (not admitted_t or restored["raw"] != original["raw"] or
        any(restored[k] != before[k]
            for k in ("typed", "catalog", "selector")) or
        list(user.rglob("native-sram-checkpoint.pending"))):
        raise ValueError("Original T did not restore exact committed SRAM")
    archives = list(user.rglob("native-sram-manual-archive-*.bin"))
    if len(archives) != 1 or archives[0].is_symlink():
        raise ValueError("Original T did not make one immutable old-source receipt")
    archive = archives[0].read_bytes()
    header = (b"UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n" +
              str(len(before["typed"])).encode("ascii") + b"\n1\n513\n")
    if archive != header + before["typed"] + before["raw"]:
        raise ValueError("Manual receipt does not preserve every short raw byte")
    (byte_root / "manual-t.bin").write_bytes(archive)
    receipts["manual-t.bin"] = {"sha256": digest(archive), "bytes": len(archive)}

    for i in (1, 2):
        launch_until_first_frame(
            launcher, user, root, f"cold-{i}", key=None, timeout=timeout)
        current = snapshot(user)
        retain(byte_root, f"cold{i}", current, receipts)
        if (current != restored or
            list(user.rglob("native-sram-manual-archive-*.bin")) != archives or
            archives[0].read_bytes() != archive):
            raise ValueError("Cold original guest altered T recovery authority")
    result = {
        "schema": "ur-win32-interactive-short-raw-r-reject-t-restore/1",
        "candidate_cmd_sha256": digest(launcher.read_bytes()),
        "original_seed_sha256": digest(seed.read_bytes()),
        "original_console_r_rejected_no_mutation": True,
        "original_console_t_restored_after_archive": True,
        "two_original_windows_cold_guest_boots": True,
        "short_raw_exact_original_bytes": 513,
        "original_guest_torn_write_observed": False,
        "real_power_cut_observed": False,
        "synthetically_truncated_fixture": True,
        "independent_release_gate_credit": 0,
        "original_binary_receipts": receipts,
    }
    (root / "result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    return result


def run_with_rom(launcher: Path, rom: Path, fixture: Path, seed: Path,
                 out: Path, timeout: int) -> dict:
    if (os.name != "nt" or out.exists() or
        not all(p.is_file() and not p.is_symlink()
                for p in (launcher, rom, fixture, seed)) or
        digest(rom.read_bytes()) != USA_SHA256):
        raise ValueError("Requires fresh original Windows ROM/source fixture")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("ROM-free candidate already contains a ROM")
    out.mkdir(parents=True)
    try:
        shutil.copyfile(rom, installed)
        if digest(installed.read_bytes()) != USA_SHA256:
            raise ValueError("Source USA ROM changed during temporary copy")
        return run_case(launcher, fixture, seed, out / "short-raw-rt", timeout)
    finally:
        installed.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--launcher", required=True, type=Path)
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--fixture", required=True, type=Path)
    ap.add_argument("--seed", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--timeout", type=int, default=120)
    a = ap.parse_args()
    print(json.dumps(run_with_rom(
        a.launcher.resolve(), a.rom.resolve(), a.fixture.resolve(),
        a.seed.resolve(), a.out.resolve(), a.timeout), sort_keys=True))


if __name__ == "__main__":
    main()
