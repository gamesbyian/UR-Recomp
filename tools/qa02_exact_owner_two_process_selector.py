#!/usr/bin/env python3
"""Independent original nominated Windows 2-process stale-selector byte auditor.

A is the original game executable in real live 2P SDL Pause; B is a distinct
native fixture process using canonical Modern selector/catalog/profile writers.
This is NOT two game executables racing or full J-07 fixture acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from baldosa_windows_native_pause_route import (
    USA_SHA256, capture_native_selector_conflict_files, run_route,
    run_native_pause_quit_selector_conflict, verify_named_profile_boot_bytes,
)
from qa02_exact_owner_win32_seam import extract_original
from verify_retained_owner_playtest import SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256

STAGES = ("before_A", "after_B_before_A", "after_A")
NAMES = ("selector", "catalog", "first_raw", "first_typed", "second_raw", "second_typed")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_host_profile_stock_sram(blob: bytes) -> tuple[int, bytes]:
    """Independently decode full typed SRAM without trusting producer receipt."""
    text = blob.decode("ascii")
    if not text.startswith("UR-HOST-PROFILE/5\n"):
        raise ValueError("Not the current authentic typed Modern profile")
    values: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if "=" not in line:
            raise ValueError("Malformed typed Modern profile assignment")
        key, value = line.split("=", 1)
        if key in values:
            raise ValueError("Duplicate typed Modern profile field")
        values[key] = value
    raw_hex = values.get("stock_sram", "")
    if len(raw_hex) != 16384:
        raise ValueError("Typed profile does not contain 8192 SRAM bytes")
    data = bytes.fromhex(raw_hex)
    generation = int(values["generation"])
    return generation, data


def snapshot_bytes(folder: Path, stage: str) -> dict[str, bytes | None]:
    out: dict[str, bytes | None] = {}
    manifest = json.loads((folder / f"{stage}.json").read_text(encoding="utf-8"))
    if set(manifest) != set(NAMES):
        raise ValueError("Snapshot omitted a source-owned file")
    for key in NAMES:
        row = manifest[key]
        if not row["present"]:
            if stage != "before_A" or not key.startswith("second_"):
                raise ValueError("Missing observed required profile file")
            out[key] = None
            continue
        data = (folder / f"{stage}.{key}.bin").read_bytes()
        if row["size"] != len(data) or row["sha256"] != sha256(data):
            raise ValueError("Actual snapshot bytes do not match their receipt")
        out[key] = data
    return out


def audit_stage_files(folder: Path) -> dict:
    before, writer, final = (snapshot_bytes(folder, stage) for stage in STAGES)
    for key in ("selector", "catalog", "first_raw", "first_typed"):
        if not before[key]:
            raise ValueError("First owner profile missing before writer B")
    for key in ("second_raw", "second_typed"):
        if before[key] is not None:
            raise ValueError("Unexpected second profile present before B")
    if before["selector"] == writer["selector"] or before["catalog"] == writer["catalog"]:
        raise ValueError("Separate Modern writer B did not actually commit selector+catalog")
    if before["first_raw"] != writer["first_raw"] or before["first_typed"] != writer["first_typed"]:
        raise ValueError("Competing writer B mutated stale first profile")
    if writer != final:
        raise ValueError("Stale game A modified canonical data after writer B committed")
    assert isinstance(final["second_raw"], bytes)
    assert isinstance(final["first_raw"], bytes)
    if final["first_raw"] == final["second_raw"]:
        raise ValueError("Two named profiles have aliased raw SRAM")
    sizes = {}
    for key in ("first", "second"):
        raw = final[f"{key}_raw"]
        typed = final[f"{key}_typed"]
        assert isinstance(raw, bytes) and isinstance(typed, bytes)
        generation, embedded = decode_host_profile_stock_sram(typed)
        if len(raw) != 8192 or embedded != raw:
            raise ValueError("Actual full typed SRAM disagrees with canonical raw data")
        sizes[key] = {"generation": generation,
                      "raw_size": len(raw), "raw_sha256": sha256(raw),
                      "typed_size": len(typed), "typed_sha256": sha256(typed)}
    return {
        "writer_B_selector_changed": True, "writer_B_catalog_changed": True,
        "A_first_raw_and_typed_unchanged": True,
        "A_cannot_revert_writer_B_selector_or_catalog": True,
        "after_writer_B_equals_after_stale_game_A_for_all_six_files": True,
        "independent_typed_sram_full_8192_byte_equality": True,
        "profiles_have_distinct_raw_sram": True, "profiles": sizes,
        "all_final_sha256": {
            key: sha256(data) for key, data in final.items()
            if isinstance(data, bytes)
        },
    }


def cold_boot_second_profile(exe: Path, rom: Path, case: Path,
                             user_root: Path, snapshot_dir: Path) -> dict:
    raw = (user_root / "saves/profile-native-ci-second/save.srm").read_bytes()
    if len(raw) != 8192:
        raise ValueError("Missing 8192-byte second-profile cold boot source")
    script = case / "qa02-second-cold-boot.txt"
    script.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "SDL_VIDEODRIVER": "windows",
        "SDL_AUDIODRIVER": "dummy",
    })
    config = case / "native_pause_quit_selector_race/config.ini"
    result = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=case, env=env, capture_output=True, text=True,
        errors="replace", timeout=120,
    )
    log = result.stdout + "\n" + result.stderr
    (snapshot_dir / "cold-B.log").write_text(log, encoding="utf-8")
    if result.returncode != 0 or "UR-BALDOSA-SAVE-MISMATCH" in log:
        raise ValueError("Second real Windows game process failed cold reentry")
    witness = verify_named_profile_boot_bytes(log, raw, profile_id="native-ci-second")
    return {
        "process_exit": result.returncode,
        "source_first_guest_sram_bytes": witness["bytes"],
        "source_first_guest_sram_fnv32": witness["fnv32"],
        "guest_boot_from_selected_new_profile": True,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("retained", "rom", "script", "fixture", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    a.retained = a.retained.resolve(strict=True)
    a.rom = a.rom.resolve(strict=True)
    a.script = a.script.resolve(strict=True)
    a.fixture = a.fixture.resolve(strict=True)
    a.out = a.out.resolve()
    if a.out.exists() or sha256(a.rom.read_bytes()) != USA_SHA256:
        raise ValueError("Refuse reused evidence root or unrecognized original USA ROM")
    a.out.mkdir(parents=True)
    exe = extract_original(a.retained, a.out)
    if sha256(exe.read_bytes()) != EXE_SHA256:
        raise ValueError("Original nominated Windows executable changed")
    route = a.out / "baseline"
    route.mkdir()
    run_route(exe, a.rom, a.script, route, pause=False, video="windows", timeout=120)
    seed = route / "baseline/Modern Player Data With Spaces/saves/save.srm"
    if len(seed.read_bytes()) != 8192:
        raise ValueError("Actual original source-owned raw seed missing")
    case = a.out / "case"
    case.mkdir()
    saved = case / "native_pause_quit_selector_race/byte-snapshots"
    proof = run_native_pause_quit_selector_conflict(
        exe, a.rom, a.script, case, a.fixture, seed,
        video="windows", timeout=120, snapshot_dir=saved,
    )
    source_log = case / "native_pause_quit_selector_race/log.txt"
    (saved / "stale-A.log").write_bytes(source_log.read_bytes())
    audited = audit_stage_files(saved)
    user_root = case / "native_pause_quit_selector_race/Two Process Profile Root With Spaces"
    before_cold = snapshot_bytes(saved, "after_A")
    boot = cold_boot_second_profile(exe, a.rom, case, user_root, saved)
    after_cold = capture_native_selector_conflict_files(user_root, saved, "after_cold_B")
    if {key: row["sha256"] if row["present"] else None for key, row in after_cold.items()} != {
        key: sha256(data) if isinstance(data, bytes) else None
        for key, data in before_cold.items()
    }:
        raise ValueError("Fresh B cold boot modified canonical A/B profile data")
    if list(user_root.rglob("*.urrun")) or list(user_root.rglob("*.urmatch")) or list(user_root.rglob("*.urghost")):
        raise ValueError("No completed guest result can be invented by selection change")
    receipt = {
        "schema": "qa02-exact-nominated-win32-stale-selector-two-real-processes/1",
        "source_commit": SOURCE_COMMIT, "original_zip_sha256": CANDIDATE_SHA256,
        "original_executable_sha256": EXE_SHA256,
        "qa_fixture_sha256": sha256(a.fixture.read_bytes()),
        "original_rom_sha256": sha256(a.rom.read_bytes()),
        "original_2p_input_sha256": sha256(a.script.read_bytes()),
        "source_harness": proof, "independent_six_file_audit": audited,
        "fresh_original_executable_second_profile": boot,
        "cold_reentry_kept_all_canonical_data": True,
        "second_process_B_is_native_fixture_not_second_game_executable": True,
        "no_duplicate_or_fake_results": True,
        "real_physical_pad_tested": False, "power_cut_tested": False,
        "recovery_of_post_raw_pre_typed_crash_p0": False,
        "release_gate_credit": 0,
    }
    (saved / "qa02-exact-owner-selector-conflict.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("QA02_EXACT_OWNER_SELECTOR_CONFLICT " + json.dumps({
        "original_exe": EXE_SHA256, "real_stale_guest_frame": 1952,
        "six_files_preserved_after_B": True, "cold_B": True, "gate_credit": 0,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
