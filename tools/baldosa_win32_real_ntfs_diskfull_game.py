#!/usr/bin/env python3
"""Source-game Win32 real NTFS full-volume save rejection.

Three phases invoked by a VHDX-only PowerShell owner. Only a temporary
verified USA ROM is installed beside the original extracted CMD; never
write ROM, VHD or private profiles into the report. Original fixture-owned
raw/typed/selector/catalog bytes are independently retained across phases.
A failed check is a test failure, never QA acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from assemble_baldosa_windows_candidate import ROM, USA_SHA256
from baldosa_win32_interactive_recovery_q import digest
from baldosa_windows_native_pause_route import native_modern_race_entry_script


def snapshot(root: Path) -> dict[str, bytes]:
    files = {
        "raw": root / "saves/profile-native-ci-rider/save.srm",
        "typed": root / "saves/profile-native-ci-rider/host-profile.txt",
        "selector": root / "host-state-v1.txt",
        "catalog": root / "profiles-v1.txt",
    }
    values = {}
    for name, file in files.items():
        if file.is_symlink() or not file.is_file():
            raise ValueError("Original canonical authority absent or redirected: " + name)
        values[name] = file.read_bytes()
    if len(values["raw"]) != 8192:
        raise ValueError("Not exact original native 8192-byte SRAM")
    return values


def retain(out: Path, stage: str, files: dict[str, bytes]) -> None:
    evidence = out / "source-bytes"
    evidence.mkdir(exist_ok=True)
    for name, content in sorted(files.items()):
        (evidence / f"{stage}.{name}.bin").write_bytes(content)


def baseline(out: Path) -> dict[str, bytes]:
    path = out / "source-bytes"
    files = {name: (path / f"before.{name}.bin").read_bytes()
             for name in ("raw", "typed", "selector", "catalog")}
    if len(files["raw"]) != 8192:
        raise ValueError("Staged fixture SRAM is wrong size")
    return files


def command(launcher: Path, user: Path, work: Path,
            script: Path, timeout: int, *, full: bool) -> tuple[int, str]:
    config = work / "real-ntfs-game-config.ini"
    if not config.is_file():
        config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    for key in ("UR_BALDOSA_RECOVERY_ACTION",
                "UR_BALDOSA_RECOVERY_PROFILE_ID",
                "UR_BALDOSA_QA_POSTRAW_TYPED_DENIAL_GATE",
                "UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE",
                "UR_BALDOSA_QA_CRASH_AFTER_INTENT_BEFORE_RAW"):
        env.pop(key, None)
    env.update({
        "UR_RECOMP_USER_DATA_ROOT": str(user),
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_BALDOSA_NO_HOLD": "1",
        "SDL_VIDEODRIVER": "windows",
        "SDL_AUDIODRIVER": "dummy",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
    })
    if full:
        env.update({
            "UR_BALDOSA_MODERN_INPUT": "1",
            "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "1",
            "UR_BALDOSA_PAUSE_SMOKE": "1",
            "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1",
            "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "2200",
            "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1",
            "UR_BALDOSA_PAUSE_QUIT_SMOKE": "1",
            "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "0",
            "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
            "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
        })
    else:
        for key in ("UR_BALDOSA_PAUSE_SMOKE", "UR_BALDOSA_PAUSE_REQUIRE_RACE",
                    "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE",
                    "UR_BALDOSA_PAUSE_QUIT_SMOKE",
                    "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE"):
            env.pop(key, None)
    args = ["cmd.exe", "/d", "/c", "call", str(launcher),
            "--config", str(config), "--script", str(script)]
    result = subprocess.run(
        args, cwd=work, env=env, timeout=timeout,
        capture_output=True, text=True, errors="replace")
    return result.returncode, result.stdout + "\n" + result.stderr


def ensure_rom(launcher: Path, rom: Path):
    if os.name != "nt" or not launcher.is_file() or not rom.is_file() or \
       rom.is_symlink() or digest(rom.read_bytes()) != USA_SHA256:
        raise ValueError("Original verified USA ROM, original CMD and Win32 required")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("ROM-free candidate already holds an installed ROM")
    shutil.copyfile(rom, installed)
    if digest(installed.read_bytes()) != USA_SHA256:
        installed.unlink(missing_ok=True)
        raise ValueError("Temporary original USA ROM did not match hash")
    return installed


def run(phase: str, launcher: Path, rom: Path, fixture: Path,
        seed: Path, user: Path, out: Path, timeout: int) -> None:
    if not user.is_absolute() or user.drive.upper() != "W:" or \
       not os.environ.get("GITHUB_ACTIONS") == "true":
        raise ValueError("Only disposable W: isolated real NTFS hosted Windows user root")
    out.mkdir(parents=True, exist_ok=True)
    if phase == "prepare":
        if user.exists():
            raise ValueError("Preexisting original source user root")
        user.mkdir()
        init = subprocess.run([str(fixture), str(user), str(seed)],
                              capture_output=True, text=True, check=True,
                              timeout=timeout)
        (out / "fixture.log").write_text(init.stdout + init.stderr,
                                         encoding="utf-8")
        warm = out / "warm-cold.txt"
        warm.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
        installed = ensure_rom(launcher, rom)
        try:
            rc, log = command(launcher, user, out, warm, timeout, full=False)
        finally:
            installed.unlink(missing_ok=True)
        (out / "warm.log").write_text(log, encoding="utf-8")
        if rc or "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider" not in log:
            raise ValueError("Original warm game failed before NTFS filling: " +
                             log[-1700:])
        saved = snapshot(user)
        if list(user.rglob("native-sram-checkpoint.pending")):
            raise ValueError("Warm source created pending recovery")
        retain(out, "before", saved)
        (out / "candidate.json").write_text(
            json.dumps({"cmd_sha256": digest(launcher.read_bytes()),
                        "fixture_sha256": digest(fixture.read_bytes()),
                        "seed_sha256": digest(seed.read_bytes()),
                        "original_rom_sha256": USA_SHA256,
                        "base": {k: {"sha256": digest(v), "bytes": len(v)}
                                 for k, v in sorted(saved.items())}},
                       indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return

    previous = baseline(out)
    if snapshot(user) != previous:
        raise ValueError("Canonical source mutated outside original game phase")
    if phase == "full":
        # Real physical NTFS capacity should be 0-4095 free bytes after
        # the PowerShell apparatus filled it and independent OS process
        # observed Win32 112. Never emulate disk-full with path permissions.
        proof = json.loads((out / "real-ntfs-substrate.json").read_text())
        if proof.get("fresh_process_os_error") != 112:
            raise ValueError("No independent real NTFS Win32 112 proof")
        route = native_modern_race_entry_script(1)
        if route.count("dump go\nquit\n") != 1:
            raise ValueError("Source exact Modern Play route changed")
        route = route.replace("dump go\nquit\n", "dump go\nwait 700\nquit\n")
        script = out / "real-ntfs-modern-play.txt"
        script.write_text(route, encoding="ascii")
        installed = ensure_rom(launcher, rom)
        try:
            rc, log = command(launcher, user, out, script, timeout, full=True)
        finally:
            installed.unlink(missing_ok=True)
        (out / "full-ntfs-original-CMD.log").write_text(log, encoding="utf-8")
        after = snapshot(user)
        retain(out, "actual-full", after)
        (out / "full-process.json").write_text(
            json.dumps({"native_cmd_exit": rc,
                        "full_original_raw_sha256": digest(after["raw"]),
                        "before_raw_sha256": digest(previous["raw"]),
                        "original_full_ntfs_cmd_sha256": digest(launcher.read_bytes()),
                        "original_guest_save_message": "UR-BALDOSA-SAVE-FAILED:" in log,
                        "original_game_race_armed": "UR_BALDOSA_NATIVE_PAUSE ARMED guest=2200" in log,
                        "canonical_equal_before_after": after == previous,
                        "qa_gate_credit": 0}, indent=2) + "\n",
            encoding="utf-8")
        if (after != previous or rc != 8 or
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=2200" not in log or
            "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1" not in log or
            "UR-BALDOSA-SAVE-FAILED: This game session could not finish saving."
            not in log or
            "UR-BALDOSA-SAVE-FAILED: Native save could not complete." not in log or
            "UR-BALDOSA-FIRST-RACER:" in log or
            "UR-BALDOSA-RECOVERY-COMMITTED:" in log):
            raise ValueError("Actual full NTFS source game did not safely refuse save: " +
                             log[-2600:])
        return
    if phase != "cold":
        raise ValueError("Unknown original source disk-full phase")
    short = out / "warm-cold.txt"
    installed = ensure_rom(launcher, rom)
    try:
        for number in (1, 2):
            rc, log = command(launcher, user, out, short, timeout, full=False)
            (out / f"cold-{number}.log").write_text(log, encoding="utf-8")
            saved = snapshot(user)
            retain(out, f"cold{number}", saved)
            if (rc or saved != previous or
                "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider" not in log or
                "UR-BALDOSA-STARTUP-PROFILE-REJECTED" in log or
                list(user.rglob("native-sram-checkpoint.pending"))):
                raise ValueError("Actual original cold boot after freeing real NTFS volume changed save")
    finally:
        installed.unlink(missing_ok=True)
    evidence = out / "source-bytes"
    receipts = {p.name: {"bytes": p.stat().st_size,
                         "sha256": digest(p.read_bytes())}
                for p in sorted(evidence.glob("*.bin"))}
    if len(receipts) != 16:
        raise ValueError("Expected exact 4 x 4 original source byte objects")
    (out / "result.json").write_text(
        json.dumps({"schema": "ur-real-original-cmd-ntfs-disk-full/1",
                    "actual_isolated_vhd_ntfs_full": True,
                    "actual_native_cmd_exit8_during_original_guest_save": True,
                    "exact_before_full_two_cold_binary_members": receipts,
                    "original_cmd_sha256": digest(launcher.read_bytes()),
                    "original_fixture_sha256": digest(fixture.read_bytes()),
                    "human_operator": False,
                    "real_power_loss_or_partial_write": False,
                    "release_gate_credit": 0},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prepare", "full", "cold"), required=True)
    for name in ("launcher", "rom", "fixture", "seed", "user", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    run(args.phase, args.launcher.resolve(), args.rom.resolve(),
        args.fixture.resolve(), args.seed.resolve(), args.user,
        args.out.resolve(), args.timeout)


if __name__ == "__main__":
    main()
