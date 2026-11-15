#!/usr/bin/env python3
"""QA-02: overlap two genuine immutable nominated Windows game processes.

A pauses at real guest 1952, B legitimately saves the SAME profile while A
remains alive, A then attempts a stale Quit, C cold-loads B's committed data.
No Modern implementation changes, unearned results or release-gate credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from baldosa_windows_native_pause_route import (
    USA_SHA256, run_route, verify_named_profile_boot_bytes,
)
from qa02_exact_owner_win32_seam import extract_original, extract_source_bound
from qa02_candidate_identity import CandidateIdentity
from qa02_exact_owner_two_process_selector import decode_host_profile_stock_sram
from verify_retained_owner_playtest import SOURCE_COMMIT, CANDIDATE_SHA256, EXE_SHA256

FILES = {
    "raw": "saves/profile-native-ci-rider/save.srm",
    "typed": "saves/profile-native-ci-rider/host-profile.txt",
    "selector": "host-state-v1.txt",
    "catalog": "profiles-v1.txt",
}
STAGES = ("before_A", "after_B", "after_A", "after_C")
ARMED = "UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1 modern_session=1 physical_sdl=1"
QUIT = "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1 paused=1 guest_steps=0"


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def snapshot(root: Path, output: Path, stage: str) -> dict[str, bytes]:
    if stage not in STAGES:
        raise ValueError("unknown exact-original two-game evidence stage")
    output.mkdir(parents=True, exist_ok=True)
    found = {}
    receipt = {}
    for label, rel in FILES.items():
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError("canonical owned save file missing or symlinked: " + rel)
        b = path.read_bytes()
        if label == "raw" and len(b) != 8192:
            raise ValueError("named SRAM must be exactly 8192 bytes")
        (output / f"{stage}.{label}.bin").write_bytes(b)
        found[label] = b
        receipt[label] = {"sha256": digest(b), "bytes": len(b)}
    (output / f"{stage}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return found


def validate_typed_raw(row: dict[str, bytes]) -> int:
    generation, embedded = decode_host_profile_stock_sram(row["typed"])
    if len(row["raw"]) != 8192 or embedded != row["raw"]:
        raise ValueError("actual complete typed 8192 SRAM differs from raw SRAM")
    return generation


def verify_interleaving(before: dict[str, bytes], b: dict[str, bytes],
                        a: dict[str, bytes]) -> dict:
    if any(set(x) != set(FILES) for x in (before, b, a)):
        raise ValueError("partial canonical file snapshot")
    old_gen, new_gen = validate_typed_raw(before), validate_typed_raw(b)
    validate_typed_raw(a)
    if old_gen >= new_gen or before["raw"] == b["raw"]:
        raise ValueError("second genuine Windows game did not save new guest data")
    if (before["selector"], before["catalog"]) != (b["selector"], b["catalog"]):
        raise ValueError("second game changed global selector or roster")
    if b != a:
        raise ValueError("stale original first game overwrote second game's data")
    return {
        "raw_changed_bytes": sum(x != y for x, y in zip(before["raw"], b["raw"])),
        "generation_before": old_gen, "generation_after_B": new_gen,
        "all_four_after_B_identical_after_stale_A": True,
        "all_stage_typed_raw_8192_equal": True,
        "post_B_sha256": {k: digest(v) for k, v in b.items()},
    }



def verify_cold_recovery(b: dict[str, bytes], a: dict[str, bytes],
                         c: dict[str, bytes], committed_generation: int) -> int:
    """Independent byte contract for the third genuine cold game."""
    if any(set(x) != set(FILES) for x in (b, a, c)):
        raise ValueError("partial canonical cold recovery snapshot")
    generation = validate_typed_raw(c)
    if c["raw"] != b["raw"]:
        raise ValueError("cold C changed B committed SRAM instead of preserving it")
    if generation < committed_generation:
        raise ValueError("cold C regressed the committed typed generation")
    if c["selector"] != a["selector"] or c["catalog"] != a["catalog"]:
        raise ValueError("cold C mutated unrelated global authority")
    return generation


def verify_checkout_identity(identity: CandidateIdentity | None, hosted_sha: str | None) -> None:
    """Reject a candidate from another checkout before extraction or execution."""
    if identity is None:
        return
    if os.environ.get("GITHUB_ACTIONS") == "true" and not hosted_sha:
        raise ValueError("QA-02 hosted candidate missing checkout SHA")
    if hosted_sha and identity.source_sha != hosted_sha:
        raise ValueError("QA-02 candidate receipt source differs from hosted checkout")


def environment(root: Path, *, gate: Path | None = None,
                pause: bool = True) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1" if pause else "0",
        "UR_BALDOSA_PAUSE_SMOKE": "1" if pause else "0",
        "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1" if pause else "0",
        "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "1952",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1" if pause else "0",
        "UR_BALDOSA_PAUSE_QUIT_SMOKE": "1" if pause else "0",
        "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "0",
        "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
        "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
        "SDL_VIDEODRIVER": "windows",
        "SDL_AUDIODRIVER": "dummy",
    })
    env.pop("UR_BALDOSA_PAUSE_QUIT_CONFLICT_GATE", None)
    if gate is not None:
        env["UR_BALDOSA_PAUSE_QUIT_CONFLICT_GATE"] = str(gate)
    return env


def game(exe: Path, rom: Path, script: Path, config: Path, cwd: Path,
         env: dict[str, str], log_path: Path) -> tuple[int, str]:
    p = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=cwd, env=env, capture_output=True, text=True,
        errors="replace", timeout=120,
    )
    log = p.stdout + "\n" + p.stderr
    log_path.write_text(log, encoding="utf-8")
    return p.returncode, log


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--retained", type=Path)
    for arg in ("rom", "script", "fixture", "out"):
        p.add_argument("--" + arg, type=Path, required=True)
    p.add_argument("--candidate-zip", type=Path)
    p.add_argument("--candidate-receipt", type=Path)
    a = p.parse_args()
    if (a.candidate_zip is None) != (a.candidate_receipt is None):
        p.error("--candidate-zip and --candidate-receipt must be supplied together")
    if a.candidate_receipt is None and a.retained is None:
        p.error("--retained required for historical candidate mode")
    for key in ("rom", "script", "fixture"):
        setattr(a, key, getattr(a, key).resolve(strict=True))
    if a.retained is not None:
        a.retained = a.retained.resolve(strict=True)
    a.out = a.out.resolve()
    if a.out.exists() or digest(a.rom.read_bytes()) != USA_SHA256:
        raise ValueError("reused root or incorrect source USA ROM")
    a.out.mkdir(parents=True)
    identity = (CandidateIdentity.from_receipt(a.candidate_receipt.resolve(strict=True))
                if a.candidate_receipt else None)
    # A valid receipt can still name a different build. On hosted Actions,
    # require its source to be the exact checked-out experiment revision.
    verify_checkout_identity(identity, os.environ.get("GITHUB_SHA"))
    exe = (extract_source_bound(a.candidate_zip.resolve(strict=True), a.out,
                                a.candidate_receipt.resolve(strict=True))
           if identity else extract_original(a.retained, a.out))
    expected_exe = identity.exe_sha256 if identity else EXE_SHA256
    if digest(exe.read_bytes()) != expected_exe:
        raise ValueError("not unchanged original nominated Windows executable")
    baseline = a.out / "baseline"
    baseline.mkdir()
    run_route(exe, a.rom, a.script, baseline, pause=False, video="windows", timeout=120)
    seed = baseline / "baseline/Modern Player Data With Spaces/saves/save.srm"
    if len(seed.read_bytes()) != 8192:
        raise ValueError("no exact real native seed")
    case = a.out / "two_games"
    case.mkdir()
    evidence = case / "evidence"
    evidence.mkdir()
    root = case / "Disposable Shared Named Racer With Spaces"
    root.mkdir()
    subprocess.run([str(a.fixture), str(root), str(seed)],
                   cwd=case, check=True, capture_output=True, text=True, timeout=30)
    before = snapshot(root, evidence, "before_A")
    if validate_typed_raw(before) != 1:
        raise ValueError("invalid original seeded typed generation")
    config = case / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    dirs = [case / x for x in ("game_A", "game_B", "game_C")]
    for directory in dirs:
        directory.mkdir()
    gate = case / "game_B_committed.ready"
    log_a = evidence / "game-A.log"
    with log_a.open("wb") as sink:
        first = subprocess.Popen(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(a.script), str(a.rom)],
            cwd=dirs[0], env=environment(root, gate=gate),
            stdout=sink, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                log = log_a.read_text(encoding="utf-8", errors="replace")
                if ARMED in log:
                    break
                if first.poll() is not None:
                    raise ValueError("first game exited before second: " + log[-1200:])
                time.sleep(.02)
            else:
                raise TimeoutError("first game never paused during original 2P race")
            if first.poll() is not None:
                raise ValueError("first Windows game not alive during overlap")
            b_exit, log_b = game(
                exe, a.rom, a.script, config, dirs[1],
                environment(root), evidence / "game-B.log",
            )
            if (b_exit != 0 or log_b.count(ARMED) != 1 or
                log_b.count(QUIT) != 1 or
                "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider status=committed" not in log_b):
                raise ValueError("second genuine original game failed its authentic save")
            verify_named_profile_boot_bytes(log_b, before["raw"])
            saved_b = snapshot(root, evidence, "after_B")
            if first.poll() is not None:
                raise ValueError("first game was not alive after B saved")
            gate.write_text("second-real-game-committed\n", encoding="ascii")
            first.wait(timeout=120)
        except BaseException:
            if first.poll() is None:
                first.kill()
                first.wait(timeout=30)
            raise
    log = log_a.read_text(encoding="utf-8", errors="replace")
    saved_a = snapshot(root, evidence, "after_A")
    if (log.count(ARMED) != 1 or
        log.count(QUIT) != 1 or
        "UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed" not in log or
        "UR-BALDOSA-SAVE-FAILED: Native save was refused before writing." not in log or
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider" in log):
        diagnostics = {
            "exit_code": first.returncode,
            "expected_save_refusal": "UR-BALDOSA-SAVE-FAILED: Native save was refused before writing." in log,
            "armed_count": log.count(ARMED),
            "quit_count": log.count(QUIT),
            "preflight_failure_seen": "UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed" in log,
            "checkpoint_seen": "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider" in log,
            "log_tail": log[-4000:],
            "after_B_vs_after_A_sha256": {
                key: {"after_B": digest(saved_b[key]), "after_A": digest(saved_a[key])}
                for key in FILES
            },
        }
        (evidence / "stale-A-failure-diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise ValueError("stale game A failed rejection witness: " +
                         json.dumps({k: v for k, v in diagnostics.items()
                                     if k != "log_tail"}, sort_keys=True))
    verify_named_profile_boot_bytes(log, before["raw"])
    comparison = verify_interleaving(before, saved_b, saved_a)
    cold = case / "cold_script.txt"
    cold.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    c_exit, log_c = game(
        exe, a.rom, cold, config, dirs[2], environment(root, pause=False),
        evidence / "game-C.log",
    )
    # Retain the actual cold-load witness even if the process fails before
    # the post-C canonical files can be snapshotted.
    cold_diagnostics = {
        "exit_code": c_exit,
        "save_mismatch_seen": "UR-BALDOSA-SAVE-MISMATCH" in log_c,
        "log_tail": log_c[-4000:],
        "after_B_sha256": {key: digest(value) for key, value in saved_b.items()},
    }
    (evidence / "cold-C-diagnostics.json").write_text(
        json.dumps(cold_diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if c_exit or cold_diagnostics["save_mismatch_seen"]:
        raise ValueError("fresh third original Windows game rejected saved B SRAM")
    try:
        verify_named_profile_boot_bytes(log_c, saved_a["raw"])
        saved_c = snapshot(root, evidence, "after_C")
    except (ValueError, OSError) as error:
        # A malformed or missing post-C save is itself the crucial evidence.
        # Preserve the failure reason before the workflow uploads the directory.
        cold_diagnostics["cold_load_or_snapshot_failure"] = str(error)
        cold_diagnostics["after_C_files"] = {
            key: {
                "exists": (root / rel).is_file(),
                "sha256": digest((root / rel).read_bytes())
                if (root / rel).is_file() and not (root / rel).is_symlink()
                else None,
            }
            for key, rel in FILES.items()
        }
        (evidence / "cold-C-diagnostics.json").write_text(
            json.dumps(cold_diagnostics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        raise
    try:
        cold_generation = verify_cold_recovery(
            saved_b, saved_a, saved_c, comparison["generation_after_B"])
    except ValueError as error:
        cold_diagnostics["byte_contract_failure"] = str(error)
        cold_diagnostics["after_C_sha256"] = {
            key: digest(value) for key, value in saved_c.items()}
        cold_diagnostics["after_C_vs_after_B_equal"] = {
            key: saved_c[key] == saved_b[key] for key in FILES}
        (evidence / "cold-C-diagnostics.json").write_text(
            json.dumps(cold_diagnostics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        raise
    if any(path for ext in ("*.urrun", "*.urmatch", "*.urghost") for path in root.rglob(ext)):
        raise ValueError("invented earned result on Pause/Quit")
    report = {
        "schema": "qa02-exact-owner-two-running-win32-games/1",
        "candidate_source": identity.source_sha if identity else SOURCE_COMMIT,
        "candidate_zip_sha256": identity.zip_sha256 if identity else CANDIDATE_SHA256,
        "candidate_exe_sha256": expected_exe,
        "reference_rom_sha256": digest(a.rom.read_bytes()),
        "original_route_sha256": digest(a.script.read_bytes()),
        "qa_fixture_sha256": digest(a.fixture.read_bytes()),
        "two_simultaneously_alive_original_game_processes": True,
        "second_game_own_raw_and_typed_save": True,
        "stale_first_game_rejected_before_raw_write": True,
        "stale_first_game_exit_code": first.returncode,
        "fresh_third_game_cold_loaded_B_SRAM": True,
        "fresh_third_game_preserved_B_SRAM_bytes": True,
        "cold_C_typed_generation": cold_generation,
        "before_B_after_B_after_A": comparison,
        "third_game_process_exit": c_exit,
        "release_gate_credit": 0,
        "physical_gamepads": False,
        "crash_mid_write_or_power_loss": False,
        "completed_original_native_event": False,
    }
    (evidence / "qa02-two-original-game-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("QA02_TWO_ORIGINAL_WIN32_GAMES " + json.dumps({
        "exe": expected_exe, "guest_bytes_changed": comparison["raw_changed_bytes"],
        "stale_A_preserved": True, "cold_C": True, "gate_credit": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
