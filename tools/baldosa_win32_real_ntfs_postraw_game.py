#!/usr/bin/env python3
"""Original packaged Windows game: genuinely full NTFS AFTER raw/before typed.

Separate product research evidence. Caller has mounted a checked disposable
W: NTFS VHDX with enough free space. The original game's source gate freezes
a genuine racer after raw+durable intent but before typed metadata. This
producer fills W: using flushed OS writes, independently verifies Win32 112
from another process, releases the original game, then cold-reconciles twice.
No real partial-write/power-cut or human release credit.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import time

from baldosa_win32_real_ntfs_diskfull_game import (
    command, ensure_rom, retain, snapshot,
)
from baldosa_win32_interactive_recovery_q import digest
from baldosa_windows_native_pause_route import (
    native_modern_race_entry_script, verify_named_profile_boot_bytes,
)

ARMED = ("UR_BALDOSA_NATIVE_PROFILE QA_POSTRAW_TYPED_GATE "
         "native_raw_written=1 typed_not_attempted=1")


def original_child_env(user: Path, gate: Path) -> dict[str, str]:
    env = os.environ.copy()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetWindowsDirectoryW.argtypes = (wintypes.LPWSTR, wintypes.UINT)
    kernel.GetWindowsDirectoryW.restype = wintypes.UINT
    buf = ctypes.create_unicode_buffer(32768)
    length = kernel.GetWindowsDirectoryW(buf, len(buf))
    if not (0 < length < len(buf)):
        raise ctypes.WinError(ctypes.get_last_error())
    windows = Path(buf.value)
    stock = windows / "System32" / "WindowsPowerShell" / "v1.0" / "Modules"
    if not windows.is_absolute() or not windows.is_dir() or not stock.is_dir():
        raise ValueError("Stock Windows PowerShell module directory absent")
    roots = [str(stock)]
    program_files = Path(env.get("ProgramFiles", ""))
    machine = program_files / "WindowsPowerShell" / "Modules"
    if program_files.is_absolute() and machine.is_dir():
        roots.append(str(machine))
    env["PSModulePath"] = os.pathsep.join(roots)
    for name in ("UR_BALDOSA_RECOVERY_ACTION", "UR_BALDOSA_RECOVERY_PROFILE_ID",
                 "UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE",
                 "UR_BALDOSA_QA_CRASH_AFTER_INTENT_BEFORE_RAW"):
        env.pop(name, None)
    env.update({
        "UR_RECOMP_USER_DATA_ROOT": str(user),
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_BALDOSA_NO_HOLD": "1",
        "SDL_VIDEODRIVER": "windows",
        "SDL_AUDIODRIVER": "dummy",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
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
        "UR_BALDOSA_QA_POSTRAW_TYPED_DENIAL_GATE": str(gate),
    })
    return env


def fill_and_independent_os_112(user: Path, out: Path) -> dict:
    """Write only to W: while original native game's locks remain held."""
    filler = user.parent / "ur-postraw-only-flushed-filler.bin"
    second = user.parent / "ur-postraw-only-second-8192.bin"
    if filler.exists() or second.exists():
        raise ValueError("Isolated NTFS filler targets already exist")
    accepted = 0
    witnessed = False
    stream = open(filler, "xb", buffering=0)
    try:
        for width in (1048576, 4096, 1):
            block = bytes(width)
            for attempt in range(16384):
                try:
                    amount = stream.write(block)
                    if amount != width:
                        raise ValueError("Genuine short NTFS write, not full-write proof")
                    os.fsync(stream.fileno())
                    accepted += amount
                except OSError as exc:
                    if getattr(exc, "winerror", None) not in (112, 39):
                        raise
                    witnessed = True
                    break
            else:
                raise ValueError("Bounded flush-filler attempt limit exceeded")
    finally:
        try:
            stream.close()
        except OSError as exc:
            if getattr(exc, "winerror", None) not in (112, 39):
                raise
            witnessed = True
    if not witnessed:
        raise ValueError("Actual W: disk full never observed")
    child = out / "independent-real-ntfs-112.ps1"
    child.write_text(
        "param([string]$Path)\n"
        "try { [IO.File]::WriteAllBytes($Path, ([byte[]]::new(8192))); exit 9 }\n"
        "catch [IO.IOException] { $code = $_.Exception.HResult -band 0xffff; "
        "if ($code -eq 112 -or $code -eq 39) { exit 112 }; exit 2 }\n",
        encoding="ascii",
    )
    checked = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
         "-ExecutionPolicy", "Bypass", "-File", str(child),
         "-Path", str(second)],
        timeout=20, capture_output=True, text=True,
    )
    (out / "second-process-112.log").write_text(
        f"exit={checked.returncode}\n" + checked.stdout + checked.stderr,
        encoding="utf-8",
    )
    if checked.returncode != 112:
        raise ValueError("Another real Windows process did not report ERROR_DISK_FULL")
    return {"actual_fsync_filler_bytes": accepted,
            "first_process_real_ntfs_full": True,
            "second_process_win32_error": 112}


def run(launcher: Path, rom: Path, fixture: Path, seed: Path,
        user: Path, out: Path, timeout: int) -> dict:
    if (os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true" or
        not user.is_absolute() or user.drive.upper() != "W:" or
        not user.is_dir() or out.exists() or out.drive.upper() == "W:"):
        raise ValueError("Requires new output and isolated live Windows W: profile")
    out.mkdir(parents=True)
    original = snapshot(user)
    pending = user / "saves/profile-native-ci-rider/native-sram-checkpoint.pending"
    if pending.exists():
        raise ValueError("Original fixture already has pending journal")
    retain(out, "before", original)
    short = out / "cold-original.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    route = native_modern_race_entry_script(1)
    if route.count("dump go\nquit\n") != 1:
        raise ValueError("Canonical original 1P source GO route changed")
    script = out / "real-original-postraw-1p-route.txt"
    script.write_text(route.replace("dump go\nquit\n",
                                    "dump go\nwait 700\nquit\n"),
                      encoding="ascii")
    config = out / "postraw-config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    gate = out / "original-postraw-release.ready"
    installed = ensure_rom(launcher, rom)
    proc = None
    middle = None
    after = None
    intent = None
    full = None
    failure_exit = None
    log_path = out / "real-postraw-full-original-CMD.log"
    try:
        env = original_child_env(user, gate)
        cmd = ["cmd.exe", "/d", "/c", "call", str(launcher),
               "--config", str(config), "--script", str(script)]
        with log_path.open("wb") as sink:
            proc = subprocess.Popen(
                cmd, cwd=out, env=env, stdout=sink, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    log = log_path.read_text(encoding="utf-8", errors="replace")
                    if ARMED in log:
                        break
                    if proc.poll() is not None:
                        raise ValueError("Original guest died before postraw: " +
                                         log[-2000:])
                    time.sleep(0.025)
                else:
                    raise TimeoutError("Original guest did not reach postraw gate")
                if proc.poll() is not None or log.count(ARMED) != 1:
                    raise ValueError("Postraw original game gate not uniquely alive")
                middle = snapshot(user)
                retain(out, "postraw", middle)
                if not pending.is_file() or pending.is_symlink():
                    raise ValueError("Original durable pending intent is missing")
                intent = pending.read_bytes()
                (out / "source-bytes" / "intent.postraw.bin").write_bytes(intent)
                if (len(intent) < 8192 or middle["raw"] == original["raw"] or
                    middle["typed"] != original["typed"] or
                    middle["selector"] != original["selector"] or
                    middle["catalog"] != original["catalog"]):
                    raise ValueError("Original Windows stage not raw-written/typed-old")
                verify_named_profile_boot_bytes(log, original["raw"])
                # Actual 128MiB NTFS volume is still free at the source gate.
                # Write/flush to a sibling W: file, never an authoritative
                # profile, and require a distinct Win32 process's error 112.
                full = fill_and_independent_os_112(user, out)
                if proc.poll() is not None:
                    raise ValueError("Original game exited during external full-volume fill")
                gate.write_text("real-independent-error-112-observed\n",
                                encoding="ascii")
                proc.wait(timeout=timeout)
                failure_exit = proc.returncode
            finally:
                if proc.poll() is None:
                    try:
                        gate.write_text("aborting-unverified-source-test\n",
                                        encoding="ascii")
                    except OSError:
                        pass
                    proc.kill()
                    proc.wait(timeout=30)
        after = snapshot(user)
        retain(out, "denied", after)
        (out / "full-postraw-result.json").write_text(
            json.dumps({"schema": "ur-original-postraw-real-ntfs-stage/1",
                        "full_volume": full, "native_exit": failure_exit,
                        "after_equals_postraw": after == middle},
                       indent=2, sort_keys=True) + "\n")
        log = log_path.read_text(encoding="utf-8", errors="replace")
        if (failure_exit != 8 or full is None or after != middle or
            not pending.is_file() or pending.read_bytes() != intent or
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider status=io_error"
            not in log or "UR-BALDOSA-SAVE-FAILED:" not in log or
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=2200" not in log or
            "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1" not in log or
            "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider status=committed"
            in log or list(user.rglob("*.urrun")) or
            list(user.rglob("*.urmatch")) or list(user.rglob("*.urghost"))):
            raise ValueError("Postraw genuine NTFS typed failure unproven: " +
                             log[-2200:])
        # Free only our disposable filler after preserving the rejected
        # source state and while the original source game is no longer alive.
        (user.parent / "ur-postraw-only-flushed-filler.bin").unlink()
        (user.parent / "ur-postraw-only-second-8192.bin").unlink(missing_ok=True)
        rc1, log1 = command(launcher, user, out, short, timeout, full=False)
        (out / "cold-1-original-CMD.log").write_text(log1, encoding="utf-8")
        recovered = snapshot(user)
        retain(out, "recovered", recovered)
        receipt = list((user / "saves/profile-native-ci-rider").glob(
            "native-sram-recovered-*.txt"))
        if (rc1 or log1.count(
                "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED "
                "exact_staged_guest_sram=1 no_records=1") != 1 or
            recovered["raw"] != middle["raw"] or
            recovered["typed"] == middle["typed"] or
            recovered["selector"] != middle["selector"] or
            recovered["catalog"] != middle["catalog"] or
            pending.exists() or len(receipt) != 1 or
            receipt[0].read_bytes() != intent):
            raise ValueError("First genuine Windows cold boot did not reconcile intent")
        verify_named_profile_boot_bytes(log1, middle["raw"])
        (out / "source-bytes" / "intent.recovery-receipt.bin").write_bytes(
            receipt[0].read_bytes())
        rc2, log2 = command(launcher, user, out, short, timeout, full=False)
        (out / "cold-2-original-CMD.log").write_text(log2, encoding="utf-8")
        second = snapshot(user)
        retain(out, "cold2", second)
        if (rc2 or "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in log2 or
            second != recovered or pending.exists() or
            receipt[0].read_bytes() != intent or
            list(user.rglob("*.urrun")) or list(user.rglob("*.urmatch"))):
            raise ValueError("Second source cold boot replayed or mutated recovery")
        verify_named_profile_boot_bytes(log2, middle["raw"])
        receipts = {
            p.name: {"bytes": p.stat().st_size, "sha256": digest(p.read_bytes())}
            for p in (out / "source-bytes").glob("*.bin")
        }
        if len(receipts) != 22:
            raise ValueError("Postraw source must retain 22 canonical/intent binaries")
        result = {
            "schema": "ur-real-win32-ntfs-full-postraw-typed/1",
            "actual_raw_plus_durable_intent_before_disk_full": True,
            "original_source_postraw_typed_refused_exit8": True,
            "independent_second_process_win32_error": 112,
            "recovery_intent_reconciled_once": True,
            "two_fresh_original_Windows_cold_boots": True,
            "original_cmd_sha256": digest(launcher.read_bytes()),
            "native_fixture_sha256": digest(fixture.read_bytes()),
            "actual_source_bytes": receipts,
            "release_gate_credit": 0,
            "human_operator": False,
            "electrical_power_cut_or_partial_disk_write": False,
        }
        (out / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    finally:
        installed.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("launcher", "rom", "fixture", "seed", "user", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    a = parser.parse_args()
    print(json.dumps(
        run(a.launcher.resolve(), a.rom.resolve(), a.fixture.resolve(),
            a.seed.resolve(), a.user, a.out.resolve(), a.timeout),
        sort_keys=True))


if __name__ == "__main__":
    main()
