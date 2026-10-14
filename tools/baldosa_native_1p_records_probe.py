#!/usr/bin/env python3
"""One real Baldosa Win32 Modern 1P result -> canonical Records -> fresh game read.

Reuses the executable, profile codec fixture, source stock script grammar and
read-only root presenter in baldosa_windows_native_pause_route.py. This is a
product integration witness; it makes NO original/native parity, controller
hardware, or release-certification assertion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from baldosa_windows_native_pause_route import (
    USA_SHA256,
    native_modern_race_entry_script,
    verify_named_profile_boot_bytes,
    verify_native_profile_checkpoint,
    sha256,
)

PROFILE = "native-ci-rider"
FINISH_CONTROLS = (
    "press right 600",
    "press right+a 30",
    "press right 600",
    "press right+up 60",
    "press right 900",
    "press right+b 30",
    "press right 1200",
)


def source_finish_script() -> str:
    """Extend the already-executed Modern root -> source GO route, not menus."""
    base = native_modern_race_entry_script(1)
    tail = "dump go\nquit\n"
    if not base.endswith(tail):
        raise ValueError("Native Modern stock GO grammar changed")
    return (base[:-len(tail)] + "dump go\n" +
            "\n".join(FINISH_CONTROLS) +
            "\nuntil 009F == 99 12000\nwait 60\n"
            "dump observed-source-result\nquit\n")


def source_result_published(log: str) -> None:
    required = (
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
        "UR_BALDOSA_NATIVE_RUN CAPTURED=1 mode=race-1p "
        "profile=native-ci-rider course=course:01 ",
        "UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p ",
    )
    if any(log.count(marker) != 1 for marker in required):
        raise ValueError("Real Modern guest did not uniquely publish source 1P result")
    result = re.search(
        r"(?m)^UR_BALDOSA_NATIVE_RESULT observed=1 mode=race-1p "
        r"race_host=(\d+) result_host=(\d+) finish_ticks60=(\d+) "
        r"input_frames=(\d+) input_runs=(\d+) published=(\d+)$", log)
    if (not result or int(result[6]) != 1 or int(result[3]) <= 0 or
            int(result[1]) >= int(result[2]) or int(result[4]) == 0 or
            "UR_BALDOSA_NATIVE_RUN SAVE_PENDING=1" in log or
            "UR_BALDOSA_NATIVE_RUN NOT_SAVED=1" in log):
        raise ValueError("Original-source finish never committed a real 1P run")


def native_records_reopened(log: str) -> None:
    required = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider ",
        "UR_BALDOSA_MODERN_ROOT records_opened=1 "
        "profile=selected validated=1 unavailable=0",
    )
    if any(log.count(marker) != 1 for marker in required):
        raise ValueError("Fresh game process did not reopen exactly one new run")
    if ("UR_BALDOSA_NATIVE_RUN CAPTURED=1" in log or
            "UR_BALDOSA_NATIVE_RESULT observed=1" in log):
        raise ValueError("Read-only fresh-game Records session minted another run")


def run_game(exe: Path, rom: Path, work: Path, user: Path,
             *, script: str, video: str, timeout: int) -> str:
    work.mkdir(parents=True, exist_ok=False)
    route = work / "stock-input-route.txt"
    route.write_text(script, encoding="ascii")
    config = work / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "UR_BALDOSA_PAUSE_SMOKE": "0",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    try:
        process = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(route), str(rom)], cwd=work, env=env,
            capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Real stock source-result route timed out") from exc
    log = process.stdout + "\n" + process.stderr
    (work / "log.txt").write_text(log, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(
            f"Native Windows guest exited {process.returncode}: {log[-2700:]}")
    return log


def run(exe: Path, rom: Path, fixture: Path, seed: Path, output: Path,
        *, video: str, timeout: int) -> dict[str, object]:
    for candidate in (exe, rom, fixture, seed):
        if not candidate.is_file() or candidate.is_symlink():
            raise ValueError(f"Missing or redirected verified input: {candidate}")
    if sha256(rom) != USA_SHA256 or seed.stat().st_size != 8192:
        raise ValueError("Missing exact USA ROM or 8192-byte stock SRAM seed")
    output.mkdir(parents=True, exist_ok=False)
    user = output / "Existing Modern Player Data With Spaces"
    user.mkdir()
    fixture_result = subprocess.run(
        [str(fixture), str(user), str(seed)], cwd=output,
        capture_output=True, text=True, timeout=timeout)
    if fixture_result.returncode:
        raise RuntimeError("Existing canonical Modern profile fixture failed: " +
                           fixture_result.stderr[-2000:])

    first = run_game(exe, rom, output / "played_native_event", user,
                     script=source_finish_script(), video=video,
                     timeout=timeout)
    source_result_published(first)
    archive = user / "runs" / PROFILE
    runs = list(archive.glob("*.urrun")) if archive.is_dir() else []
    if len(runs) != 1 or runs[0].is_symlink():
        raise ValueError("Real native 1P event did not create one canonical run")
    existing = runs[0].read_bytes()
    record_sha256 = hashlib.sha256(existing).hexdigest()
    if len(existing) == 0:
        raise ValueError("Guest published an empty Records artifact")
    verify_native_profile_checkpoint(fixture, user, PROFILE, first, timeout)
    selected_sram = user / "saves" / f"profile-{PROFILE}" / "save.srm"
    saved_sram = selected_sram.read_bytes()
    if len(saved_sram) != 8192:
        raise ValueError("Native source result damaged named 8192-byte SRAM")
    second = run_game(
        exe, rom, output / "fresh_game_records", user,
        script="turbo on\nwait 1800\nquit\n",
        video=video, timeout=timeout)
    verify_named_profile_boot_bytes(second, saved_sram)
    native_records_reopened(second)
    if runs[0].read_bytes() != existing or len(list(archive.glob("*.urrun"))) != 1:
        raise ValueError("Fresh game Records inspection changed the saved run")
    if (user / "saves/save.srm").exists():
        raise ValueError("Named native Records leaked into anonymous SRAM")
    verify_native_profile_checkpoint(fixture, user, PROFILE, second, timeout)
    return {
        "scope": "native-windows-modern-real-guest-1p-product-integration",
        "source": "pinned Baldosa AOT stock 1P result, existing Modern codecs",
        "source_revision_note": "executable identity supplied by owning CI job",
        "first_process_source_result_published": True,
        "newly_persisted_urrun_count": 1,
        "new_run_sha256": record_sha256,
        "second_native_game_process_reopened_exact_new_record": True,
        "second_process_reloaded_previous_native_sram": True,
        "original_native_strict_event_pass": False,
        "physical_controller_hardware_tested": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("exe", "rom", "fixture", "seed", "out"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--timeout", type=int, default=95)
    args = parser.parse_args()
    paths = [getattr(args, key).resolve()
             for key in ("exe", "rom", "fixture", "seed", "out")]
    data = run(*paths, video=args.video, timeout=args.timeout)
    report = paths[-1] / "report.json"
    report.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print("PASS: original native Windows 1P source result -> real saved run -> "
          "fresh game Records readback; no original/native or physical credit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
