#!/usr/bin/env python3
"""Actual extracted Windows CMD R/T recovery menu, real console key events.

A narrow, product-owned witness, not a physical human/controller QA result.
Preserves original-format BEFORE and AFTER raw/typed/catalog/selector bytes,
the exact manual archive, two fresh original CMD cold boots, and console logs.
Uses the same proven separate Win32 console injector as the Q witness.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from assemble_baldosa_windows_candidate import ROM, USA_SHA256
from baldosa_win32_interactive_recovery_q import digest, snapshot


def stock_sram(typed: bytes) -> bytes:
    lines = typed.splitlines()
    fields = [line[len(b"stock_sram="):] for line in lines
              if line.startswith(b"stock_sram=")]
    if len(fields) != 1 or len(fields[0]) != 16384:
        raise ValueError("Typed original profile lacks canonical 8192-byte SRAM")
    try:
        raw = bytes.fromhex(fields[0].decode("ascii"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("Original typed SRAM must be hexadecimal") from exc
    if len(raw) != 8192:
        raise ValueError("Original typed SRAM size invalid")
    return raw


def retain(folder: Path, stage: str, states: dict[str, bytes],
           receipts: dict[str, dict]) -> None:
    if set(states) != {"selector", "catalog", "typed", "raw"}:
        raise ValueError("Incomplete canonical source state")
    folder.mkdir(parents=True, exist_ok=True)
    for key, content in sorted(states.items()):
        name = stage + "." + key + ".bin"
        (folder / name).write_bytes(content)
        receipts[name] = {"bytes": len(content), "sha256": digest(content)}


def forced_stop_tree(proc: subprocess.Popen) -> None:
    """Terminate a running ORIGINAL game only after recording its first frame.

    Original CMD starts a child executable. Terminating cmd alone would leak
    the source native game, its OS locks and an uncontrolled save writer.
    """
    if proc.poll() is None:
        stop = subprocess.run(
            ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True, text=True, timeout=25)
        if stop.returncode != 0 and proc.poll() is None:
            raise ValueError("Could not terminate exact original CMD process tree: "
                             + stop.stdout[-600:] + stop.stderr[-600:])
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.wait(timeout=20)
        raise ValueError("Original CMD remained live after tree shutdown") from exc


def launch_until_first_frame(launcher: Path, user: Path, root: Path,
                             name: str, *, key: str | None,
                             timeout: int,
                             profile_id: str | None = None) -> tuple[str, bool]:
    transcript = root / (name + ".log")
    wrapper = root / (name + ".cmd")
    wrapper.write_text(
        "@echo off\n"
        + f'call "{launcher}" >"{transcript}" 2>&1\n'
        + "exit /b %ERRORLEVEL%\n", encoding="utf-8")
    env = os.environ.copy()
    for inherited in ("UR_BALDOSA_NO_HOLD", "UR_BALDOSA_RECOVERY_ACTION",
                      "UR_BALDOSA_RECOVERY_PROFILE_ID"):
        env.pop(inherited, None)
    env.update({
        "UR_RECOMP_USER_DATA_ROOT": str(user),
        "SDL_AUDIODRIVER": "dummy",
        "SDL_VIDEODRIVER": "windows",
    })
    proc = subprocess.Popen(
        ["cmd.exe", "/d", "/c", "call", str(wrapper)],
        cwd=launcher.parent, env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE)
    prompt = "Explicit recovery choice [R/T/S/Q]:"
    marker = "first frame simulated"
    injected = False
    entered_profile = False
    finished = False
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            text = (transcript.read_text(encoding="utf-8", errors="replace")
                    if transcript.is_file() else "")
            if key and not injected and prompt in text:
                injector = subprocess.run(
                    [sys.executable, str(
                        Path(__file__).with_name(
                            "baldosa_win32_interactive_recovery_q.py")),
                     "--inject-console-key", key, str(proc.pid)],
                    cwd=root, capture_output=True, text=True, timeout=25)
                (root / (name + ".key.log")).write_text(
                    f"exit={injector.returncode}\n" +
                    injector.stdout + "\n" + injector.stderr,
                    encoding="utf-8")
                if injector.returncode != 0:
                    raise ValueError("Real original CMD " + key +
                                     " console key was not admitted")
                injected = True
            if (profile_id and injected and not entered_profile and
                    "Healthy registered profile ID:" in text):
                injector = subprocess.run(
                    [sys.executable, str(
                        Path(__file__).with_name(
                            "baldosa_win32_interactive_recovery_q.py")),
                     "--inject-console-text", str(proc.pid), profile_id],
                    cwd=root, capture_output=True, text=True, timeout=25)
                (root / (name + ".profile.log")).write_text(
                    f"exit={injector.returncode}\n" +
                    injector.stdout + "\n" + injector.stderr,
                    encoding="utf-8")
                if injector.returncode != 0:
                    raise ValueError("CMD S profile-ID input was refused")
                entered_profile = True
            if marker in text:
                finished = True
                break
            if proc.poll() is not None:
                raise ValueError("Original CMD exited before live guest frame: "
                                 + text[-1800:])
            time.sleep(0.03)
        if not finished:
            raise TimeoutError("Original CMD no-argument game did not start")
    finally:
        forced_stop_tree(proc)
    text = transcript.read_text(encoding="utf-8", errors="replace")
    if key:
        if (not injected or
            (profile_id is not None and not entered_profile) or
            text.count(prompt) != 1 or
            prompt + " " + key not in text or
            text.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") != 1 or
            text.count("UR-BALDOSA-RECOVERY-COMMITTED:") != 1 or
            "UR-BALDOSA-RECOVERY-REFUSED:" in text or
            "UR-BALDOSA-RECOVERY-RETRY-FAILED:" in text or
            "UR-BALDOSA-FIRST-RACER:" in text):
            raise ValueError("Original interactive " + key +
                             " did not commit exactly once before relaunch")
    elif (prompt in text or "UR-BALDOSA-RECOVERY-" in text or
          "UR-BALDOSA-STARTUP-PROFILE-REJECTED:" in text):
        raise ValueError("Cold source guest unexpectedly entered recovery UI")
    if text.count(marker) != 1:
        raise ValueError("Native guest must cross exactly one real first frame")
    return text, injected


def run_case(launcher: Path, fixture: Path, seed: Path,
             root: Path, choice: str, timeout: int,
             noncanonical_typed: bool = False) -> dict:
    root.mkdir()
    user = root / "Original Player With Spaces"
    user.mkdir()
    init = subprocess.run([str(fixture), str(user), str(seed)],
                          capture_output=True, text=True, check=True,
                          timeout=timeout)
    (root / "fixture.log").write_text(
        init.stdout + "\n" + init.stderr, encoding="utf-8")
    raw = user / "saves/profile-native-ci-rider/save.srm"
    typed_file = raw.with_name("host-profile.txt")
    if noncanonical_typed:
        if choice != "R":
            raise ValueError("Only explicit R is covered by this source witness")
        canonical = typed_file.read_bytes()
        header, separator, remainder = canonical.partition(b"\n")
        if (not separator or not remainder or
            not header.startswith(b"UR-HOST-PROFILE/")):
            raise ValueError("Original typed fixture header not recognized")
        changed_typed = header + separator + b"\n" + remainder
        typed_file.write_bytes(changed_typed)
        if typed_file.read_bytes() != changed_typed:
            raise ValueError("Exact noncanonical source profile bytes were lost")
    first = snapshot(user)
    if stock_sram(first["typed"]) != first["raw"]:
        raise ValueError("Fixture did not produce matching typed/raw pair")
    if noncanonical_typed and not first["typed"].startswith(
        b"UR-HOST-PROFILE/5\n\n"
    ):
        raise ValueError("Noncanonical original typed source did not persist")
    damaged = bytearray(first["raw"])
    damaged[256] ^= 1
    raw.write_bytes(damaged)
    before = snapshot(user)
    if (before["raw"] == first["raw"] or
        before["raw"][:16] != first["raw"][:16] or
        any(before[x] != first[x]
            for x in ("typed", "catalog", "selector"))):
        raise ValueError("Failed to set one-byte historical unjournaled mismatch")
    if list(user.rglob("native-sram-checkpoint.pending")):
        raise ValueError("Legacy raw mismatch must not have a pending intent")
    receipts: dict[str, dict] = {}
    byte_root = root / "source-bytes"
    retain(byte_root, "before-" + choice, before, receipts)
    transcript, injected = launch_until_first_frame(
        launcher, user, root, "interactive-" + choice,
        key=choice, timeout=timeout)
    after = snapshot(user)
    retain(byte_root, "after-" + choice, after, receipts)
    if not injected or after["selector"] != before["selector"] or \
       after["catalog"] != before["catalog"] or \
       after["raw"] != (before["raw"] if choice == "R" else first["raw"]) or \
       stock_sram(after["typed"]) != after["raw"]:
        raise ValueError(choice + " altered unauthorized canonical authority")
    if choice == "T" and after["typed"] != before["typed"]:
        raise ValueError("T must retain exactly the committed typed profile")
    if choice == "R" and after["typed"] == before["typed"]:
        raise ValueError("R must advance typed metadata to selected guest SRAM")
    if noncanonical_typed and (after["typed"].startswith(
        b"UR-HOST-PROFILE/5\n\n"
    ) or after["typed"] == first["typed"]):
        raise ValueError("R did not commit the canonical next profile state")
    archives = list(user.rglob("native-sram-manual-archive-*.bin"))
    if len(archives) != 1 or archives[0].is_symlink():
        raise ValueError("Expected exactly one real immutable manual receipt")
    archive = archives[0].read_bytes()
    header = (b"UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n"
              + str(len(before["typed"])).encode("ascii")
              + b"\n1\n8192\n")
    if archive != header + before["typed"] + before["raw"]:
        raise ValueError("Original archive failed full pre-mutation byte equality")
    (byte_root / ("manual-" + choice + ".bin")).write_bytes(archive)
    receipts["manual-" + choice + ".bin"] = {
        "sha256": digest(archive), "bytes": len(archive)}
    if list(user.rglob("native-sram-checkpoint.pending")) or \
       list(user.rglob("native-sram-recovered-intent-*.bin")):
        raise ValueError("Legacy repair invented pending intent or replay authority")
    # The same actual no-argument extracted Windows CMD, twice from new OS
    # processes, must select the newly consistent named racer without repair.
    for cold in (1, 2):
        launch_until_first_frame(
            launcher, user, root, "cold-" + choice + "-" + str(cold),
            key=None, timeout=timeout)
        current = snapshot(user)
        retain(byte_root, f"cold{cold}-" + choice, current, receipts)
        if current != after or list(
                user.rglob("native-sram-manual-archive-*.bin")) != archives or \
           archives[0].read_bytes() != archive:
            raise ValueError("Original cold restart mutated repaired authority")
    result = {
        "schema": ("ur-win32-interactive-noncanonical-raw-r/1"
                   if noncanonical_typed else
                   "ur-win32-interactive-original-cmd-rt/1"),
        "noncanonical_original_typed_file_archived_exact": noncanonical_typed,
        "choice": choice,
        "exact_extracted_cmd_sha256": digest(launcher.read_bytes()),
        "original_seed_sha256": digest(seed.read_bytes()),
        "actual_console_key_injected": injected,
        "original_cmd_recovery_committed_once": (
            transcript.count("UR-BALDOSA-RECOVERY-COMMITTED:") == 1),
        "original_first_frame_after_relaunch": True,
        "original_first_frame_on_two_cold_boots": True,
        "source_before_after_and_cold_bytes": receipts,
        "legacy_raw_byte_changes": sum(x != y for x, y in zip(
            first["raw"], before["raw"])),
        "manual_archive_exact_previous_raw_and_typed": True,
        "unchanged_catalog_and_selector": True,
        "independent_release_gate_credit": 0,
    }
    (root / "result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def run_with_rom(launcher: Path, rom: Path, fixture: Path,
                 seed: Path, root: Path, timeout: int,
                 noncanonical_r_only: bool = False) -> dict:
    if os.name != "nt":
        raise ValueError("Real Win32 console required")
    if root.exists() or not launcher.is_file() or not fixture.is_file() or \
       not seed.is_file() or not rom.is_file() or rom.is_symlink() or \
       digest(rom.read_bytes()) != USA_SHA256:
        raise ValueError("Require fresh source root and authentic USA ROM")
    installed = launcher.parent / ROM
    if installed.exists() or installed.is_symlink():
        raise ValueError("ROM-free original candidate still holds installed ROM")
    root.mkdir(parents=True)
    try:
        shutil.copyfile(rom, installed)
        if digest(installed.read_bytes()) != USA_SHA256:
            raise ValueError("Temporary original USA ROM differs")
        choices = ("R",) if noncanonical_r_only else ("R", "T")
        result = {choice: run_case(
            launcher, fixture, seed, root / choice, choice, timeout,
            noncanonical_typed=noncanonical_r_only)
                  for choice in choices}
        (root / "interactive-rt-result.json").write_text(
            json.dumps({
                "schema": ("ur-win32-interactive-noncanonical-raw-r/1"
                           if noncanonical_r_only else
                           "ur-win32-interactive-original-cmd-rt/1"),
                "tested_choices": list(choices),
                "results": result,
                "physical_operator": False,
                "release_gate_credit": 0,
            }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
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
    ap.add_argument("--timeout", type=int, default=100)
    ap.add_argument("--noncanonical-r-only", action="store_true")
    a = ap.parse_args()
    print(json.dumps(run_with_rom(
        a.launcher.resolve(), a.rom.resolve(), a.fixture.resolve(),
        a.seed.resolve(), a.out.resolve(), a.timeout,
        noncanonical_r_only=a.noncanonical_r_only), sort_keys=True))


if __name__ == "__main__":
    main()
