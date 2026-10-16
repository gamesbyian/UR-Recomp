#!/usr/bin/env python3
"""Bounded real Win32 crash test of the *original* nominated owner executable.

No new candidate, framework or product code; disposable profile data only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from assemble_baldosa_windows_candidate import EXE, PREFIX, LAUNCHER, README, MANIFEST
from baldosa_windows_native_pause_route import (
    run_route, run_native_crash_between_raw_and_typed, USA_SHA256,
)
from verify_retained_owner_playtest import (
    SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256, ZIP,
    NAMES as OWNER_FILES, validate,
)


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def extract_original(retained: Path, work: Path) -> Path:
    actual = {p.name for p in retained.iterdir()}
    if actual != OWNER_FILES | {"ORIGINAL-ARTIFACT-RETENTION.json"}:
        raise ValueError("Retained archive member set differs from the original owner receipt")
    four = work / "original-four"
    four.mkdir()
    for name in OWNER_FILES:
        source = retained / name
        if not source.is_file() or source.is_symlink():
            raise ValueError("Missing/redirected original owner member: " + name)
        shutil.copyfile(source, four / name)
    validate(four)  # existing original SHA/provenance/ROM-free/manifest verifier
    candidate = four / ZIP
    if digest(candidate) != CANDIDATE_SHA256:
        raise ValueError("Original nominated owner ZIP SHA differs")
    with zipfile.ZipFile(candidate) as archive:
        names = archive.namelist()
        expected = sorted(PREFIX + name for name in (EXE, LAUNCHER, README, MANIFEST))
        if names != expected or archive.testzip() is not None:
            raise ValueError("Original inner ZIP member-set/CRC differs")
        exe = work / EXE
        with archive.open(PREFIX + EXE) as src, exe.open("xb") as dst:
            shutil.copyfileobj(src, dst)
    if digest(exe) != EXE_SHA256:
        raise ValueError("Extracted original executable SHA differs")
    return exe


def inspect_seam(seam: Path) -> dict:
    report = json.loads((seam / "file-receipt.json").read_text("utf-8"))
    if set(report) != {"raw-sram", "typed-profile", "selector", "roster"}:
        raise ValueError("Not the four owned crash-seam files")
    for name, row in report.items():
        before = (seam / f"{name}.before.bin").read_bytes()
        after = (seam / f"{name}.after.bin").read_bytes()
        changed = sum(a != b for a, b in zip(before, after)) + abs(len(before) - len(after))
        if (len(before) != row["before_bytes"] or len(after) != row["after_bytes"]
            or hashlib.sha256(before).hexdigest() != row["before_sha256"]
            or hashlib.sha256(after).hexdigest() != row["after_sha256"]
            or changed != row["changed_byte_count"]):
            raise ValueError("Unfaithful actual byte receipt: " + name)
        if name == "raw-sram":
            if len(before) != 8192 or len(after) != 8192 or changed == 0:
                raise ValueError("Invalid/zero-delta actual raw crash witness")
        elif changed:
            raise ValueError("Fault mutated last-good committed metadata: " + name)
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("retained", "rom", "script", "fixture", "out"):
        p.add_argument("--" + name, required=True, type=Path)
    a = p.parse_args()
    if a.out.exists():
        raise ValueError("Refusing prior data root or overwritten crash evidence")
    if digest(a.rom) != USA_SHA256:
        raise ValueError("Reference USA ROM identity differs")
    a.out.mkdir(parents=True)
    exe = extract_original(a.retained, a.out)
    work = a.out / "run"
    work.mkdir()
    run_route(exe, a.rom, a.script, work, pause=False, video="windows", timeout=120)
    seed = work / "baseline/Modern Player Data With Spaces/saves/save.srm"
    seam = work / "native_post_raw_pre_typed_crash/seam"
    proof = run_native_crash_between_raw_and_typed(
        exe, a.rom, a.script, work, a.fixture, seed,
        video="windows", timeout=120, snapshot_dir=seam,
    )
    files = inspect_seam(seam)
    if not (proof["real_raw_sram_write_completed"]
            and proof["fresh_process_rejected_before_guest"]
            and not proof["cross_file_crash_atomicity_proven"]):
        raise ValueError("Did not reproduce the unresolved actual guest crash P0")
    receipt = {
        "schema": "qa02-nominated-owner-real-win32-crash-byte-receipt/1",
        "tested_source": SOURCE_COMMIT,
        "original_candidate_zip_sha256": CANDIDATE_SHA256,
        "original_candidate_exe_sha256": EXE_SHA256,
        "same_original_executable_executed": digest(exe) == EXE_SHA256,
        "fixture_sha256": digest(a.fixture),
        "source_script_sha256": digest(a.script),
        "reference_rom_sha256": digest(a.rom),
        "native_process_result": proof,
        "byte_exact_seam_files": files,
        "classification": "real_Win32_in_process__Exit86_and_cold_process_refusal_not_external_taskkill_or_power_loss",
        "release_gate_witnesses": 0,
        "physical_hardware_tested": False,
    }
    (seam / "qa02-exact-owner-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("QA02_EXACT_NOMINATED_WIN32_P0 " + json.dumps({
        "original_exe": EXE_SHA256,
        "raw_changed": files["raw-sram"]["changed_byte_count"],
        "typed_unchanged": files["typed-profile"]["changed_byte_count"] == 0,
        "cold_restart_rejected": True,
        "gate_credit": 0,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
