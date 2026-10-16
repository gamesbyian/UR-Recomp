#!/usr/bin/env python3
"""One real Win32 read-only SRAM save fault on the original nominated owner PE.

All mutable data belongs to a disposable source-created named racer fixture.
NTFS read-only file attribute is not a full disk, torn write, or power loss.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

from baldosa_windows_native_pause_route import run_route, USA_SHA256
from qa02_exact_owner_win32_seam import extract_original

FILES = {
    "raw": "saves/profile-native-ci-rider/save.srm",
    "typed": "saves/profile-native-ci-rider/host-profile.txt",
    "selector": "host-state-v1.txt",
    "catalog": "profiles-v1.txt",
}


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def take(root: Path) -> dict[str, bytes]:
    return {label: (root / rel).read_bytes() for label, rel in FILES.items()}


def compare(before: dict[str, bytes], after: dict[str, bytes]) -> dict:
    if set(before) != set(FILES) or set(after) != set(FILES):
        raise ValueError("Incomplete source-owned file inventory")
    rows = {}
    for label in FILES:
        old, new = before[label], after[label]
        rows[label] = {
            "before_size": len(old), "after_size": len(new),
            "before_sha256": digest(old), "after_sha256": digest(new),
            "changed": sum(a != b for a, b in zip(old, new)) + abs(len(old) - len(new)),
        }
    if rows["raw"]["before_size"] != 8192:
        raise ValueError("Invalid named-profile raw SRAM fixture")
    return rows


def attrib(raw: Path, flag: str) -> None:
    p = subprocess.run(["attrib", flag, str(raw)], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"Win32 attrib {flag} failed: {p.stdout} {p.stderr}")


def run_game(exe: Path, rom: Path, script: Path, config: Path,
             cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    p = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=cwd, env=env, capture_output=True, text=True,
        errors="replace", timeout=120,
    )
    return p.returncode, p.stdout + "\n" + p.stderr


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("retained", "rom", "script", "fixture", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    a.rom = a.rom.resolve(strict=True)
    a.script = a.script.resolve(strict=True)
    a.fixture = a.fixture.resolve(strict=True)
    a.retained = a.retained.resolve(strict=True)
    a.out = a.out.resolve()
    if a.out.exists() or digest(a.rom.read_bytes()) != USA_SHA256:
        raise ValueError("Refusing reused test root or incorrect original USA ROM")
    a.out.mkdir(parents=True)
    exe = extract_original(a.retained, a.out)  # existing exact owner ZIP/EXE auditor
    route = a.out / "route"
    route.mkdir()
    run_route(exe, a.rom, a.script, route, pause=False, video="windows", timeout=120)
    seed = route / "baseline/Modern Player Data With Spaces/saves/save.srm"
    case = a.out / "denied-raw-attribute"
    case.mkdir()
    root = case / "Disposable Named Racer With Spaces"
    root.mkdir()
    subprocess.run([str(a.fixture), str(root), str(seed)],
                   cwd=case, check=True, capture_output=True, text=True, timeout=30)
    validation = subprocess.run(
        [str(a.fixture), str(root), "native-ci-rider", "--verify-native-save"],
        cwd=case, capture_output=True, text=True, timeout=30)
    if validation.returncode or "VERIFIED profile=native-ci-rider sram=8192" not in validation.stdout:
        raise ValueError("Source-owned valid initial typed/raw prerequisite absent")
    before = take(root)
    raw = root / FILES["raw"]
    config = case / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(root),
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
        "SDL_VIDEODRIVER": "windows",
        "SDL_AUDIODRIVER": "dummy",
    })
    attrib(raw, "+R")
    try:
        if not (raw.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY):
            raise ValueError("Windows source raw did not acquire readonly attribute")
        exit_code, log = run_game(exe, a.rom, a.script, config, case, env)
        during = take(root)
    finally:
        attrib(raw, "-R")  # restore permission even if test fails
    evidence = case / "evidence"
    evidence.mkdir()
    (evidence / "read-only-exit.log").write_text(log, encoding="utf-8")
    rows = compare(before, during)
    for label in FILES:
        (evidence / f"{label}.before.bin").write_bytes(before[label])
        (evidence / f"{label}.during.bin").write_bytes(during[label])
    (evidence / "original-read-only-file-digests.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markers = (
        "UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1",
        "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1 paused=1 guest_steps=0",
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider bytes=8192",
    )
    witnessed = all(log.count(marker) == 1 for marker in markers)
    rejection = any(s in log for s in (
        "UR_BALDOSA_NATIVE_PROFILE native_save_failed",
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT rejected",
        "UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed",
    ))
    unearned_sidecars = [str(p.relative_to(root)) for ext in ("*.urrun", "*.urmatch", "*.urghost")
                         for p in root.rglob(ext)]
    result = {
        "schema": "qa02-exact-owner-real-win32-readonly-raw/1",
        "candidate_original_exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "fixture_exe_sha256": hashlib.sha256(a.fixture.read_bytes()).hexdigest(),
        "os_file_attribute_readonly_verified": True,
        "guest_pause_quit_observed": witnessed,
        "source_save_failure_reported_in_process_log": rejection,
        "native_process_exit": exit_code,
        "file_digests": rows,
        "data_preserved_through_failed_save": all(row["changed"] == 0 for row in rows.values()),
        "unearned_run_match_ghost_sidecars": unearned_sidecars,
        "physical_player_notice_verified": False,
        "actual_power_cut_or_disk_full": False,
        "release_gate_credit": 0,
    }
    (evidence / "qa02-readonly-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not witnessed or not result["data_preserved_through_failed_save"] or not rejection or unearned_sidecars:
        raise ValueError("Real Windows readonly save did not meet independent fail-closed assertions")
    clean = case / "cold-boot"
    clean.mkdir()
    short = clean / "no_guest.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    env.update({key: "0" for key in (
        "UR_BALDOSA_PAUSE_SMOKE", "UR_BALDOSA_MODERN_INPUT",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE", "UR_BALDOSA_PAUSE_QUIT_SMOKE",
        "UR_BALDOSA_PAUSE_REQUIRE_RACE",
    )})
    fresh_exit, fresh_log = run_game(exe, a.rom, short, config, clean, env)
    (evidence / "cold-boot.log").write_text(fresh_log, encoding="utf-8")
    cold_valid = (fresh_exit == 0 and
                  "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider bytes=8192" in fresh_log and
                  "UR-BALDOSA-SAVE-MISMATCH" not in fresh_log)
    final = subprocess.run(
        [str(a.fixture), str(root), "native-ci-rider", "--verify-native-save"],
        capture_output=True, text=True, timeout=30)
    if not cold_valid or final.returncode:
        raise ValueError("Valid original profile not playable after restoring Win32 write permission")
    result["cold_start_after_permission_repair"] = True
    result["post_cold_file_digests"] = {
        label: digest(blob) for label, blob in take(root).items()
    }
    (evidence / "qa02-readonly-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("QA02_ORIGINAL_NOMINATED_WIN32_READONLY " + json.dumps({
        "original_exe": result["candidate_original_exe_sha256"],
        "data_preserved": True, "cold_recovered": True, "release_gate_credit": 0,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
