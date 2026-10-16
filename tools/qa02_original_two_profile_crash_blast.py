#!/usr/bin/env python3
"""QA-02: independent exact original Win32 crash blast-radius across two racers.

After actual native B SRAM save and _Exit(86) before typed checkpoint, inspect
whether the verified intact A can be reselected by the existing locked Modern
profile selector. Any reproduced lockout is a *negative* P0 witness, never a
passing release gate. All saves are temporary fixture-owned files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from baldosa_windows_native_pause_route import (
    USA_SHA256, run_route, verify_named_profile_boot_bytes,
)
from qa02_exact_owner_win32_seam import extract_original
from qa02_exact_owner_two_process_selector import decode_host_profile_stock_sram
from verify_retained_owner_playtest import SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256

FILES = {
    "selector": "host-state-v1.txt",
    "catalog": "profiles-v1.txt",
    "A_raw": "saves/profile-native-ci-rider/save.srm",
    "A_typed": "saves/profile-native-ci-rider/host-profile.txt",
    "B_raw": "saves/profile-native-ci-second/save.srm",
    "B_typed": "saves/profile-native-ci-second/host-profile.txt",
}
STAGES = ("healthy_before_B_crash", "after_B_crash",
          "after_B_cold_refusal", "after_selector_refusal")
CRASH_MARK = "UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_RAW_WRITE exit=86 typed_checkpoint=0"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def capture(root: Path, output: Path, stage: str) -> dict[str, bytes]:
    if stage not in STAGES:
        raise ValueError("invalid independent crash-blast-radius stage")
    output.mkdir(parents=True, exist_ok=True)
    result, receipt = {}, {}
    for name, rel in FILES.items():
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError("unexpected missing/redirected canonical file: " + rel)
        data = path.read_bytes()
        if name.endswith("_raw") and len(data) != 8192:
            raise ValueError("named raw SRAM is not 8192 bytes")
        (output / f"{stage}.{name}.bin").write_bytes(data)
        result[name] = data
        receipt[name] = {"sha256": digest(data), "bytes": len(data)}
    (output / f"{stage}.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def adjudicate_crash(before: dict[str, bytes], after: dict[str, bytes]) -> dict:
    if set(before) != set(FILES) or set(after) != set(FILES):
        raise ValueError("incomplete six-file independent raw crash receipt")
    for key in ("A", "B"):
        generation, full = decode_host_profile_stock_sram(before[key + "_typed"])
        if generation != 1 or len(full) != 8192 or full != before[key + "_raw"]:
            raise ValueError("both profiles must be originally valid before crash")
    for key in ("selector", "catalog", "A_raw", "A_typed", "B_typed"):
        if before[key] != after[key]:
            raise ValueError("crash changed last-good metadata or healthy racer A: " + key)
    if after["B_raw"] == before["B_raw"] or len(after["B_raw"]) != 8192:
        raise ValueError("original game did not write newly changed B raw SRAM")
    if decode_host_profile_stock_sram(after["B_typed"])[1] == after["B_raw"]:
        raise ValueError("injected real B crash did not leave raw/typed mismatch")
    diff = sum(x != y for x, y in zip(before["B_raw"], after["B_raw"]))
    return {
        "healthy_A_raw_typed_and_global_data_unchanged": True,
        "B_raw_changed_count": diff,
        "B_old_typed_unpublished": True,
        "B_complete_raw_and_typed_diverge": True,
        "A_complete_raw_matches_typed": True,
        "old_and_new_B_raw_sha256": [digest(before["B_raw"]), digest(after["B_raw"])],
        "after_crash_six_file_sha256": {k: digest(v) for k, v in after.items()},
    }


def source_fixture(fixture: Path, root: Path, args: list[str],
                   *, timeout: int = 90) -> tuple[int, str]:
    p = subprocess.run([str(fixture), str(root), *args],
                       capture_output=True, text=True,
                       errors="replace", timeout=timeout)
    return p.returncode, p.stdout + "\n" + p.stderr


def run_game(exe: Path, rom: Path, script: Path, root: Path, folder: Path,
             config: Path, *, crash: bool) -> tuple[int, str]:
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1" if crash else "0",
        "UR_BALDOSA_PAUSE_SMOKE": "1" if crash else "0",
        "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1" if crash else "0",
        "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "1952",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1" if crash else "0",
        "UR_BALDOSA_PAUSE_QUIT_SMOKE": "1" if crash else "0",
        "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "0",
        "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
        "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
        "SDL_VIDEODRIVER": "windows",
        "SDL_AUDIODRIVER": "dummy",
    })
    env.pop("UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE", None)
    if crash:
        env["UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE"] = "1"
    p = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=folder, env=env, capture_output=True,
        text=True, errors="replace", timeout=120)
    return p.returncode, p.stdout + "\n" + p.stderr


def main() -> int:
    p = argparse.ArgumentParser()
    for field in ("retained", "rom", "script", "fixture", "out"):
        p.add_argument("--" + field, type=Path, required=True)
    a = p.parse_args()
    for field in ("retained", "rom", "script", "fixture"):
        setattr(a, field, getattr(a, field).resolve(strict=True))
    a.out = a.out.resolve()
    if a.out.exists() or digest(a.rom.read_bytes()) != USA_SHA256:
        raise ValueError("nonfresh QA root or wrong USA source ROM")
    a.out.mkdir(parents=True)
    exe = extract_original(a.retained, a.out)
    if digest(exe.read_bytes()) != EXE_SHA256:
        raise ValueError("original nominated Windows game binary does not match")
    baseline = a.out / "baseline"
    baseline.mkdir()
    run_route(exe, a.rom, a.script, baseline, pause=False,
              video="windows", timeout=120)
    seed = baseline / "baseline/Modern Player Data With Spaces/saves/save.srm"
    if len(seed.read_bytes()) != 8192:
        raise ValueError("failed authentic source 8KiB SRAM seed")
    work = a.out / "case"
    work.mkdir()
    evidence = work / "evidence"
    evidence.mkdir()
    root = work / "Two Distinct Crash Test Racers With Spaces"
    root.mkdir()
    code, _ = source_fixture(a.fixture, root, [str(seed)])
    if code:
        raise ValueError("canonical fixture did not create first valid racer A")
    code, log = source_fixture(a.fixture, root, [str(seed), "--add-second"])
    if code or "switched=native-ci-second sram=8192 distinct=1" not in log:
        raise ValueError("canonical fixture failed to activate separate racer B")
    for profile in ("native-ci-rider", "native-ci-second"):
        code, log = source_fixture(a.fixture, root, [profile, "--verify-native-save"])
        if code or f"VERIFIED profile={profile} sram=8192" not in log:
            raise ValueError("initial Modern typed/raw named rider invalid: " + profile)
    # Healthy control: the exact existing locked canonical selector works
    # in BOTH directions while both registered profile raw images are valid.
    for current, next_id in (("native-ci-second", "native-ci-rider"),
                             ("native-ci-rider", "native-ci-second")):
        code, log = source_fixture(
            a.fixture, root, [current, next_id, "--select-existing-next-boot"])
        if code or f"existing_next_boot={next_id}" not in log:
            raise ValueError("healthy existing-profile switch control did not succeed")
    before = capture(root, evidence, "healthy_before_B_crash")
    config = work / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    original = work / "game_B_crash"
    original.mkdir()
    code, crash_log = run_game(exe, a.rom, a.script, root, original, config, crash=True)
    (evidence / "game-B-crash.log").write_text(crash_log, encoding="utf-8")
    if code != 86 or crash_log.count(CRASH_MARK) != 1 or (
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=" in crash_log):
        raise ValueError("original game did not die exactly after raw B write")
    verify_named_profile_boot_bytes(crash_log, before["B_raw"], profile_id="native-ci-second")
    after = capture(root, evidence, "after_B_crash")
    audit = adjudicate_crash(before, after)
    code_a, log_a = source_fixture(a.fixture, root, ["native-ci-rider", "--verify-native-save"])
    code_b, log_b = source_fixture(a.fixture, root, ["native-ci-second", "--verify-native-save"])
    (evidence / "A-B-codec-verify.log").write_text(
        f"A code={code_a}\n{log_a}\nB code={code_b}\n{log_b}", encoding="utf-8")
    if code_a or "VERIFIED profile=native-ci-rider sram=8192" not in log_a:
        raise ValueError("original healthy A became corrupt after B crash")
    if code_b == 0:
        raise ValueError("modern codec treated divergent raw B as healthy")
    fresh = work / "game_B_fresh"
    fresh.mkdir()
    short = work / "cold.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    cold_rc, cold_log = run_game(exe, a.rom, short, root, fresh, config, crash=False)
    (evidence / "B-cold-rejection.log").write_text(cold_log, encoding="utf-8")
    if (cold_rc != 7 or
        "UR-BALDOSA-SAVE-MISMATCH: Named racer SRAM differs from " not in cold_log or
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in cold_log):
        raise ValueError("B cold boot did not fail closed before guest on actual mismatch")
    after_cold = capture(root, evidence, "after_B_cold_refusal")
    if after_cold != after:
        raise ValueError("failed cold B boot mutated any of the six owned files")
    # This is the crucial blast-radius discriminator. Same canonical
    # selector succeeded on healthy B immediately prior to crashing;
    # after B's mismatch it must NOT silently ignore B to select A.
    code, switch_log = source_fixture(
        a.fixture, root,
        ["native-ci-second", "native-ci-rider", "--select-existing-next-boot"])
    (evidence / "B-to-A-canonical-switch.log").write_text(
        f"exit={code}\n{switch_log}", encoding="utf-8")
    after_switch = capture(root, evidence, "after_selector_refusal")
    if after_switch != after:
        raise ValueError("profile selection under B crash mutated saved canonical files")
    if code == 0:
        raise ValueError("selector unexpectedly accepted other profile; prior code premise changed")
    if any(list(root.rglob(ext)) for ext in ("*.urrun", "*.urmatch", "*.urghost")):
        raise ValueError("crash or attempted switch invented completed run/record")
    evidence_report = {
        "schema": "qa02-original-owner-two-profile-crash-blast-radius/1",
        "outcome": "P0_reproduced_original_B_raw_typed_crash_blocks_canonical_switch_to_intact_A",
        "source_commit": SOURCE_COMMIT,
        "original_zip_sha256": CANDIDATE_SHA256,
        "original_executable_sha256": EXE_SHA256,
        "fixture_sha256": digest(a.fixture.read_bytes()),
        "rom_sha256": digest(a.rom.read_bytes()),
        "original_2p_script_sha256": digest(a.script.read_bytes()),
        "healthy_bidirectional_selector_control": True,
        "profile_A_verified_valid_after_B_crash": True,
        "B_actual_original_game_crash_exit": 86,
        "B_cold_launch_exit": cold_rc,
        "B_to_A_canonical_switch_exit": code,
        "selection_refusal_preserved_all_six_files": True,
        "actual_file_audit": audit,
        "not_a_user_UI_or_all_recovery_paths_proof": True,
        "not_a_product_fix": True,
        "not_a_release_pass": True,
        "release_gate_credit": 0,
    }
    (evidence / "qa02-original-B-crash-A-blocked.json").write_text(
        json.dumps(evidence_report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("QA02_ORIGINAL_B_CRASH_A_BLOCKED " + json.dumps({
        "sha": EXE_SHA256, "original_B_changed_raw_bytes": audit["B_raw_changed_count"],
        "healthy_A": True, "B_cold_refused": True,
        "B_to_A_canonical_reselection_refused": True, "release_gate_credit": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
