#!/usr/bin/env python3
"""Real extracted Windows CMD T recovery of an untrusted corrupt SRAM intent.

Product-owned original-process test; NOT a human keypress, true torn write,
electrical outage, or independent QA acceptance. All original bytes retained.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from assemble_baldosa_windows_candidate import ROM, USA_SHA256
from baldosa_win32_interactive_recovery_q import digest, snapshot
from baldosa_win32_interactive_recovery_rt import (
    launch_until_first_frame, retain, stock_sram,
)


def main_case(launcher: Path, rom: Path, fixture: Path, seed: Path,
              root: Path, timeout: int) -> dict:
    if os.name != "nt" or root.exists() or not all(
        p.is_file() and not p.is_symlink()
        for p in (launcher, rom, fixture, seed)
    ) or digest(rom.read_bytes()) != USA_SHA256:
        raise ValueError("Fresh real Win32 source/USA-ROM input required")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("Original extracted ROM-free candidate already has ROM")
    root.mkdir(parents=True)
    try:
        shutil.copyfile(rom, installed)
        if digest(installed.read_bytes()) != USA_SHA256:
            raise ValueError("Temporary pinned USA game ROM mismatched")
        user = root / "Original Player With Spaces"
        user.mkdir()
        setup = subprocess.run(
            [str(fixture), str(user), str(seed)],
            capture_output=True, text=True, timeout=timeout, check=True)
        (root / "fixture.log").write_text(
            setup.stdout + "\n" + setup.stderr, encoding="utf-8")
        old = snapshot(user)
        if stock_sram(old["typed"]) != old["raw"] or len(old["raw"]) != 8192:
            raise ValueError("Expected canonical original guest stock SRAM")
        profile = user / "saves/profile-native-ci-rider"
        raw = profile / "save.srm"
        pending = profile / "native-sram-checkpoint.pending"
        if pending.exists() or pending.is_symlink():
            raise ValueError("Fixture already has pending intent")
        damaged = bytearray(old["raw"])
        damaged[256] ^= 1
        raw.write_bytes(damaged)
        untrusted = b"INVALID\x00original-guest\xff"
        pending.write_bytes(untrusted)
        before = snapshot(user)
        if (before["raw"] == old["raw"] or
            any(before[k] != old[k] for k in ("typed", "selector", "catalog")) or
            pending.read_bytes() != untrusted):
            raise ValueError("Did not prepare exact bounded corrupt-intent input")
        byte_root = root / "source-bytes"
        receipts: dict[str, dict] = {}
        retain(byte_root, "before", before, receipts)
        (byte_root / "untrusted-before.bin").write_bytes(untrusted)
        receipts["untrusted-before.bin"] = {
            "bytes": len(untrusted), "sha256": digest(untrusted)}
        transcript, injected = launch_until_first_frame(
            launcher, user, root, "interactive-bad-intent-T",
            key="T", timeout=timeout)
        after = snapshot(user)
        retain(byte_root, "after", after, receipts)
        if (not injected or after != old or pending.exists() or
            pending.is_symlink() or stock_sram(after["typed"]) != after["raw"]):
            raise ValueError("Original CMD did not restore committed typed SRAM")
        manual = list(profile.glob("native-sram-manual-archive-*.bin"))
        suspect = list(profile.glob("native-sram-untrusted-intent-*.bin"))
        if (len(manual) != 1 or len(suspect) != 1 or
            manual[0].is_symlink() or suspect[0].is_symlink()):
            raise ValueError("Exactly two real archive-first receipts required")
        manual_bytes = manual[0].read_bytes()
        suspect_bytes = suspect[0].read_bytes()
        expected_manual = (
            b"UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n" +
            str(len(before["typed"])).encode("ascii") +
            b"\n1\n8192\n" + before["typed"] + before["raw"])
        expected_suspect = (
            b"UR-BALDOSA-UNTRUSTED-SRAM-INTENT/1\n" +
            str(len(untrusted)).encode("ascii") + b"\n" + untrusted)
        if (manual_bytes != expected_manual or
            suspect_bytes != expected_suspect):
            raise ValueError("Original Windows typed rollback lost source bytes")
        for name, content in (
            ("manual-archive.bin", manual_bytes),
            ("untrusted-archive.bin", suspect_bytes),
        ):
            (byte_root / name).write_bytes(content)
            receipts[name] = {"bytes": len(content), "sha256": digest(content)}
        for cold in (1, 2):
            launch_until_first_frame(
                launcher, user, root, f"cold-{cold}", key=None,
                timeout=timeout)
            now = snapshot(user)
            retain(byte_root, f"cold{cold}", now, receipts)
            if (now != old or manual[0].read_bytes() != manual_bytes or
                suspect[0].read_bytes() != suspect_bytes or
                pending.exists() or pending.is_symlink()):
                raise ValueError("Original cold Windows game lost archive/authority")
        if (list(user.rglob("*.urrun")) or list(user.rglob("*.urmatch")) or
            list(user.rglob("native-sram-checkpoint.pending"))):
            raise ValueError("Recovery manufactured an event or replay authority")
        result = {
            "schema": "ur-win32-interactive-malformed-intent-typed/1",
            "candidate_cmd_sha256": digest(launcher.read_bytes()),
            "stock_seed_sha256": digest(seed.read_bytes()),
            "genuine_original_windows_cmd": True,
            "console_T_key_injected_not_human": injected,
            "bad_intent_never_promoted": True,
            "archive_first_original_raw_typed_and_opaque_intent": True,
            "committed_typed_restored_exactly": True,
            "both_original_cold_game_processes_idempotent": True,
            "canonical_selector_and_catalog_unchanged": True,
            "raw_guest_delta_bytes": sum(x != y for x, y in
                                         zip(old["raw"], before["raw"])),
            "source_bytes": receipts,
            "physical_human_or_power_cut": False,
            "independent_release_gate_credit": 0,
        }
        (root / "result.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        return result
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
    print(json.dumps(main_case(
        a.launcher.resolve(), a.rom.resolve(), a.fixture.resolve(),
        a.seed.resolve(), a.out.resolve(), a.timeout), sort_keys=True))


if __name__ == "__main__":
    main()
