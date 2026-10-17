#!/usr/bin/env python3
"""Real packaged Windows CMD S refusing invalid targets without mutation.

Separate product-owned negative evidence, never an extension of the fixed
independently verified Q/R/T/S positive artifacts or physical operator QA.
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
from baldosa_win32_interactive_recovery_q import digest
from baldosa_win32_interactive_recovery_rt import forced_stop_tree
from baldosa_win32_interactive_recovery_s import canonical, keep

INVALID_ID = "native-ci-no-such-racer"
CORRUPT_REGISTERED_ID = "native-ci-second"


def spawn(launcher: Path, user: Path, root: Path, label: str):
    transcript = root / (label + ".log")
    wrapper = root / (label + ".cmd")
    wrapper.write_text(
        '@echo off\n'
        f'call "{launcher}" >"{transcript}" 2>&1\n'
        'exit /b %ERRORLEVEL%\n', encoding="utf-8")
    env = os.environ.copy()
    for name in ("UR_BALDOSA_NO_HOLD", "UR_BALDOSA_RECOVERY_ACTION",
                 "UR_BALDOSA_RECOVERY_PROFILE_ID"):
        env.pop(name, None)
    env.update({
        "UR_RECOMP_USER_DATA_ROOT": str(user),
        "SDL_AUDIODRIVER": "dummy", "SDL_VIDEODRIVER": "windows",
    })
    proc = subprocess.Popen(
        ["cmd.exe", "/d", "/c", "call", str(wrapper)],
        cwd=launcher.parent, env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE)
    return proc, transcript


def wait_for(proc, transcript: Path, needle: str, deadline: float) -> str:
    while time.monotonic() < deadline:
        text = (transcript.read_text(encoding="utf-8", errors="replace")
                if transcript.is_file() else "")
        if needle in text:
            return text
        if proc.poll() is not None:
            raise ValueError("Original packaged CMD exited before " + needle +
                             ": " + text[-1800:])
        time.sleep(0.03)
    raise TimeoutError("Original Windows CMD did not reach: " + needle)


def inject(pid: int, root: Path, label: str, argv: list[str]):
    cmd = [sys.executable, str(Path(__file__).with_name(
        "baldosa_win32_interactive_recovery_q.py")), *argv]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                            timeout=25)
    (root / (label + ".injection.log")).write_text(
        f"exit={result.returncode}\n" + result.stdout + "\n" + result.stderr,
        encoding="utf-8")
    if result.returncode:
        raise ValueError("Real console injector refused " + label)


def run(launcher: Path, fixture: Path, seed: Path, root: Path,
        timeout: int, *, corrupt_registered_target: bool = False) -> dict:
    root.mkdir()
    user = root / "Three Original Players With Spaces"
    user.mkdir()
    fixture_logs = []
    for extra in ([], ["--add-second-keep-first"],
                  ["--add-third-keep-first"]):
        result = subprocess.run(
            [str(fixture), str(user), str(seed), *extra],
            check=True, capture_output=True, text=True, timeout=timeout)
        fixture_logs.append(result.stdout + "\n" + result.stderr)
    (root / "fixture.log").write_text("\n---\n".join(fixture_logs),
                                       encoding="utf-8")
    third = user / "saves/profile-native-ci-third/host-profile.txt"
    if not third.is_file() or third.is_symlink():
        raise ValueError("Original third racer fixture is not canonical")
    original_c = third.read_bytes()
    before_damage = canonical(user)
    if len({before_damage[x] for x in ("a-raw", "b-raw", "c-raw")}) != 3:
        raise ValueError("Test requires distinct original SRAM for 3 racers")
    third.unlink()
    raw_a = user / "saves/profile-native-ci-rider/save.srm"
    damaged = bytearray(before_damage["a-raw"])
    damaged[0x0711] ^= 0x35
    raw_a.write_bytes(damaged)
    changed_raws = {"a-raw"}
    target_id = INVALID_ID
    if corrupt_registered_target:
        # B really is catalogued, but independent raw/typed equality is
        # required before any emergency selector publication. Damage one
        # non-signature SRAM byte without changing its typed checkpoint.
        b_raw = user / "saves/profile-native-ci-second/save.srm"
        broken_b = bytearray(before_damage["b-raw"])
        broken_b[0x0699] ^= 0x52
        b_raw.write_bytes(broken_b)
        changed_raws.add("b-raw")
        target_id = CORRUPT_REGISTERED_ID
    before = canonical(user)
    if (any(before[k] == before_damage[k] for k in changed_raws) or
        any(before[k] != before_damage[k]
            for k in before if k not in changed_raws)):
        raise ValueError("Refusal scenario did not isolate intended raw damage")
    if third.exists():
        raise ValueError("Unrelated C damaged typed data remains present")
    evidence = root / "source-bytes"
    evidence.mkdir()
    (evidence / "unrelated-C-original-typed.bin").write_bytes(original_c)
    receipts = {"unrelated-C-original-typed.bin": {
        "bytes": len(original_c), "sha256": digest(original_c)}}
    keep(evidence, "before-invalid-S", before, receipts)

    proc, transcript = spawn(launcher, user, root, "invalid-S")
    try:
        deadline = time.monotonic() + timeout
        wait_for(proc, transcript, "Explicit recovery choice [R/T/S/Q]:",
                 deadline)
        inject(proc.pid, root, "invalid-S-key",
               ["--inject-console-key", "S", str(proc.pid)])
        wait_for(proc, transcript, "Healthy registered profile ID:", deadline)
        inject(proc.pid, root, "invalid-S-profile",
               ["--inject-console-text", str(proc.pid), target_id])
        text = wait_for(proc, transcript, "UR-BALDOSA-RECOVERY-REFUSED:",
                        deadline)
        if (f"next_profile={target_id} completed=0" not in text or
            "UR_BALDOSA_RECOVERY_CHOICE choice=healthy status=3" not in text or
            text.count("Explicit recovery choice [R/T/S/Q]:") != 1 or
            text.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") != 1 or
            text.count("UR-BALDOSA-RECOVERY-REFUSED:") != 1 or
            "UR-BALDOSA-RECOVERY-COMMITTED:" in text or
            "UR_BALDOSA_NATIVE_PROFILE APPLIED" in text or
            "first frame simulated" in text or
            "UR-BALDOSA-FIRST-RACER:" in text):
            raise ValueError("Invalid S request reached a guest or did not refuse")
    finally:
        forced_stop_tree(proc)
    after = canonical(user)
    keep(evidence, "after-invalid-S", after, receipts)
    if after != before or third.exists():
        raise ValueError("Invalid S mutated original A/B/C or selector")
    if list(user.rglob("native-sram-manual-archive-*.bin")) or list(
            user.rglob("native-sram-checkpoint.pending")) or list(
            user.rglob("native-sram-recovered-intent-*.bin")):
        raise ValueError("Invalid S invented a manual repair or pending authority")

    # Fresh source process MUST still reject the damaged A; explicit Q
    # from the same original packaged launcher must exit with code 7.
    proc, transcript = spawn(launcher, user, root, "cold-Q-after-invalid-S")
    try:
        deadline = time.monotonic() + timeout
        wait_for(proc, transcript, "Explicit recovery choice [R/T/S/Q]:",
                 deadline)
        inject(proc.pid, root, "cold-Q-key",
               ["--inject-console-key", "Q", str(proc.pid)])
        proc.wait(timeout=timeout)
        text = transcript.read_text(encoding="utf-8", errors="replace")
        if (proc.returncode != 7 or
            text.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") != 1 or
            text.count("Explicit recovery choice [R/T/S/Q]:") != 1 or
            "UR_BALDOSA_NATIVE_PROFILE APPLIED" in text or
            "first frame simulated" in text or
            "UR-BALDOSA-RECOVERY-COMMITTED:" in text):
            raise ValueError("Next cold original CMD failed to re-refuse A")
    finally:
        forced_stop_tree(proc)
    cold = canonical(user)
    keep(evidence, "cold-Q-after-invalid-S", cold, receipts)
    if cold != before or third.exists():
        raise ValueError("Fresh cold Q mutated previous invalid S data")
    result = {
        "schema": "ur-win32-interactive-original-cmd-invalid-s/1",
        "exact_original_extracted_cmd_sha256": digest(launcher.read_bytes()),
        "original_fixture_sha256": digest(fixture.read_bytes()),
        "original_seed_sha256": digest(seed.read_bytes()),
        "invalid_requested_profile": target_id,
        "registered_target_corrupt_sram": corrupt_registered_target,
        "real_win32_console_keys": ["S", "literal target+Enter", "cold Q"],
        "refusal_before_any_guest_frame": True,
        "second_original_cold_process_rejected_damaged_A_exit_7": True,
        "no_canonical_data_mutated": True,
        "unrelated_C_typed_remained_absent": True,
        "source_bytes_sha256": receipts,
        "human_operator": False,
        "release_gate_credit": 0,
    }
    (root / "invalid-S-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def with_rom(launcher: Path, rom: Path, fixture: Path, seed: Path,
             root: Path, timeout: int, *, corrupt_registered_target: bool = False):
    if (os.name != "nt" or root.exists() or not launcher.is_file() or
        not rom.is_file() or rom.is_symlink() or not fixture.is_file() or
        not seed.is_file() or digest(rom.read_bytes()) != USA_SHA256):
        raise ValueError("Original Win32, new evidence root and authentic ROM needed")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("ROMless candidate already carries user ROM")
    try:
        shutil.copyfile(rom, installed)
        if digest(installed.read_bytes()) != USA_SHA256:
            raise ValueError("Temporary original ROM mismatch")
        return run(launcher, fixture, seed, root, timeout,
                   corrupt_registered_target=corrupt_registered_target)
    finally:
        installed.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    for name in ("launcher", "rom", "fixture", "seed", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--registered-corrupt-target", action="store_true")
    a = ap.parse_args()
    print(json.dumps(with_rom(a.launcher.resolve(), a.rom.resolve(),
                              a.fixture.resolve(), a.seed.resolve(),
                              a.out.resolve(), a.timeout,
                              corrupt_registered_target=a.registered_corrupt_target),
                     sort_keys=True))


if __name__ == "__main__":
    main()
