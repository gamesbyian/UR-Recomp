#!/usr/bin/env python3
"""Original Windows CMD S recovery with actual profile-ID text console input.

A source-product-only evidence producer. Three canonical named racers exist:
A is selected and its raw SRAM is damaged; B is healthy; unrelated C has
missing typed metadata. The actual packaged CMD must type S, then B's literal
profile ID, switch only the canonical selector, and boot authentic B twice.
No environment-selected repair, no fake profile, no human release credit.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from assemble_baldosa_windows_candidate import ROM, USA_SHA256
from baldosa_win32_interactive_recovery_q import digest
from baldosa_win32_interactive_recovery_rt import (
    launch_until_first_frame, retain,
)

A = "native-ci-rider"
B = "native-ci-second"
C = "native-ci-third"


def canonical(root: Path) -> dict[str, bytes]:
    files = {
        "selector": root / "host-state-v1.txt",
        "catalog": root / "profiles-v1.txt",
    }
    for label, identity in (("a", A), ("b", B), ("c", C)):
        files[label + "-raw"] = root / ("saves/profile-" + identity) / "save.srm"
        if label != "c":
            files[label + "-typed"] = (
                root / ("saves/profile-" + identity) / "host-profile.txt")
    result = {}
    for name, path in files.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or redirected canonical " + name)
        data = path.read_bytes()
        if name.endswith("-raw") and len(data) != 8192:
            raise ValueError("Incorrect original SRAM length " + name)
        result[name] = data
    if set(result) != {
        "selector", "catalog", "a-raw", "a-typed",
        "b-raw", "b-typed", "c-raw"
    }:
        raise ValueError("Unexpected three-racer authority set")
    return result


def keep(folder: Path, stage: str, files: dict[str, bytes],
         receipts: dict[str, dict]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in sorted(files.items()):
        label = stage + "." + name + ".bin"
        (folder / label).write_bytes(content)
        receipts[label] = {"bytes": len(content), "sha256": digest(content)}


def run(launcher: Path, fixture: Path, seed: Path, root: Path,
        timeout: int) -> dict:
    root.mkdir()
    user = root / "Three Original Players With Spaces"
    user.mkdir()
    fixture_logs = []
    for args in (
        [str(fixture), str(user), str(seed)],
        [str(fixture), str(user), str(seed), "--add-second-keep-first"],
        [str(fixture), str(user), str(seed), "--add-third-keep-first"],
    ):
        step = subprocess.run(args, capture_output=True, text=True,
                              check=True, timeout=timeout)
        fixture_logs.append(step.stdout + "\n" + step.stderr)
    (root / "fixture.log").write_text(
        "\n--- NEXT ORIGINAL CANONICAL FIXTURE ---\n".join(fixture_logs),
        encoding="utf-8")
    third = user / "saves/profile-native-ci-third/host-profile.txt"
    if not third.is_file() or third.is_symlink():
        raise ValueError("Third canonical racer fixture is absent")
    third_content = third.read_bytes()
    if not third_content:
        raise ValueError("Third canonical typed profile is empty")
    byte_root = root / "source-bytes"
    byte_root.mkdir()
    (byte_root / "unrelated-C-original-typed.bin").write_bytes(third_content)
    receipts = {
        "unrelated-C-original-typed.bin": {
            "bytes": len(third_content), "sha256": digest(third_content)}
    }
    first = canonical(user)
    if len({first["a-raw"], first["b-raw"], first["c-raw"]}) != 3:
        raise ValueError("Original named racer SRAMs are not distinct")
    third.unlink()
    source = user / "saves/profile-native-ci-rider/save.srm"
    damaged = bytearray(first["a-raw"])
    damaged[0x0711] ^= 0x35
    source.write_bytes(damaged)
    before = canonical(user)
    if before["a-raw"] == first["a-raw"] or \
       any(before[x] != first[x] for x in before if x != "a-raw") or \
       third.exists():
        raise ValueError("Three-racer synthetic damage was not isolated")
    keep(byte_root, "before-S", before, receipts)
    log, injected = launch_until_first_frame(
        launcher, user, root, "interactive-S", key="S",
        profile_id=B, timeout=timeout)
    after = canonical(user)
    keep(byte_root, "after-S", after, receipts)
    if (not injected or
        log.count("Healthy registered profile ID:") != 1 or
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-second" not in log):
        raise ValueError("Original interactive S did not boot intended racer")
    if any(after[x] != before[x] for x in before if x != "selector"):
        raise ValueError("S changed another racer's raw/typed, third C or catalog")
    if after["selector"] == before["selector"]:
        raise ValueError("S did not publish an authorized next-boot selector")
    if third.exists():
        raise ValueError("S silently recreated unrelated broken C")
    if list(user.rglob("native-sram-manual-archive-*.bin")) or \
       list(user.rglob("native-sram-checkpoint.pending")) or \
       list(user.rglob("native-sram-recovered-intent-*.bin")):
        raise ValueError("S invented repair archives or pending intent")
    for cold in (1, 2):
        boot, _ = launch_until_first_frame(
            launcher, user, root, f"cold-S-{cold}", key=None,
            timeout=timeout)
        if "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-second" not in boot:
            raise ValueError("Cold native process did not load exact B racer")
        current = canonical(user)
        keep(byte_root, f"cold{cold}-S", current, receipts)
        if current != after or third.exists():
            raise ValueError("Cold game changed original A/B/C/selector/catalog")
    result = {
        "schema": "ur-win32-interactive-original-cmd-s/1",
        "original_actual_cmd_sha256": digest(launcher.read_bytes()),
        "original_native_fixture_sha256": digest(fixture.read_bytes()),
        "original_seed_sha256": digest(seed.read_bytes()),
        "actual_win32_console_choice": "S",
        "literal_win32_console_profile_text": B,
        "original_cmd_committed_once": True,
        "original_native_guest_B_cold_boot_count": 2,
        "damaged_A_untouched": True,
        "healthy_B_untouched": True,
        "unrelated_broken_C_untouched": True,
        "only_authorized_selector_changed": True,
        "all_retained_source_bytes": receipts,
        "release_gate_credit": 0,
        "physical_operator": False,
    }
    (root / "interactive-s-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return result


def with_rom(launcher: Path, rom: Path, fixture: Path,
             seed: Path, root: Path, timeout: int) -> dict:
    if os.name != "nt" or root.exists() or not launcher.is_file() or \
       not rom.is_file() or rom.is_symlink() or not fixture.is_file() or \
       not seed.is_file() or digest(rom.read_bytes()) != USA_SHA256:
        raise ValueError("Windows, unused root and verified USA ROM required")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("ROM-free candidate unexpectedly contains a ROM")
    try:
        shutil.copyfile(rom, installed)
        if digest(installed.read_bytes()) != USA_SHA256:
            raise ValueError("Original installed ROM digest mismatch")
        return run(launcher, fixture, seed, root, timeout)
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
    print(json.dumps(with_rom(
        a.launcher.resolve(), a.rom.resolve(),
        a.fixture.resolve(), a.seed.resolve(), a.out.resolve(),
        a.timeout), sort_keys=True))


if __name__ == "__main__":
    main()
