#!/usr/bin/env python3
"""Run the *existing* pinned Baldosa 2P route in isolated native Windows dirs.

No substitute guest driver or new input grammar: this launches the actual
UniracersSNESRecomp executable with Baldosa's original --script/--framedump
arguments. Two clean processes differ only by the opt-in 24-event-pump host
pause/resume witness. Neither touches the user's profile/save root.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import zipfile

USA_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
CRC = re.compile(r'"crc32_wram":\s*"(0x[0-9a-fA-F]+)"')
PAUSE = re.compile(r"UR_BALDOSA_NATIVE_PAUSE (ARMED|RELEASED|RESUMED) ([^\r\n]*)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def frame_crcs(folder: Path) -> list[str]:
    frames = folder.glob("frame_*.json")
    def sort_key(path: Path) -> int:
        match = re.fullmatch(r"frame_(\d+)\.json", path.name)
        if match is None:
            raise ValueError(f"Unexpected framedump path: {path}")
        return int(match.group(1))
    files = sorted(frames, key=sort_key)
    if not files:
        raise ValueError(f"No real guest framedumps produced in {folder}")
    parsed = []
    for path in files:
        match = CRC.search(path.read_text(encoding="utf-8"))
        if not match:
            raise ValueError(f"Missing real WRAM CRC in {path}")
        parsed.append(match.group(1).lower())
    return parsed


def run_route(exe: Path, rom: Path, script: Path, root: Path,
              *, pause: bool, video: str, timeout: int,
              delayed_restart: bool = False,
              profile_fixture: Path | None = None,
              profile_seed: Path | None = None) -> tuple[list[str], str]:
    if delayed_restart and not pause:
        raise ValueError("Delayed native Restart requires an acknowledged host pause")
    if (profile_fixture is None) != (profile_seed is None):
        raise ValueError("Real native Modern profile needs a typed fixture and seed SRAM")
    if profile_fixture and pause:
        raise ValueError("Use the unpaused guest for initial named-profile SRAM witness")
    name = ("with_named_profile" if profile_fixture else
            ("with_delayed_restart" if delayed_restart else
             ("with_pause" if pause else "baseline")))
    output = root / name
    # Never remove an earlier result (or a directory outside our owned root).
    output.mkdir(parents=True, exist_ok=False)
    (output / "saves").mkdir()  # old cwd root must remain empty
    (output / "dump").mkdir()
    user_root = output / "Modern Player Data With Spaces"
    user_root.mkdir()
    if profile_fixture:
        # Build an AUTHENTIC Modern state, profile and roster with existing
        # shipping C++ serializers, never a shadow Python file format.
        subprocess.run(
            [str(profile_fixture), str(user_root), str(profile_seed)],
            cwd=output, timeout=timeout, capture_output=True,
            text=True, check=True)
    framedump = output / "fd"
    framedump.mkdir()
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    env = os.environ.copy()
    env.update({
        # Same explicit mutable root selected by our existing Windows
        # run-uniracers.cmd; no second profile/save directory is invented.
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1" if profile_fixture else "0",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1" if profile_fixture else "0",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
        "SNESRECOMP_DUMP_DIR": str(output / "dump"),
        "UR_BALDOSA_PAUSE_SMOKE": "1" if pause else "0",
        "UR_BALDOSA_MODERN_INPUT": "1" if pause else "0",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1" if pause else "0",
        "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "1" if pause else "0",
        "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "1" if pause else "0",
        "UR_BALDOSA_DELAYED_RESTART_SMOKE": "1" if delayed_restart else "0",
        "UR_BALDOSA_RESTART_FRAME_TRACE": "1" if (not pause or delayed_restart) else "0",
        "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "1952",
        "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1",
    })
    cmd = [str(exe), "--no-launcher", "--config", str(config),
           "--script", str(script), "--framedump", str(framedump), str(rom)]
    try:
        outcome = subprocess.run(cmd, cwd=output, env=env, timeout=timeout,
                                 capture_output=True, text=True, errors="replace")
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{name}: native guest process timed out after {timeout}s") from exc
    log = outcome.stdout + "\n" + outcome.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if outcome.returncode != 0:
        raise RuntimeError(f"{name}: native guest returned {outcome.returncode}; "
                           f"log tail:\n{log[-5000:]}")
    if not (user_root / "keybinds.ini").is_file():
        raise RuntimeError(f"{name}: game wrote no native keybinds into Modern user root")
    if profile_fixture:
        verify_named_profile_boot(log, profile_seed)
        verify_native_profile_checkpoint(
            profile_fixture, user_root, "native-ci-rider", log, timeout)
        if (user_root / "saves/save.srm").exists():
            raise RuntimeError(f"{name}: named guest wrote unrelated default-profile SRAM")
        if not (user_root / "saves/profile-native-ci-rider/save.srm").is_file():
            raise RuntimeError(f"{name}: named guest did not preserve selected-profile SRAM")
    elif not (user_root / "saves/save.srm").is_file():
        raise RuntimeError(f"{name}: real guest SRAM not saved under Modern user root")
    if any((output / "saves").iterdir()):
        raise RuntimeError(f"{name}: guest created package/cwd-local saves")
    return frame_crcs(framedump), log



def verify_native_profile_checkpoint(
    fixture: Path, root: Path, profile_id: str, log: str, timeout: int,
) -> None:
    """Native shutdown first, original Modern typed store read-back second."""
    line = (
        f"UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile={profile_id} "
    )
    matches = re.findall(
        rf"(?m)^{re.escape(line)}status=(committed|unchanged)$", log)
    if len(matches) != 1:
        raise ValueError("No unique acknowledged native post-save profile publication")
    process = subprocess.run(
        [str(fixture), str(root), profile_id, "--verify-native-save"],
        capture_output=True, text=True, timeout=timeout,
    )
    if process.returncode != 0 or (
        f"UR_BALDOSA_NATIVE_PROFILE VERIFIED profile={profile_id} sram=8192 "
        not in process.stdout
    ):
        raise ValueError(
            "Native disk SRAM and existing Modern typed profile store diverged: "
            f"{process.returncode} {process.stdout} {process.stderr}")


PROFILE_BOOT_SRAM = re.compile(
    r"^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
    r"profile=native-ci-rider bytes=8192 fnv=([0-9a-fA-F]{8})$",
    re.MULTILINE,
)


def fnv32(data: bytes) -> str:
    h = 2166136261
    for b in data:
        h = ((h ^ b) * 16777619) & 0xffffffff
    return f"{h:08x}"


def verify_named_profile_boot_bytes(
    log: str, raw: bytes, profile_id: str = "native-ci-rider",
) -> dict[str, str]:
    # The title's stock before_run_frame callback fires AFTER RtlReadSram
    # but before the first actual RtlRunFrame. Compare the entire 8192 bytes
    # using an independent hash of the real previous native guest's SRAM.
    if profile_id not in ("native-ci-rider", "native-ci-second", "mike"):
        raise ValueError("Unknown named native QA profile")
    pattern = re.compile(
        rf"^UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM "
        rf"profile={re.escape(profile_id)} bytes=8192 fnv=([0-9a-fA-F]{{8}})$",
        re.MULTILINE)
    proof = pattern.findall(log)
    if len(proof) != 1:
        raise ValueError("No unique first-frame named Modern guest SRAM witness")
    expected_root = (
        f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={profile_id} "
        f"root=saves/profile-{profile_id}\n")
    if expected_root not in log:
        raise ValueError("Native guest did not activate the expected isolated profile root")
    if len(raw) != 8192 or proof[0].lower() != fnv32(raw):
        raise ValueError("Native guest did not load exactly the selected profile's SRAM")
    return {"bytes": len(raw), "fnv32": proof[0].lower()}



def verify_named_profile_boot(log: str, seed: Path) -> dict[str, str]:
    return verify_named_profile_boot_bytes(log, seed.read_bytes())


def run_existing_named_profile_fresh_process(
    exe: Path, rom: Path, script: Path, root: Path, *,
    video: str, timeout: int, clean_frames: int, fixture: Path,
) -> dict[str, str | int]:
    """Boot the same previously-played Modern profile in a SECOND native process.

    No fixture rerun, no reseeding, no duplicate state or copy to a new root.
    Original guest SRAM writes after the first process are the second
    process's only save authority. A fresh boot must read exactly those bytes
    and not create a default/anonymous save.
    """
    previous = root / "with_named_profile"
    user_root = previous / "Modern Player Data With Spaces"
    sram = user_root / "saves/profile-native-ci-rider/save.srm"
    state = user_root / "saves/profile-native-ci-rider/host-profile.txt"
    product = user_root / "host-state-v1.txt"
    catalog = user_root / "profiles-v1.txt"
    # Snapshot durable material before new process can modify it. In
    # particular, comparing against sram.read_bytes() *after* the run would
    # hide accidental writes before the boot-check callback.
    saved = sram.read_bytes()
    if len(saved) != 8192:
        raise ValueError("Durable named-profile SRAM is not a complete 8-KiB image")
    metadata_before = [p.read_bytes() for p in (state, product, catalog)]
    output = root / "named_profile_fresh_relaunch"
    output.mkdir(parents=True, exist_ok=False)
    framedump = output / "fd"
    framedump.mkdir()
    (output / "dump").mkdir()
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
        "SNESRECOMP_DUMP_DIR": str(output / "dump"),
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        # No synthetic host Restart or seeded first-run environment.
        "UR_BALDOSA_PAUSE_SMOKE": "0",
        "UR_BALDOSA_MODERN_INPUT": "0",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "0",
        "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
        "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
        "UR_BALDOSA_RESTART_FRAME_TRACE": "0",
    })
    outcome = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), "--framedump", str(framedump),
         str(rom)],
        cwd=output, env=env, timeout=timeout, capture_output=True,
        text=True, errors="replace",
    )
    log = outcome.stdout + "\n" + outcome.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if outcome.returncode:
        raise RuntimeError(
            f"Fresh native Modern profile process failed {outcome.returncode}: "
            f"{log[-3000:]}")
    proof = verify_named_profile_boot_bytes(log, saved)
    frames = check_named_profile_guest_terminal(
        frame_crcs(framedump), log, clean_frames=clean_frames)
    verify_native_profile_checkpoint(
        fixture, user_root, "native-ci-rider", log, timeout)
    # Profile metadata may now advance by exactly the authentic typed SRAM
    # checkpoint; the global selector and catalog remain unchanged.
    for path, original in zip((product, catalog), metadata_before[1:]):
        if path.read_bytes() != original:
            raise ValueError(
                f"Native guest unexpectedly changed host-owned Modern state: {path.name}")
    if (user_root / "saves/save.srm").exists():
        raise ValueError("Fresh named Modern process created anonymous save")
    if len(sram.read_bytes()) != 8192:
        raise ValueError("Fresh native process damaged selected named profile SRAM")
    return {"loaded_8192_byte_save_from_previous_process": True,
            "initial_native_sram_fnv32": proof["fnv32"],
            "second_process_guest_frames": frames}



def run_second_named_profile_isolation(
    exe: Path, rom: Path, root: Path, fixture: Path, seed: Path,
    *, video: str, timeout: int,
) -> dict[str, str | int]:
    """Switch to another real typed Modern profile and boot the SAME AOT.

    One player must not inherit the other's SRAM just because the title
    keeps one global ROM, original game menu, and compiled native executable.
    This exercises the exact system-root + active-selector authority; no
    parallel UI or alternate profile serialization is introduced.
    """
    user_root = root / "with_named_profile/Modern Player Data With Spaces"
    first_root = user_root / "saves/profile-native-ci-rider"
    first_sram = first_root / "save.srm"
    first_metadata = first_root / "host-profile.txt"
    prior_sram = first_sram.read_bytes()
    prior_metadata = first_metadata.read_bytes()
    if len(prior_sram) != 8192:
        raise ValueError("First named profile has invalid durable SRAM length")
    output = root / "different_named_profile"
    output.mkdir(parents=True, exist_ok=False)
    fixture_process = subprocess.run(
        [str(fixture), str(user_root), str(seed), "--add-second"],
        cwd=output, timeout=timeout, capture_output=True, text=True,
        errors="replace")
    if fixture_process.returncode:
        raise RuntimeError(
            f"Existing typed Modern second-profile fixture rejected: "
            f"{fixture_process.returncode} {fixture_process.stderr[-2000:]}")
    second_root = user_root / "saves/profile-native-ci-second"
    second_sram = second_root / "save.srm"
    source = second_sram.read_bytes()
    if len(source) != 8192 or source == prior_sram:
        raise ValueError("Second named Modern profile lacks independent SRAM")
    script = output / "bounded_second_profile.txt"
    script.write_text("turbo on\nwait 4\nquit\n", encoding="ascii")
    framedump = output / "fd"
    framedump.mkdir()
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
        "SNESRECOMP_DUMP_DIR": str(output),
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_PAUSE_SMOKE": "0",
        "UR_BALDOSA_MODERN_INPUT": "0",
    })
    outcome = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), "--framedump", str(framedump),
         str(rom)],
        cwd=output, env=env, timeout=timeout, capture_output=True,
        text=True, errors="replace")
    log = outcome.stdout + "\n" + outcome.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if outcome.returncode:
        raise RuntimeError(
            f"Second named real native guest rejected: "
            f"{outcome.returncode} {log[-3000:]}")
    proof = verify_named_profile_boot_bytes(
        log, source, profile_id="native-ci-second")
    verify_native_profile_checkpoint(
        fixture, user_root, "native-ci-second", log, timeout)
    frames = frame_crcs(framedump)
    if not frames or not re.search(r"^script f=\d+ quit$", log, re.M):
        raise ValueError("Second named profile never executed real guest frames")
    if first_sram.read_bytes() != prior_sram or (
        first_metadata.read_bytes() != prior_metadata
    ):
        raise ValueError("Second native guest changed first Modern profile")
    if (user_root / "saves/save.srm").exists():
        raise ValueError("Second profile leaked into anonymous default save")
    if len(second_sram.read_bytes()) != 8192:
        raise ValueError("Second native guest corrupted its own SRAM length")
    return {
        "second_profile_loaded_exact_8192_bytes": True,
        "second_profile_boot_fnv32": proof["fnv32"],
        "first_profile_unchanged": True,
        "guest_frames": len(frames),
    }


def assert_corrupt_named_profile_rejected(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
) -> None:
    output = root / "corrupt_named_profile"
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Modern Player Data With Spaces"
    user_root.mkdir()
    subprocess.run([str(fixture), str(user_root), str(seed)],
                   cwd=output, capture_output=True, text=True,
                   timeout=timeout, check=True)
    profile_dir = user_root / "saves/profile-native-ci-rider"
    saved_before = (profile_dir / "save.srm").read_bytes()
    # A corrupt Modern profile must NEVER silently fall back to the stock
    # generic save, even though a valid active profile ID was requested.
    (profile_dir / "host-profile.txt").write_text(
        "malformed selected profile; keep all SRAM untouched",
        encoding="utf-8")
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    outcome = subprocess.run([
        str(exe), "--no-launcher", "--config", str(config),
        "--script", str(script), str(rom),
    ], cwd=output, env=env, capture_output=True, text=True,
       timeout=timeout, errors="replace")
    log = outcome.stdout + "\n" + outcome.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if (outcome.returncode != 7 or
        "UR_BALDOSA_NATIVE_PROFILE REJECTED reason="
        "selected_profile_state_missing_or_invalid" not in log):
        raise ValueError(
            "Corrupt selected Modern profile did not reject real guest boot")
    if (profile_dir / "save.srm").read_bytes() != saved_before or (
        user_root / "saves/save.srm").exists():
        raise ValueError("Rejected named profile unexpectedly mutated SRAM")



def check_named_profile_guest_terminal(
    framedump_crcs: list[str], log: str, *, clean_frames: int
) -> int:
    """Real saved SRAM can shift the menu until-loop by one guest frame.

    This is not a tolerance for a missing scripted checkpoint. The native
    route must explicitly report a valid t480 dump and quit at the last
    actually rendered native guest frame, with no more than one prior-boot
    frame difference from the otherwise untouched clean-SRAM baseline.
    """
    named_frames = len(framedump_crcs)
    if named_frames not in (clean_frames - 1, clean_frames):
        raise ValueError(
            f"Named-profile guest frame count outside independently observed "
            f"one-frame saved-SRAM window: {named_frames} vs {clean_frames}")
    for event in ("dump t480 ok", "quit"):
        if not re.search(
            rf"^script f={named_frames} {re.escape(event)}$",
            log, re.MULTILINE,
        ):
            raise ValueError(
                f"Named-profile guest did not reach real terminal checkpoint: {event}")
    return named_frames

def check_pause_log(log: str) -> dict[str, str]:
    found = {kind: rest for kind, rest in PAUSE.findall(log)}
    if set(found) != {"ARMED", "RELEASED", "RESUMED"}:
        raise ValueError(f"Missing native pause lifecycle proof: {found}")
    if "live_race=1" not in found["ARMED"]:
        raise ValueError("Native pause was not triggered in authoritative live gameplay")
    if "physical_sdl=1" not in found["ARMED"] or "physical_sdl=1" not in found["RELEASED"]:
        raise ValueError("Native pause did not traverse two physical SDL key edges")
    if "modern_session=1" not in found["ARMED"]:
        raise ValueError("Native pause did not use the acknowledged Modern session API")
    if not re.search(
        r"UR_BALDOSA_NATIVE_RESTART SAME_FRAME guest=\d+ sram_equal=1 wram_equal=1(?:\r?\n|$)", log):
        raise ValueError("Native guest rollback did not preserve WRAM and SRAM at its anchor")
    if "frozen_pumps=24" not in found["RELEASED"] or "frozen_pumps=24" not in found["RESUMED"]:
        raise ValueError(f"Guest hold too short: {found}")
    freeze = re.findall(
        r"UR_BALDOSA_NATIVE_PAUSE FROZEN_PRESENT guest=(\d+) "
        r"present_count=(\d+) no_guest_steps=1", log)
    if len(freeze) != 1 or int(freeze[0][1]) < 23:
        raise ValueError("Native paused raster was not presented across frozen pumps")
    panel = re.findall(
        r"UR_BALDOSA_NATIVE_PAUSE PANEL_RENDERED=1 pixels=(\d+)x(\d+) "
        r"renderer=shared guest_steps=0", log)
    if len(panel) != 1 or int(panel[0][0]) < 320 or int(panel[0][1]) < 320:
        raise ValueError("Native pause shared panel did not visibly paint the frozen raster")
    if log.count(
        "UR_BALDOSA_NATIVE_PAUSE_MENU NAV=1 down_up=1 "
        "selected=0 guest_steps=0") != 1:
        raise ValueError("Native Modern menu did not navigate on physical SDL keys")
    if "FAIL=" in log:
        raise ValueError("Native pause code detected a guest-state violation")
    return found


DELAYED_RESTART = re.compile(
    r"^UR_BALDOSA_NATIVE_RESTART DELAYED anchor_guest=(\d+) "
    r"request_guest=(\d+) paused=1 sram_equal=1 wram_rewound=1$",
    re.MULTILINE,
)


def check_delayed_restart_log(log: str, *, expected_request_frame: int) -> dict[str, int]:
    # One real SDL-keyboard Restart after actual guest progression, while
    # paused. Do not confuse this with the already-accepted same-frame roundtrip.
    matches = DELAYED_RESTART.findall(log)
    if len(matches) != 1:
        raise ValueError("Missing unique live delayed native Restart witness")
    anchor, request = (int(v) for v in matches[0])
    if anchor < 1 or anchor + 12 >= request or request != expected_request_frame:
        raise ValueError("Delayed native Restart lacked actual guest progression")
    if "UR_BALDOSA_NATIVE_PAUSE FAIL=" in log:
        raise ValueError("Native delayed Restart detected an execution violation")
    check_pause_log(log)
    return {"anchor_guest": anchor, "request_guest": request}


HOST_FRAME_CRC = re.compile(
    r"^UR_BALDOSA_HOST_FRAME_CRC host=(\d+) guest=(\d+) hash=([0-9a-fA-F]{8})$",
    re.MULTILINE,
)
HOST_TRACE_START = 1948
HOST_TRACE_END = 1970
HOST_RESTART_FRAME = 1952


def parse_host_wram_trace(log: str) -> dict[int, tuple[int, str]]:
    """Append-only real simulation-frame evidence, independent of guest dump filenames.

    Baldosa's original framedumper names files by snes_frame_counter. A native
    rollback may rebase that counter and overwrite earlier identical guest
    frames. The WRAM CRC in such files is valid for its *guest* frame, but
    cannot prove or disprove a *host*-relative Restart. The title callback
    records monotonic SnesDesktopHostFrameStats.frame here instead.
    """
    found = {}
    for host, guest, digest in HOST_FRAME_CRC.findall(log):
        host_frame = int(host)
        if host_frame in found:
            raise ValueError(f"Duplicate host-frame WRAM trace {host_frame}")
        found[host_frame] = int(guest), digest.lower()
    needed = set(range(HOST_TRACE_START, HOST_TRACE_END + 1))
    if set(found) != needed:
        raise ValueError(f"Missing/out-of-window actual host-frame WRAM samples: "
                         f"missing={sorted(needed - set(found))} "
                         f"extra={sorted(set(found) - needed)}")
    return found


def check_delayed_restart_host_trace(
    baseline_log: str, delayed_log: str
) -> dict[str, int]:
    baseline = parse_host_wram_trace(baseline_log)
    delayed = parse_host_wram_trace(delayed_log)
    for frame in range(HOST_TRACE_START, HOST_RESTART_FRAME + 1):
        if baseline[frame] != delayed[frame]:
            raise ValueError(
                f"Native Restart changed guest state before physical R at host {frame}")
    first = next(
        (frame for frame in range(HOST_RESTART_FRAME + 1, HOST_TRACE_END + 1)
         if baseline[frame][1] != delayed[frame][1]), None)
    if first is None:
        raise ValueError(
            "Native Restart did not change any actual post-resume host-frame WRAM")
    # A restored guest-frame counter corroborates the causal rewind, but
    # only the full guest WRAM witness is mandatory. Never use filename
    # positions to infer whether a guest actually advanced after Restart.
    return {
        "first_divergent_host_frame": first,
        "original_guest_counter_after_resume": baseline[first][0],
        "restarted_guest_counter_after_resume": delayed[first][0],
        "host_sample_count": len(baseline),
    }


def assert_invalid_mutable_root_fails_closed(
    exe: Path, rom: Path, script: Path, root: Path, *,
    video: str, timeout: int,
) -> None:
    output = root / "invalid_native_root"
    output.mkdir(parents=True, exist_ok=False)
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": "relative-root-MUST-FAIL",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    outcome = subprocess.run([
        str(exe), "--no-launcher", "--config", str(config),
        "--script", str(script), str(rom),
    ], cwd=output, env=env, timeout=timeout,
       capture_output=True, text=True, errors="replace")
    log = outcome.stdout + "\n" + outcome.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if outcome.returncode == 0 or "UR-STARTUP-SAVE-ROOT:" not in log:
        raise ValueError(
            "Native Baldosa incorrectly fell back to local saves for an "
            "invalid explicitly selected Modern data root")
    if (output / "relative-root-MUST-FAIL").exists() or (output / "saves").exists():
        raise ValueError("Rejected native user root mutated package/cwd state")


def verify_native_modern_root_log(log: str, players: int = 1) -> None:
    """Real shared root to acknowledged stock 1P/2P menu, not a guest guess."""
    if players not in (1, 2):
        raise ValueError("Unsupported native stock player count")
    stages = [
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared",
    ]
    if players == 1:
        stages.extend([
            "UR_BALDOSA_MODERN_ROOT selected=3",
            "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=none validated=0 unavailable=0",
            "UR_BALDOSA_MODERN_ROOT records_closed=1",
            "UR_BALDOSA_MODERN_ROOT selected=0",
        ])
    else:
        stages.append("UR_BALDOSA_MODERN_ROOT selected=2")
    stages.extend([
        f"UR_BALDOSA_MODERN_ROOT stock_requested players={players}",
        "UR_BALDOSA_MODERN_ROOT stock_entered "
        f"players={players} menu={0x3c if players == 1 else 0x3d:02x}",
    ])
    positions = []
    for marker in stages:
        if log.count(marker) != 1:
            raise ValueError(f"Native Modern stock route missing/duplicate: {marker}")
        positions.append(log.index(marker))
    if positions != sorted(positions):
        raise ValueError("Native Modern root SDL/stock journey out of order")
    if "UR_BALDOSA_MODERN_ROOT stock_rejected=" in log:
        raise ValueError("Native Modern stock route aborted")


def verify_native_named_records_root_log(log: str) -> None:
    """Read-only REAL Windows Records on the selected named profile."""
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider",
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_ROOT painted=1 destinations=5 renderer=shared",
        "UR_BALDOSA_MODERN_ROOT selected=3",
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=selected validated=1 unavailable=1",
        "UR_BALDOSA_MODERN_ROOT records_closed=1",
        "UR_BALDOSA_MODERN_ROOT selected=0",
        "UR_BALDOSA_MODERN_ROOT stock_requested players=1",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
    )
    positions = []
    for token in stages:
        if log.count(token) != 1:
            raise ValueError(f"Native named Records marker missing/duplicate: {token}")
        positions.append(log.index(token))
    if positions != sorted(positions):
        raise ValueError("Native named Records lifecycle out of order")
    if ("UR_BALDOSA_MODERN_ROOT route=3 unavailable=1" in log or
        "UR_BALDOSA_MODERN_ROOT records_opened=1 profile=none" in log or
        "UR_BALDOSA_MODERN_ROOT stock_rejected=" in log or
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT rejected" in log):
        raise ValueError("Native named Records used an unverified route")


def verify_native_records_page_handoff(log: str) -> None:
    """Use genuine native SDL page navigation, not a separate QA records UI."""
    initial = "UR_BALDOSA_MODERN_ROOT records_page=1p"
    opened = "UR_BALDOSA_MODERN_ROOT records_opened=1"
    two = "UR_BALDOSA_MODERN_ROOT records_page=2p"
    closed = "UR_BALDOSA_MODERN_ROOT records_closed=1"
    # The initial 1P selection is emitted before the opened diagnostic.
    # The second 1P selection must follow the physical Down-to-2P edge.
    # Check suffix tokens as well as complete markers: truncated/duplicate
    # diagnostic lines must not evade the strictly ordered route contract.
    if (log.count("records_page=1p") != 2 or
            log.count("records_page=2p") != 1 or
            log.count("records_opened=1") != 1 or
            log.count("records_closed=1") != 1):
        raise ValueError("Native Records 1P/2P pages duplicated or missing")
    positions = (
        log.find(initial), log.find(opened), log.find(two),
        log.find(initial, log.find(two) + len(two)), log.find(closed),
    )
    if -1 in positions or list(positions) != sorted(positions):
        raise ValueError(
            "Native Records 1P/2P SDL page handoff missing or out of order")


def run_native_named_records_root(
    exe: Path, rom: Path, root: Path, fixture: Path, seed: Path,
    *, video: str, timeout: int,
) -> dict[str, object]:
    """Real named Modern profile opens canonical archives then enters stock 1P.

    A separate test-only fixture writes valid/malformed historical artifacts
    via the SHIPPING .urrun codec. Never pretend those were guest-completed.
    """
    output = root / "native_named_readonly_records"
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Existing Named Racer With Spaces"
    user_root.mkdir()
    subprocess.run(
        [str(fixture), str(user_root), str(seed)], cwd=output,
        capture_output=True, text=True, timeout=timeout, check=True,
    )
    created = subprocess.run(
        [str(fixture), str(user_root), "native-ci-rider",
         "--seed-readonly-records"], cwd=output,
        capture_output=True, text=True, timeout=timeout, check=True,
    )
    if "valid=1 unavailable=1 scope=read_only" not in created.stdout:
        raise ValueError("Historical archive fixture did not use canonical writer")
    archive = user_root / "runs" / "native-ci-rider"
    original = {path.name: path.read_bytes() for path in archive.iterdir()}
    if set(original) != {"0001.urrun", "0002.urrun"}:
        raise ValueError("Unexpected seeded Records fixture namespace")
    paired_seed = subprocess.run(
        [str(fixture), str(user_root), "native-ci-rider",
         "--seed-readonly-2p"], cwd=output,
        capture_output=True, text=True, timeout=timeout, check=True,
    )
    if ("paired=1 unavailable=1 "
            "scope=read_only_historical_not_played") not in paired_seed.stdout:
        raise ValueError("Historical 2P fixture did not use canonical paired codecs")
    match_archive = user_root / "multiplayer-runs"
    original_pairs = {path.name: path.read_bytes()
                      for path in match_archive.iterdir()}
    if set(original_pairs) != {
            "0001-match.urrun", "0001-match.urrun.urmatch",
            "0002-incomplete.urrun"}:
        raise ValueError("Unexpected historical 2P fixture artifact set")
    script = output / "root_records.txt"
    script.write_text("turbo on\nwait 1800\nquit\n", encoding="ascii")
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    process = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=output, env=env, capture_output=True, text=True,
        timeout=timeout, errors="replace",
    )
    log = process.stdout + "\n" + process.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(
            f"Named Records Windows guest rc={process.returncode}: {log[-2500:]}")
    verify_native_named_records_root_log(log)
    verify_native_records_page_handoff(log)
    # The actual native Windows Records presenter must consume the
    # original shipping match codecs, not merely display pre-seeded counts.
    # This historical fixture is explicitly NOT an actual played race.
    if log.count(
        "UR_BALDOSA_MODERN_ROOT records_last_2p="
        "LAST 01 WIN 00:28.66 source=historical_paired_archive"
    ) != 1:
        raise ValueError(
            "Native Windows 2P Records did not expose its validated "
            "source-paired latest-match result")
    if log.count(
        "UR_BALDOSA_MODERN_ROOT matches_readonly=1 paired=1 "
        "unavailable=1 selected=1"
    ) != 1:
        raise ValueError("Native named profile did not load the bound historical 2P pair")
    verify_named_profile_boot_bytes(log, seed.read_bytes())
    verify_native_profile_checkpoint(
        fixture, user_root, "native-ci-rider", log, timeout)
    observed = {path.name: path.read_bytes() for path in archive.iterdir()}
    if observed != original:
        raise ValueError("Opening native Records minted/altered an .urrun artifact")
    observed_pairs = {path.name: path.read_bytes()
                      for path in match_archive.iterdir()}
    if observed_pairs != original_pairs:
        raise ValueError("Native 2P Records modified or minted a match artifact")
    if (user_root / "saves/save.srm").exists() or (output / "saves").exists():
        raise ValueError("Native named Records leaked into the default save root")

    # Reuse this exact extracted native binary, named profile and original
    # SDL root smoke in a SECOND process. With only one registered profile,
    # Multiplayer must remain playable but its unbound 2P route may never
    # manufacture a pair or assign an opponent from a controller seat.
    unbound_env = {**env, "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "2"}
    unbound = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=output, env=unbound_env, capture_output=True, text=True,
        timeout=timeout, errors="replace")
    unbound_log = unbound.stdout + "\n" + unbound.stderr
    (output / "named-single-profile-stock-2p.log").write_text(
        unbound_log, encoding="utf-8")
    if unbound.returncode:
        raise RuntimeError(
            "Named single-profile stock 2P rejected: " +
            unbound_log[-2400:])
    verify_native_modern_root_log(unbound_log, players=2)
    if unbound_log.count(
            "UR_BALDOSA_MODERN_ROOT join_unavailable=1 "
            "stock_2p_without_record_identity=1") != 1:
        raise ValueError("Named single-profile 2P fabricated or bypassed join authority")
    if (unbound_log.count(
            "UR_BALDOSA_MODERN_ROOT unbound_2p_warning_open=1") != 1 or
            unbound_log.count(
                "UR_BALDOSA_MODERN_ROOT unbound_2p_consented=1") != 1 or
            "UR_BALDOSA_MODERN_ROOT unbound_2p_declined=1" in unbound_log):
        raise ValueError("Unrecorded stock 2P bypassed explicit P1 consent")
    if ("UR_BALDOSA_NATIVE_MATCH CAPTURED=1" in unbound_log or
            {p.name: p.read_bytes() for p in match_archive.iterdir()} !=
            original_pairs):
        raise ValueError("Unbound stock 2P changed canonical pair history")
    # A third invocation uses the fixture's canonical transaction to
    # register/initialize P2 and switch the selected SRAM to that racer.
    # This is still test-synthetic host gamepad input, NEVER a physical-pad
    # or played ordinary-2P result certification.
    created_second = subprocess.run(
        [str(fixture), str(user_root), str(seed), "--add-second"],
        cwd=output, capture_output=True, text=True, timeout=timeout,
        check=True)
    if "switched=native-ci-second" not in created_second.stdout:
        raise ValueError("Canonical named P2 fixture did not activate")
    joined_env = {**env, "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "3"}
    joined = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=output, env=joined_env, capture_output=True, text=True,
        timeout=timeout, errors="replace")
    joined_log = joined.stdout + "\n" + joined.stderr
    (output / "named-two-profile-stock-2p.log").write_text(
        joined_log, encoding="utf-8")
    if joined.returncode:
        raise RuntimeError(
            "Named two-seat stock 2P rejected: " + joined_log[-2600:])
    verify_native_modern_root_log(joined_log, players=2)
    stages = (
        "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-second",
        "UR_BALDOSA_MODERN_ROOT join_opened=1 players=2",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=1",
        "UR_BALDOSA_MODERN_ROOT synthetic_join_edge seat=1",
        "UR_BALDOSA_MODERN_ROOT join_confirmed seat=2",
        "UR_BALDOSA_MODERN_ROOT stock_requested players=2",
        "UR_BALDOSA_MODERN_ROOT synthetic_join_edge seat=2",
        "UR_BALDOSA_MODERN_ROOT stock_entered players=2 menu=3d",
    )
    positions = [joined_log.find(marker) for marker in stages]
    if (-1 in positions or positions != sorted(positions) or
            any(joined_log.count(marker) != 1 for marker in stages)):
        raise ValueError("Named native P1/P2 consent did not precede real stock 2P")
    if ("UR_BALDOSA_NATIVE_MATCH CAPTURED=1" in joined_log or
            {p.name: p.read_bytes() for p in match_archive.iterdir()} !=
            original_pairs):
        raise ValueError("Synthetic 2P join wrongly minted a real-match artifact")
    verify_native_profile_checkpoint(
        fixture, user_root, "native-ci-second", joined_log, timeout)
    return {
        "selected_named_profile_sram_authorized": True,
        "canonical_valid_archives_read_on_real_windows": 1,
        "canonical_2p_archive_readonly_tabs_checked": True,
        "historical_2p_pairs_read": 1,
        "incomplete_2p_pairs_reported_unavailable": 1,
        "2p_archive_unchanged_after_guest": True,
        "actual_native_2p_match_published": False,
        "named_one_profile_2p_stock_guest_playable": True,
        "unbound_2p_never_attributed_to_a_record": True,
        "two_named_profile_pad_semantic_confirmations": 2,
        "two_named_profile_original_stock_2p_entered": True,
        "synthetic_join_not_played_match_proof": True,
        "malformed_archives_reported_unavailable": 1,
        "no_run_created_by_record_view_or_script_quit": True,
        "existing_profile_checkpoint_verified": True,
        "real_stock_one_player_after_records": True,
        "backend_replay_compatibility_asserted": False,
    }


def run_native_modern_root_smoke(
    exe: Path, rom: Path, root: Path, *, video: str, timeout: int,
    players: int = 1,
) -> dict[str, bool]:
    """Windows host SDL root → original stock menu, exact source-observed 1P/2P.

    One guest executable, one input filter, the already authored Modern root.
    No forced WRAM states, fabricated race/result, or separate frontend owner.
    """
    if players not in (1, 2):
        raise ValueError("Unsupported native stock player count")
    output = root / f"native_modern_root_{players}p"
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Modern Root Player Data"
    user_root.mkdir()
    script = output / "root_window.txt"
    script.write_text("turbo on\nwait 1800\nquit\n", encoding="ascii")
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": str(players),
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    run = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=output, env=env, capture_output=True, text=True,
        timeout=timeout, errors="replace")
    log = run.stdout + "\n" + run.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(
            f"Native {players}P root Windows process rejected: "
            f"{run.returncode} {log[-3500:]}")
    verify_native_modern_root_log(log, players)
    saved = user_root / "saves/save.srm"
    if not saved.is_file() or len(saved.read_bytes()) != 8192:
        raise ValueError("Original guest did not save under the same Modern root")
    if (output / "saves").exists():
        raise ValueError("Root handoff wrote package/cwd-local guest saves")
    return {
        "shared_modern_root_visible": True,
        "real_sdl_root_navigation": True,
        "stock_guest_menu_observed": True,
        "native_guest_player_count": players,
        "no_guest_state_writes": True,
    }




# Probe each candidate in a fresh, independently booted original guest.
# Original Uniracers manual: A/B advance menus; X/Y backtrack.
# https://www.world-of-nintendo.com/manuals/super_nes/uniracers.shtml
# The real guest independently confirmed B advances 3c -> 6d.
STOCK_RETURN_CANDIDATES = ("x", "y")


def native_modern_root_reentry_script(button: str) -> str:
    """Bounded source guest back-input probe after a REAL Modern 1P handoff.

    The real SDL event pump may reopen the host root only if a candidate
    truly leads the original guest to its stock main 0xd7 surface. No fake
    WRAM menu bytes, emulator resets or indefinite script awaits.
    """
    if button not in STOCK_RETURN_CANDIDATES:
        raise ValueError("Unsupported source stock return candidate")
    return "\n".join([
        "turbo on",
        "until16 0053 == F60C",
        "wait 900",
        f"press {button} 2",
        "wait 360",
        "dump after_candidate",
        "quit",
        "",
    ])


def verify_native_modern_root_reentry_log(log: str) -> None:
    """Demand one *ordered*, genuine root exit, return and shared repaint."""
    verify_native_modern_root_log(log, 1)
    stages = [
        "UR_BALDOSA_MODERN_ROOT stock_entered players=1 menu=3c",
        "UR_BALDOSA_MODERN_ROOT reopened=1 menu=d7 guest_writes=0",
        "UR_BALDOSA_MODERN_ROOT reopened_painted=1 renderer=shared",
    ]
    pos = []
    for marker in stages:
        if log.count(marker) != 1:
            raise ValueError(f"Native Modern root reentry missing/duplicate {marker}")
        pos.append(log.index(marker))
    if pos != sorted(pos):
        raise ValueError("Native Modern root reentry transition out of order")


def run_native_modern_root_reentry(
    exe: Path, rom: Path, root: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    """Identify which real stock controller control returns to original MAIN.

    Every probe gets an isolated process, no shared state or guessed keyboard
    replay. A new Modern root is accepted only AFTER original 0xd7 observation.
    A lack of genuine exit fails CI and records the observed guest menu path.
    """
    probes: dict[str, str] = {}
    for button in STOCK_RETURN_CANDIDATES:
        output = root / f"native_modern_root_reentry_{button}"
        output.mkdir(parents=True, exist_ok=False)
        user_root = output / "Modern Returning Player Data"
        user_root.mkdir()
        script = output / "stock-menu-return.txt"
        script.write_text(native_modern_root_reentry_script(button),
                          encoding="ascii")
        config = output / "config.ini"
        config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
        env = os.environ.copy()
        env.update({
            "SNESRECOMP_USER_DATA_DIR": str(user_root),
            "UR_EXECUTION_MODE": "modern",
            "UR_BALDOSA_MODERN_ROOT": "1",
            "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "1",
            "UR_BALDOSA_MODERN_ROOT_REENTER_SMOKE": "1",
            "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
            "UR_BALDOSA_MODERN_INPUT": "1",
            "SDL_VIDEODRIVER": video,
            "SDL_AUDIODRIVER": "dummy",
        })
        try:
            result = subprocess.run(
                [str(exe), "--no-launcher", "--config", str(config),
                 "--script", str(script), str(rom)],
                cwd=output, env=env, capture_output=True, text=True,
                timeout=timeout, errors="replace")
        except subprocess.TimeoutExpired as exc:
            partial = (exc.stdout or b"")
            partial_err = (exc.stderr or b"")
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            if isinstance(partial_err, bytes):
                partial_err = partial_err.decode("utf-8", errors="replace")
            (output / "timeout-log.txt").write_text(
                partial + "\n" + partial_err, encoding="utf-8")
            raise RuntimeError(
                f"Bounded native root stock {button} probe timed out; "
                f"tail={(partial + partial_err)[-2000:]}") from exc
        log = result.stdout + "\n" + result.stderr
        (output / "log.txt").write_text(log, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(
                f"Native stock {button} probe returned {result.returncode}: "
                f"{log[-3000:]}")
        try:
            verify_native_modern_root_reentry_log(log)
        except ValueError:
            probes[button] = "; ".join(
                line for line in log.splitlines()
                if "UR_BALDOSA_MODERN_ROOT source_menu" in line)[-1600:]
            continue

        saved = user_root / "saves" / "save.srm"
        if not saved.is_file() or saved.stat().st_size != 8192:
            raise ValueError(f"Modern root reentry via {button} lost 8KiB SRAM")
        if (output / "saves").exists():
            raise ValueError("Modern root reentry leaked save to package/cwd")
        return {
            "stock_return_button_observed": button,
            "native_guest_main_menu_observed": True,
            "physical_sdl_escape_dispatched": True,
            "shared_root_reopened_and_painted": True,
            "gameplay_guest_writes": 0,
            "profile_sram_external": True,
        }

    raise ValueError(
        "No source-visible original menu return button confirmed; "
        f"real guest traces: {probes}")


def native_modern_race_entry_script(players: int) -> str:
    """One source-owned stock race route AFTER the host chose 1P or 2P.

    Presses only stock controls downstream of the established Modern root,
    with the same 200-frame menu settling intervals as the pinned original
    race_1p/race_2p scripts. The script may never select the main menu itself.
    The original guest's NMI handler and GO ticker are mandatory barriers.
    """
    if players == 1:
        steps = [
            "press start 2",  # racer
            "wait 200",
            "press start 2",  # tour
            "wait 200",
            "press start 2",  # track
            "wait 200",
            "press start 2",  # now playing
        ]
    elif players == 2:
        steps = [
            "press start 2",  # P1 racer
            "wait 200",
            "press p2:down 2",
            "wait 30",
            "press p2:start 2",  # P2 racer
            "wait 200",
            "press start 2",  # tour
            "wait 200",
            "press start 2",  # track
            "wait 200",
            "press start 2",  # now playing
        ]
    else:
        raise ValueError("Modern race entry must use one or two players")
    return "\n".join([
        "turbo on",
        "until16 0053 == F60C",
        "wait 900",  # root's real handoff must finish, not assumed at launch
        *steps,
        "until16 0053 == 8610",
        "until 0E1F != 00",
        "dump go",
        "quit",
        "",
    ])


def run_native_modern_race_entry(
    exe: Path, rom: Path, root: Path, *, players: int, video: str,
    timeout: int,
) -> dict[str, object]:
    """Execute Modern root → source stock picker → original GO in real Win32.

    The product integrates navigation only. Completion, results and course
    fidelity remain owned by the independent gameplay QA lane.
    """
    output = root / f"modern_to_live_race_{players}p"
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Modern Race Entry User Data With Spaces"
    user_root.mkdir()
    script = output / "original-stock-route.txt"
    script.write_text(native_modern_race_entry_script(players),
                      encoding="ascii")
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    framedump = output / "guest-frame-dumps"
    framedump.mkdir()
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": str(players),
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
    })
    try:
        run = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(script), "--framedump", str(framedump), str(rom)],
            cwd=output, env=env, capture_output=True, text=True,
            timeout=timeout, errors="replace")
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Modern {players}P root never reached source GO barrier") from exc
    log = run.stdout + "\n" + run.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(
            f"Modern {players}P root to original race failed "
            f"rc={run.returncode}: {log[-4500:]}")
    verify_native_modern_root_log(log, players)
    # A successful until16 NMI==8610 plus GO ticker is the original game's
    # own evidence that the launch reached a running guest race.
    crcs = frame_crcs(framedump)
    if len(crcs) < 900:
        raise ValueError("Modern stock journey produced too few real guest frames")
    saved = user_root / "saves" / "save.srm"
    if not saved.is_file() or saved.stat().st_size != 8192:
        raise ValueError("Modern guest race entry lost canonical SRAM root")
    if (output / "saves").exists():
        raise ValueError("Modern race journey leaked SRAM beside executable")
    return {
        "players": players,
        "native_root_handoff_observed": True,
        "original_race_nmi_barrier_passed": True,
        "original_go_ticker_barrier_passed": True,
        "actual_guest_frames": len(crcs),
        "profile_sram_isolated_from_executable": True,
        "complete_event_outcome_claimed": False,
    }


def verify_native_pause_quit_log(log: str) -> None:
    """Confirm a physical paused-menu Quit without inventing an event result."""
    stages = (
        "UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1 modern_session=1 physical_sdl=1",
        "UR_BALDOSA_NATIVE_PAUSE PANEL_RENDERED=1",
        "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1 paused=1 guest_steps=0",
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider status=",
    )
    positions = []
    for marker in stages:
        if log.count(marker) != 1:
            raise ValueError(f"Native paused Quit missing/duplicate {marker}")
        positions.append(log.index(marker))
    if positions != sorted(positions):
        raise ValueError("Native paused Quit stages out of order")
    if ("UR_BALDOSA_NATIVE_PAUSE FAIL=" in log or
        "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_REJECTED=" in log or
        "UR_BALDOSA_NATIVE_PAUSE RELEASED " in log or
        "UR_BALDOSA_NATIVE_PAUSE RESUMED " in log or
        re.search(r"^script f=\d+ quit$", log, re.MULTILINE)):
        raise ValueError("Native paused Quit was bypassed or guest resumed")
    if not re.search(
        r"^UR_BALDOSA_NATIVE_PROFILE CHECKPOINT "
        r"profile=native-ci-rider status=(committed|unchanged)$",
        log, re.MULTILINE,
    ):
        raise ValueError("Native paused Quit did not commit the typed Modern profile")


def verify_paused_quit_fresh_relaunch(
    exe: Path, rom: Path, root: Path, user_root: Path, fixture: Path,
    *, video: str, timeout: int,
) -> dict[str, object]:
    """Fresh native process must load the exact SRAM left by paused Quit.

    The same selected Modern root, catalog and typed state are reused.
    No reseed, profile switch, alternate save directory or synthetic event.
    """
    selected_save = user_root / "saves/profile-native-ci-rider/save.srm"
    saved = selected_save.read_bytes()
    if len(saved) != 8192:
        raise ValueError("Paused Quit did not leave a full selected SRAM image")
    selector = user_root / "host-state-v1.txt"
    catalog = user_root / "profiles-v1.txt"
    before = (selector.read_bytes(), catalog.read_bytes())
    output = root / "after_native_pause_quit_relaunch"
    output.mkdir(parents=True, exist_ok=False)
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    script = output / "bounded-relaunch.txt"
    script.write_text("turbo on\nwait 4\nquit\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "0",
        "UR_BALDOSA_MODERN_ROOT": "0",
        "UR_BALDOSA_PAUSE_SMOKE": "0",
        "UR_BALDOSA_PAUSE_QUIT_SMOKE": "0",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    try:
        process = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(script), str(rom)],
            cwd=output, env=env, capture_output=True, text=True,
            errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Fresh process did not reload paused-Quit SRAM") from exc
    log = process.stdout + "\n" + process.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(
            f"Fresh native process rejected paused-Quit profile "
            f"rc={process.returncode}: {log[-2300:]}"
        )
    proof = verify_named_profile_boot_bytes(log, saved)
    verify_native_profile_checkpoint(
        fixture, user_root, "native-ci-rider", log, timeout)
    if (selector.read_bytes(), catalog.read_bytes()) != before:
        raise ValueError("Fresh paused-Quit relaunch changed Modern selector/catalog")
    if (user_root / "saves/save.srm").exists() or (output / "saves").exists():
        raise ValueError("Fresh paused-Quit process leaked into another save root")
    if len(selected_save.read_bytes()) != 8192:
        raise ValueError("Fresh paused-Quit process damaged named profile SRAM")
    if list(user_root.rglob("*.urrun")):
        raise ValueError("Interrupted native race manufactured a finished run")
    return {
        "new_native_process_launched": True,
        "exact_previous_process_8192_byte_sram_loaded": True,
        "reloaded_fnv32": proof["fnv32"],
        "canonical_catalog_and_selector_unchanged": True,
        "no_default_profile_save": True,
        "no_fabricated_completed_run": True,
    }


def capture_native_selector_conflict_files(
    user_root: Path, snapshot_dir: Path, stage: str,
) -> dict[str, dict[str, object]]:
    """QA-only complete file bytes, not source guesses or fixture receipts.

    The second profile legitimately does not exist in the before-B snapshot.
    Preserve its ABSENCE as an explicit state instead of fabricating bytes.
    """
    names = {
        "selector": "host-state-v1.txt",
        "catalog": "profiles-v1.txt",
        "first_raw": "saves/profile-native-ci-rider/save.srm",
        "first_typed": "saves/profile-native-ci-rider/host-profile.txt",
        "second_raw": "saves/profile-native-ci-second/save.srm",
        "second_typed": "saves/profile-native-ci-second/host-profile.txt",
    }
    if stage not in ("before_A", "after_B_before_A", "after_A", "after_cold_B"):
        raise ValueError("Unrecognized owned profile-conflict stage")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, dict[str, object]] = {}
    for key, rel in names.items():
        path = user_root / rel
        if path.is_symlink():
            raise ValueError("Refusing redirected profile-conflict file")
        if not path.exists():
            if not key.startswith("second_") or stage != "before_A":
                raise ValueError(f"Missing expected named file at {stage}: {rel}")
            receipt[key] = {"present": False}
            continue
        if not path.is_file():
            raise ValueError(f"Unexpected profile-conflict file type: {rel}")
        raw = path.read_bytes()
        if key.endswith("_raw") and len(raw) != 8192:
            raise ValueError("Selected named SRAM is not exactly 8192 bytes")
        (snapshot_dir / f"{stage}.{key}.bin").write_bytes(raw)
        receipt[key] = {
            "present": True, "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "repo_relative_path": rel,
        }
    (snapshot_dir / f"{stage}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def run_native_pause_quit_selector_conflict(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
    snapshot_dir: Path | None = None,
) -> dict[str, object]:
    """Two *real processes* force a selection change during native pause.

    The source guest stays frozen until fixture B has independently selected
    another registered Modern profile. Host A must then refuse RtlWriteSram
    before touching first rider's 8KiB raw save. The handshake is a CI-only
    file gate for the existing physical SDL Up/Enter pause menu journey.
    """
    output = root / "native_pause_quit_selector_race"
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Two Process Profile Root With Spaces"
    user_root.mkdir()
    subprocess.run(
        [str(fixture), str(user_root), str(seed)],
        cwd=output, timeout=timeout, check=True,
        capture_output=True, text=True,
    )
    save = user_root / "saves/profile-native-ci-rider/save.srm"
    raw_before = save.read_bytes()
    if len(raw_before) != 8192:
        raise ValueError("Two-process fixture has no original 8192-byte SRAM")
    if snapshot_dir is not None:
        capture_native_selector_conflict_files(user_root, snapshot_dir, "before_A")
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    gate = output / "external_writer_committed.ready"
    log_path = output / "log.txt"
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "UR_BALDOSA_PAUSE_SMOKE": "1",
        "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1",
        "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "1952",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1",
        "UR_BALDOSA_PAUSE_QUIT_SMOKE": "1",
        "UR_BALDOSA_PAUSE_QUIT_CONFLICT_GATE": str(gate),
        "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "0",
        "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
        "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    armed = (
        "UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 "
        "live_race=1 modern_session=1 physical_sdl=1"
    )
    with log_path.open("wb") as sink:
        process = subprocess.Popen(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(script), str(rom)],
            cwd=output, env=env, stdout=sink, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                log = log_path.read_text(encoding="utf-8", errors="replace")
                if armed in log:
                    break
                if process.poll() is not None:
                    raise ValueError(
                        "Native guest exited before 2P pause: " + log[-1600:])
                time.sleep(0.02)
            else:
                raise TimeoutError("Native guest never reached live 2P pause")

            # True independent process B uses the shipping Modern state,
            # catalog, profile and selector CAS codecs to switch authority.
            changed = subprocess.run(
                [str(fixture), str(user_root), str(seed), "--add-second"],
                cwd=output, capture_output=True, text=True,
                timeout=timeout, check=True,
            )
            if "switched=native-ci-second sram=8192 distinct=1" not in changed.stdout:
                raise ValueError("Real competing Modern profile switch unverified")
            if snapshot_dir is not None:
                capture_native_selector_conflict_files(user_root, snapshot_dir, "after_B_before_A")
            gate.write_text("writer-B-committed\n", encoding="ascii")
            process.wait(timeout=timeout)
        except BaseException:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=timeout)
            raise

    if snapshot_dir is not None:
        capture_native_selector_conflict_files(user_root, snapshot_dir, "after_A")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    if process.returncode != 0:
        raise RuntimeError(
            f"Native conflict exit failed rc={process.returncode}: {log[-2200:]}")
    verify_named_profile_boot_bytes(log, raw_before)
    if log.count(armed) != 1 or log.count(
        "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1 paused=1 guest_steps=0"
    ) != 1:
        raise ValueError("Native conflict did not complete real paused SDL Quit")
    if (
        "UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=3" not in log or
        "UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed" not in log or
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider" in log or
        "UR_BALDOSA_NATIVE_PAUSE RELEASED " in log
    ):
        raise ValueError("Selection conflict did not reject BEFORE raw native save")
    if save.read_bytes() != raw_before:
        raise ValueError("Rejected native save overwrote old player's raw SRAM")
    first_profile = user_root / "saves/profile-native-ci-rider/host-profile.txt"
    if not first_profile.is_file() or not (user_root / "profiles-v1.txt").is_file():
        raise ValueError("Conflict removed original typed profile or catalog")
    for rider in ("native-ci-rider", "native-ci-second"):
        verified = subprocess.run(
            [str(fixture), str(user_root), rider, "--verify-native-save"],
            cwd=output, capture_output=True, text=True, timeout=timeout,
        )
        if verified.returncode or (
            f"UR_BALDOSA_NATIVE_PROFILE VERIFIED profile={rider} sram=8192"
            not in verified.stdout
        ):
            raise ValueError(f"Independent profile {rider} was corrupted")
    if list(user_root.rglob("*.urrun")) or (output / "saves").exists():
        raise ValueError("Conflicted process invented run or alternate SRAM root")
    return {
        "separate_native_and_modern_writer_processes": True,
        "authentic_paused_guest_frame": 1952,
        "conflicting_selector_change_committed_before_physical_quit": True,
        "raw_sram_8192_bytes_preserved_after_rejected_save": True,
        "both_named_profiles_independently_verified": True,
        "no_fake_completed_run": True,
    }


def run_native_pause_quit(
    exe: Path, rom: Path, script: Path, root: Path, fixture: Path,
    seed: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    """Quit an actual in-race 2P native guest from the frozen Modern menu.

    Uses the already established SDL pump and profile fixture. The shutdown
    must save into the named Modern root and publish through the same typed
    checkpoint as normal process exit; it must not reach script quit.
    """
    output = root / "native_modern_pause_quit"
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Modern Quit Profile Root With Spaces"
    user_root.mkdir()
    subprocess.run(
        [str(fixture), str(user_root), str(seed)],
        cwd=output, timeout=timeout, capture_output=True, text=True,
        check=True,
    )
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
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
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    try:
        completed = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(script), str(rom)],
            cwd=output, env=env, capture_output=True,
            text=True, errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Real native pause Quit did not close the host") from exc
    log = completed.stdout + "\n" + completed.stderr
    (output / "log.txt").write_text(log, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(
            f"Native pause Quit shutdown failed rc={completed.returncode}: "
            f"{log[-2500:]}"
        )
    verify_native_pause_quit_log(log)
    verify_named_profile_boot(log, seed)
    verify_native_profile_checkpoint(
        fixture, user_root, "native-ci-rider", log, timeout)
    save = user_root / "saves/profile-native-ci-rider/save.srm"
    if not save.is_file() or save.stat().st_size != 8192:
        raise ValueError("Native paused Quit lost the selected profile's 8KiB SRAM")
    if ((user_root / "saves/save.srm").exists() or
        (output / "saves").exists()):
        raise ValueError("Native paused Quit leaked into a competing SRAM root")
    fresh = verify_paused_quit_fresh_relaunch(
        exe, rom, output, user_root, fixture,
        video=video, timeout=timeout)
    return {
        "fresh_relaunch_of_quit_profile": fresh,
        "authentic_live_guest_pause_frame": 1952,
        "physical_sdl_menu_navigation": True,
        "quit_via_existing_sdl_shutdown": True,
        "native_guest_remained_paused_until_quit": True,
        "named_profile_checkpoint_verified_after_shutdown": True,
        "selected_profile_sram_bytes": save.stat().st_size,
        "event_success_synthesized": False,
    }



def run_native_two_original_windows_games(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, timeout: int,
) -> dict[str, object]:
    """Two actual overlapping original guests; one authentic stale writer."""
    # Reuse the independent QA's established byte decoder and interleaving
    # assertions without changing its candidate identity or gate authority.
    from qa02_exact_owner_two_games import (
        snapshot, validate_typed_raw, verify_interleaving,
        environment, game, ARMED, QUIT,
    )
    out = root / "native_two_original_windows_games"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Same Named Profile With Spaces"
    user_root.mkdir()
    subprocess.run([str(fixture), str(user_root), str(seed)],
                   cwd=out, check=True, capture_output=True,
                   text=True, timeout=timeout)
    evidence = out / "fault-bytes"
    evidence.mkdir()
    before = snapshot(user_root, evidence, "before_A")
    if before["raw"] != seed.read_bytes():
        raise ValueError("Source-original SRAM seed changed")
    validate_typed_raw(before)
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    a, b, c = (out / name for name in ("game-A", "game-B", "game-C"))
    for path in (a, b, c):
        path.mkdir()
    gate = out / "second-game-completed.ready"
    log_a = out / "game-A.log"
    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(script), str(rom)]
    with log_a.open("wb") as sink:
        first = subprocess.Popen(
            command, cwd=a, env=environment(user_root, gate=gate),
            stdout=sink, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                first_log = log_a.read_text(encoding="utf-8", errors="replace")
                if ARMED in first_log:
                    break
                if first.poll() is not None:
                    raise ValueError("Original game A stopped before its race pause")
                time.sleep(.02)
            else:
                raise TimeoutError("Original game A never reached frame-1952 pause")
            if first.poll() is not None:
                raise ValueError("Original game A not alive before B started")
            rc_b, log_b = game(
                exe, rom, script, config, b, environment(user_root),
                out / "game-B.log")
            if (rc_b != 0 or log_b.count(ARMED) != 1 or
                log_b.count(QUIT) != 1 or
                "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider status=committed"
                not in log_b):
                raise ValueError("Original game B failed authentic source save")
            verify_named_profile_boot_bytes(log_b, before["raw"])
            saved_b = snapshot(user_root, evidence, "after_B")
            validate_typed_raw(saved_b)
            if first.poll() is not None:
                raise ValueError("Original stale A died before B's committed save")
            gate.write_text("real-B-committed\n", encoding="ascii")
            first.wait(timeout=timeout)
        except BaseException:
            if first.poll() is None:
                first.kill()
                first.wait(timeout=30)
            raise
    saved_a = snapshot(user_root, evidence, "after_A")
    first_log = log_a.read_text(encoding="utf-8", errors="replace")
    if (first.returncode != 0 or first_log.count(ARMED) != 1 or
        first_log.count(QUIT) != 1 or
        "UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed" not in first_log or
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=native-ci-rider"
        in first_log):
        raise ValueError("Stale original game A did not fail before raw save")
    verify_named_profile_boot_bytes(first_log, before["raw"])
    comparison = verify_interleaving(before, saved_b, saved_a)
    cold = out / "short-cold.txt"
    cold.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    rc_c, log_c = game(
        exe, rom, cold, config, c, environment(user_root, pause=False),
        out / "game-C.log")
    if rc_c or "UR_BALDOSA_NATIVE_PROFILE REJECTED" in log_c:
        raise ValueError("Cold original game C rejected B's valid saved SRAM")
    verify_named_profile_boot_bytes(log_c, saved_b["raw"])
    verify_native_profile_checkpoint(
        fixture, user_root, "native-ci-rider", log_c, timeout)
    saved_c = snapshot(user_root, evidence, "after_C")
    validate_typed_raw(saved_c)
    if (saved_c["selector"], saved_c["catalog"]) != (
            saved_b["selector"], saved_b["catalog"]):
        raise ValueError("Cold C mutated selector or catalog")
    if any(user_root.rglob("*.urrun")) or any(user_root.rglob("*.urmatch")):
        raise ValueError("Two original guests fabricated result records")
    return {
        "actual_overlapping_original_game_processes": True,
        "same_profile_original_race_pause": 1952,
        "B_native_raw_and_typed_committed": True,
        "A_stale_save_refused_before_original_raw_write": True,
        "all_four_B_bytes_unchanged_by_A": True,
        "third_cold_game_loaded_B_SRAM": True,
        "changed_raw_bytes": comparison["raw_changed_bytes"],
        "source_original_canonical_four_stage_bytes_retained": True,
        "true_simultaneous_raw_writer_collision_proven": False,
        "physical_operator_acceptance": False,
        "qa_gate_credit": 0,
    }


def run_native_real_win32_prewrite_directory_denial(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    """Actual Windows file system DACL denies native prewrite intent staging.

    Uses a disposable CI-only profile. Unlike a synthetic denied callback,
    icacls must actually prevent a fresh file from being created. The entire
    DACL is restored in finally even if the source guest refuses or crashes.
    """
    out = root / "native_actual_win32_prewrite_dacl_denial"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Denied Real Win32 File System"
    user_root.mkdir()
    subprocess.run([str(fixture), str(user_root), str(seed)],
                   cwd=out, capture_output=True,
                   text=True, check=True, timeout=timeout)
    profile = user_root / "saves/profile-native-ci-rider"
    files = {
        "raw-sram": profile / "save.srm",
        "typed-profile": profile / "host-profile.txt",
        "selector": user_root / "host-state-v1.txt",
        "roster": user_root / "profiles-v1.txt",
    }
    before = {name: file.read_bytes() for name, file in files.items()}
    if len(before["raw-sram"]) != 8192 or before["raw-sram"] != seed.read_bytes():
        raise ValueError("ACL prewrite source fixture missing complete original guest SRAM")
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    sid_out = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        capture_output=True, text=True, timeout=10, check=True)
    sid_csv = list(csv.reader(sid_out.stdout.splitlines()))
    if len(sid_csv) != 1 or not sid_csv[0] or not sid_csv[0][-1].startswith("S-1-5-"):
        raise ValueError("Actual Windows user SID unavailable for disposable DACL test")
    sid = sid_csv[0][-1]
    denied = False
    log = ""
    rc = None
    during = None
    def icacls(*args: str) -> None:
        process = subprocess.run(["icacls", str(profile), *args, "/T"],
                                 capture_output=True, text=True, timeout=30)
        if (process.returncode or
            "Successfully processed" not in process.stdout):
            raise ValueError(
                "OS icacls " + " ".join(args[:1]) + " failed: " +
                (process.stdout + process.stderr)[-1000:])
    try:
        icacls("/deny", f"*{sid}:(WD,AD,WEA,WA,DE,DC)")
        denied = True
        probe = profile / "_product_acl_probe_NOT_a_save.txt"
        try:
            with probe.open("xb") as f:
                f.write(b"not a native game save")
        except PermissionError:
            if probe.exists():
                raise ValueError("Denied Win32 probe created a forbidden file")
        else:
            probe.unlink(missing_ok=True)
            raise ValueError("Actual OS DACL did not deny disposable profile write")
        env = os.environ.copy()
        env.update({
            "SNESRECOMP_USER_DATA_DIR": str(user_root),
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
            "SDL_VIDEODRIVER": video,
            "SDL_AUDIODRIVER": "dummy",
        })
        proc = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(script), str(rom)],
            cwd=out, env=env, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        rc = proc.returncode
        log = proc.stdout + "\n" + proc.stderr
        (out / "actual-win32-denied-save.log").write_text(log, encoding="utf-8")
        during = {name: file.read_bytes() for name, file in files.items()}
    finally:
        if denied:
            icacls("/remove:d", f"*{sid}")
    if during is None:
        raise ValueError("Win32 denial did not capture source canonical bytes")
    if (log.count("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1") != 1 or
        log.count("UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM profile=native-ci-rider bytes=8192") != 1):
        raise ValueError("Original Windows guest failed to reach actual denied save")
    if ("native_sram_intent_not_durable" not in log and
        "native_save_preflight_failed" not in log and
        "save_profile_lock_unavailable" not in log):
        raise ValueError(
            f"Real NTFS denied write produced no source pre-raw refusal; exit={rc}")
    pending = profile / "native-sram-checkpoint.pending"
    if (during != before or pending.exists() or
        list(user_root.rglob("*.urrun")) or list(user_root.rglob("*.urmatch"))):
        raise ValueError("Real denied Win32 save mutated canonical source bytes")
    short = out / "fresh-short.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    clean = env.copy()
    clean.pop("UR_BALDOSA_PAUSE_SMOKE", None)
    clean.pop("UR_BALDOSA_PAUSE_REQUIRE_RACE", None)
    clean.pop("UR_BALDOSA_PAUSE_SMOKE_AT_FRAME", None)
    clean.pop("UR_BALDOSA_PHYSICAL_PAUSE_SMOKE", None)
    clean.pop("UR_BALDOSA_PAUSE_QUIT_SMOKE", None)
    for i in (1, 2):
        process = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(short), str(rom)],
            cwd=out, env=clean, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        fresh = process.stdout + "\n" + process.stderr
        (out / f"cold-boot-{i}.log").write_text(fresh, encoding="utf-8")
        if process.returncode or "UR_BALDOSA_NATIVE_PROFILE REJECTED" in fresh:
            raise ValueError("Restored NTFS DACL prevented subsequent native boot")
        verify_named_profile_boot_bytes(fresh, before["raw-sram"])
        if (any(path.read_bytes() != before[label] for label, path in files.items())
            or pending.exists()):
            raise ValueError("Post-DACL original cold guest changed committed save")
    evidence = out / "fault-bytes"
    evidence.mkdir()
    measurements = {}
    for label, file in files.items():
        for stage, source in (
            ("before", before), ("denied", during),
        ):
            data = source[label]
            name = f"{label}.{stage}.bin"
            (evidence / name).write_bytes(data)
            measurements[name] = {
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            }
        name = f"{label}.second-cold.bin"
        data = file.read_bytes()
        (evidence / name).write_bytes(data)
        measurements[name] = {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
        }
    if len(measurements) != 12:
        raise ValueError("Win32 DACL witness lacks complete canonical evidence")
    (evidence / "file-receipt.json").write_text(
        json.dumps(measurements, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    (out / "refusal.json").write_text(
        json.dumps({
            "schema": "ur-baldosa-source-real-win32-prewrite-ntfs-dacl/1",
            "actual_os_write_denied": True,
            "write_access_restored_before_cold_boots": True,
            "source_guest_frame": 1952,
            "native_exit_code": rc,
            "raw_guest_save_write_attempted": False,
            "canonical_state_unchanged": True,
            "second_boot_source_exact": True,
            "real_disk_full_or_power_loss": False,
            "post_raw_write_acl_denial": False,
            "physical_operator_accepted": False,
            "qa_gate_credit": 0,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "actual_windows_directory_dacl_write_denied": True,
        "original_game_rejected_before_raw_overwrite": True,
        "all_four_canonical_files_unchanged": True,
        "dacl_restored_in_finally": True,
        "two_source_original_guest_cold_boots_after_restoration": True,
        "real_post_raw_denial": False,
        "real_disk_full_power_loss": False,
        "release_gate_credit": 0,
    }


def run_native_journaled_b_crash_then_a_isolation(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    """Real Win32 B after-raw journaled cut, then B replay and explicit healthy A.

    Complements F5's REAL unjournaled B cut. Do not infer atomic NTFS
    durability, an actual power cut, or human operation of the CMD menu.
    """
    out = root / "native_journaled_b_crash_then_a"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Journaled B and Intact A"
    user_root.mkdir()
    for args in (
        [str(fixture), str(user_root), str(seed)],
        [str(fixture), str(user_root), str(seed), "--add-second-keep-first"],
    ):
        subprocess.run(args, cwd=out, check=True,
                       capture_output=True, text=True, timeout=timeout)
    a = user_root / "saves/profile-native-ci-rider"
    b = user_root / "saves/profile-native-ci-second"
    files = {
        "a-raw": a / "save.srm",
        "a-typed": a / "host-profile.txt",
        "b-raw": b / "save.srm",
        "b-typed": b / "host-profile.txt",
        "selector": user_root / "host-state-v1.txt",
        "roster": user_root / "profiles-v1.txt",
    }
    orig = {name: path.read_bytes() for name, path in files.items()}
    if (len(orig["a-raw"]) != 8192 or len(orig["b-raw"]) != 8192 or
        orig["a-raw"] == orig["b-raw"]):
        raise ValueError("Journaled two-racer fixture not independently valid")
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    short = out / "fresh-short.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    def launch(tag: str, *, guest_script: Path = short,
               extra: dict[str, str] | None = None) -> tuple[int, str]:
        child_env = dict(env)
        if extra:
            child_env.update(extra)
        child = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(guest_script), str(rom)],
            cwd=out, env=child_env, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        log = child.stdout + "\n" + child.stderr
        (out / f"{tag}.log").write_text(log, encoding="utf-8")
        return child.returncode, log
    rc, selected_log = launch("explicit-select-b", extra={
        "UR_BALDOSA_RECOVERY_ACTION": "healthy",
        "UR_BALDOSA_RECOVERY_PROFILE_ID": "native-ci-second",
    })
    if (rc != 89 or selected_log.count(
            "UR_BALDOSA_RECOVERY_CHOICE choice=healthy") != 1 or
        "completed=1" not in selected_log):
        raise ValueError("Journaled B witness failed explicit original EXE selection")
    selected = {name: path.read_bytes() for name, path in files.items()}
    if (selected["selector"] == orig["selector"] or
        any(selected[k] != orig[k] for k in files if k != "selector")):
        raise ValueError("B selection changed unrelated source bytes")
    rc, healthy_log = launch("healthy-b-boot")
    if rc or "RECOVERY_RECONCILED" in healthy_log:
        raise ValueError("Distinct stock racer B did not boot before cut")
    verify_named_profile_boot_bytes(
        healthy_log, selected["b-raw"], profile_id="native-ci-second")
    rc, crash_log = launch("source-b-after-raw-crash", guest_script=script,
        extra={
            "UR_BALDOSA_PAUSE_SMOKE": "1",
            "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1",
            "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "1952",
            "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1",
            "UR_BALDOSA_PAUSE_QUIT_SMOKE": "1",
            "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "0",
            "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
            "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
            "UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE": "1",
            "UR_BALDOSA_QA_LEGACY_UNJOURNALED_CRASH": "0",
        })
    if (rc != 86 or crash_log.count(
            "UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1") != 1 or
        crash_log.count(
            "UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_RAW_WRITE exit=86 typed_checkpoint=0") != 1):
        raise ValueError("Real journaled selected B did not stop at source raw cut")
    verify_named_profile_boot_bytes(
        crash_log, selected["b-raw"], profile_id="native-ci-second")
    crashed = {name: path.read_bytes() for name, path in files.items()}
    pending = b / "native-sram-checkpoint.pending"
    if (len(crashed["b-raw"]) != 8192 or
        crashed["b-raw"] == selected["b-raw"] or
        any(crashed[k] != selected[k] for k in files if k != "b-raw") or
        not pending.is_file() or pending.is_symlink()):
        raise ValueError("Journaled source B crash not isolated to raw and intent")
    intent = pending.read_bytes()
    marker = b"UR-BALDOSA-NATIVE-SRAM-INTENT/1\n"
    if not intent.startswith(marker) or len(intent) > 100_000:
        raise ValueError("Selected B durable intent lacks canonical version/frame")
    parts = intent[len(marker):].split(b"\n", 2)
    if (len(parts) != 3 or not all(p.isdigit() for p in parts[:2]) or
        any(len(p) > 8 for p in parts[:2])):
        raise ValueError("Selected B durable intent lacks bounded old/new lengths")
    old_len, new_len = int(parts[0]), int(parts[1])
    if (old_len != len(crashed["b-typed"]) or
        new_len <= 0 or new_len > 65_536 or
        len(parts[2]) != old_len + new_len or
        parts[2][:old_len] != crashed["b-typed"]):
        raise ValueError("B prewrite intent does not contain exact old typed profile")
    intended_next_typed = parts[2][old_len:]
    rc, recon_log = launch("first-b-cold-recovery")
    if (rc != 0 or recon_log.count(
            "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED exact_staged_guest_sram=1 no_records=1") != 1):
        raise ValueError("Actual fresh B guest did not reconcile journal exactly once")
    verify_named_profile_boot_bytes(
        recon_log, crashed["b-raw"], profile_id="native-ci-second")
    recovered = {name: path.read_bytes() for name, path in files.items()}
    if (recovered["b-typed"] != intended_next_typed or
        recovered["b-raw"] != crashed["b-raw"] or
        recovered["b-typed"] == crashed["b-typed"] or
        any(recovered[k] != crashed[k] for k in files if
            k not in ("b-raw", "b-typed")) or pending.exists()):
        raise ValueError("B journal recovery changed A/catalog/selector or failed typed CAS")
    archived = list(b.glob("native-sram-recovered-*.txt"))
    if len(archived) != 1 or archived[0].read_bytes() != intent:
        raise ValueError("B journal was not archived and retired exactly")
    rc, second_b_log = launch("second-b-cold")
    if rc or "RECOVERY_RECONCILED" in second_b_log:
        raise ValueError("B second cold boot repeated the typed commit")
    verify_named_profile_boot_bytes(
        second_b_log, crashed["b-raw"], profile_id="native-ci-second")
    if any(path.read_bytes() != recovered[name] for name, path in files.items()):
        raise ValueError("Second B original guest mutated reconciled state")
    rc, choose_a_log = launch("explicit-select-a", extra={
        "UR_BALDOSA_RECOVERY_ACTION": "healthy",
        "UR_BALDOSA_RECOVERY_PROFILE_ID": "native-ci-rider",
    })
    if (rc != 89 or choose_a_log.count(
            "UR_BALDOSA_RECOVERY_CHOICE choice=healthy") != 1 or
        "completed=1" not in choose_a_log):
        raise ValueError("Original executable did not explicitly switch to intact A")
    switched = {name: path.read_bytes() for name, path in files.items()}
    if (switched["selector"] != orig["selector"] or
        any(switched[k] != recovered[k] for k in files if k != "selector")):
        raise ValueError("Explicit A switch overwrote B's recovered source state")
    for count in (1, 2):
        rc, log = launch(f"healthy-a-cold-{count}")
        if rc or "RECOVERY_RECONCILED" in log:
            raise ValueError("Fresh native A did not boot independently after B replay")
        verify_named_profile_boot_bytes(
            log, orig["a-raw"], profile_id="native-ci-rider")
        if (any(path.read_bytes() != switched[name]
                for name, path in files.items()) or
            pending.exists() or archived[0].read_bytes() != intent):
            raise ValueError("A boots mutated B's journaled recovery or archive")
    if (list(user_root.rglob("*.urrun")) or
        list(user_root.rglob("*.urmatch"))):
        raise ValueError("B journal/A selection minted unearned records")
    evidence = out / "fault-bytes"
    evidence.mkdir()
    hashes = {}
    for label in files:
        for stage, snapshot in (
            ("b-selected", selected), ("b-crash", crashed),
            ("b-reconciled", recovered), ("a-selected", switched),
        ):
            data = snapshot[label]
            name = f"{label}.{stage}.bin"
            (evidence / name).write_bytes(data)
            hashes[name] = {
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            }
        name = f"{label}.second-a-cold.bin"
        data = files[label].read_bytes()
        (evidence / name).write_bytes(data)
        hashes[name] = {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
        }
    for label, data in (("intent.crash.bin", intent),
                        ("intent.archived.bin", archived[0].read_bytes())):
        (evidence / label).write_bytes(data)
        hashes[label] = {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
        }
    if len(hashes) != 32 or pending.exists():
        raise ValueError("Journaled B/A evidence member count or intent invalid")
    (evidence / "file-receipt.json").write_text(
        json.dumps(hashes, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    return {
        "original_guest_b_journaled_post_raw_exit_86": True,
        "b_typed_old_at_crash_and_new_after_one_cold": True,
        "b_raw_preserved_and_intent_archived_byte_identical": True,
        "intact_a_unchanged_through_b_reconciliation": True,
        "original_executable_explicitly_selected_a": True,
        "two_source_native_a_cold_boots_and_two_b_cold_boots": True,
        "six_canonical_files_five_stages_plus_intents_retained": len(hashes),
        "no_unearned_records": True,
        "release_gate_credit": 0,
    }


def run_native_real_crashed_second_healthy_first(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    """F5: actual original guest writes B raw then dies; intact A still boots.

    No synthetic post-crash damage. The original Win32 RtlWriteSram writes the
    selected B's 8 KiB raw image before _Exit(86). An explicit user-authorized
    one-shot switch must select actual healthy A; no B recovery is performed.
    """
    out = root / "native_real_b_crash_healthy_a_recovery"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Two Separate Original Guest Racers"
    user_root.mkdir()
    for command in ([str(fixture), str(user_root), str(seed)],
                    [str(fixture), str(user_root), str(seed),
                     "--add-second-keep-first"]):
        subprocess.run(command, cwd=out, check=True, timeout=timeout,
                       capture_output=True, text=True)
    a = user_root / "saves/profile-native-ci-rider"
    b = user_root / "saves/profile-native-ci-second"
    a_raw, a_typed = a / "save.srm", a / "host-profile.txt"
    b_raw, b_typed = b / "save.srm", b / "host-profile.txt"
    selector, catalog = user_root / "host-state-v1.txt", user_root / "profiles-v1.txt"
    six = (a_raw, a_typed, b_raw, b_typed, selector, catalog)
    before = {p: p.read_bytes() for p in six}
    if (len(before[a_raw]) != 8192 or len(before[b_raw]) != 8192 or
        before[a_raw] == before[b_raw]):
        raise ValueError("F5 fixture lacks two distinct valid source racers")
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    short = out / "cold.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    def invoke(*, source_script: Path = short,
               overrides: dict[str, str] | None = None) -> tuple[int, str]:
        launched = env.copy()
        if overrides:
            launched.update(overrides)
        proc = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(source_script), str(rom)],
            cwd=out, env=launched, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        return proc.returncode, proc.stdout + "\n" + proc.stderr
    def save_log(name: str, log: str) -> None:
        (out / (name + ".log")).write_text(log, encoding="utf-8")
    # First select healthy B using the SAME explicit native action offered
    # by the packaged launcher. Selection is next-process-only.
    rc, log = invoke(overrides={
        "UR_BALDOSA_RECOVERY_ACTION": "healthy",
        "UR_BALDOSA_RECOVERY_PROFILE_ID": "native-ci-second",
    })
    save_log("select-b-before-fault", log)
    if rc != 89 or "choice=healthy" not in log or "completed=1" not in log:
        raise ValueError("F5 did not select separately authorized B")
    selected = {p: p.read_bytes() for p in six}
    if (any(selected[p] != before[p] for p in (a_raw, a_typed, b_raw, b_typed, catalog))
        or selected[selector] == before[selector]):
        raise ValueError("Pre-crash B selector changed unrelated canonical bytes")
    rc, boot = invoke()
    save_log("healthy-b-original-boot", boot)
    if rc != 0:
        raise ValueError("Original B guest did not boot before fault")
    verify_named_profile_boot_bytes(
        boot, selected[b_raw], profile_id="native-ci-second")
    if any(p.read_bytes() != selected[p] for p in six):
        raise ValueError("Healthy B pre-crash short guest modified authority")
    cut_env = {
        "UR_BALDOSA_PAUSE_SMOKE": "1",
        "UR_BALDOSA_PAUSE_REQUIRE_RACE": "1",
        "UR_BALDOSA_PAUSE_SMOKE_AT_FRAME": "1952",
        "UR_BALDOSA_PHYSICAL_PAUSE_SMOKE": "1",
        "UR_BALDOSA_PAUSE_QUIT_SMOKE": "1",
        "UR_BALDOSA_PAUSE_PANEL_NAV_SMOKE": "0",
        "UR_BALDOSA_DELAYED_RESTART_SMOKE": "0",
        "UR_BALDOSA_RESTART_SAME_FRAME_SMOKE": "0",
        "UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE": "1",
        "UR_BALDOSA_QA_LEGACY_UNJOURNALED_CRASH": "1",
    }
    rc, crash_log = invoke(source_script=script, overrides=cut_env)
    save_log("actual-b-post-raw-crash", crash_log)
    if (rc != 86 or
        crash_log.count("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1") != 1 or
        crash_log.count("UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_RAW_WRITE exit=86 typed_checkpoint=0") != 1):
        raise ValueError(f"Original B writer did not terminate at F5 cut: {rc} {crash_log[-1200:]}")
    verify_named_profile_boot_bytes(
        crash_log, selected[b_raw], profile_id="native-ci-second")
    crashed = {p: p.read_bytes() for p in six}
    if (len(crashed[b_raw]) != 8192 or crashed[b_raw] == selected[b_raw] or
        any(crashed[p] != selected[p] for p in
            (a_raw, a_typed, b_typed, selector, catalog)) or
        (b / "native-sram-checkpoint.pending").exists()):
        raise ValueError("F5 did not isolate exact real B raw-only crash")
    rc, rejected = invoke()
    save_log("b-cold-refusal", rejected)
    if rc != 7 or "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in rejected:
        raise ValueError("Broken real B automatically recovered without intent")
    if any(p.read_bytes() != crashed[p] for p in six):
        raise ValueError("Refused B cold launch changed another racer")
    rc, switched = invoke(overrides={
        "UR_BALDOSA_RECOVERY_ACTION": "healthy",
        "UR_BALDOSA_RECOVERY_PROFILE_ID": "native-ci-rider",
    })
    save_log("explicit-a-selection", switched)
    if (rc != 89 or "choice=healthy" not in switched or
        "completed=1" not in switched or
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in switched):
        raise ValueError("Original Windows recovery command could not select intact A")
    after_switch = {p: p.read_bytes() for p in six}
    if (any(after_switch[p] != crashed[p] for p in
            (a_raw, a_typed, b_raw, b_typed, catalog)) or
        after_switch[selector] != before[selector]):
        raise ValueError("Real B recovery changed source or healthy A, or wrong selector")
    for n in (1, 2):
        rc, fresh = invoke()
        save_log(f"cold-a-{n}", fresh)
        if rc != 0 or "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in fresh:
            raise ValueError("Healthy A after genuine B crash did not boot cleanly")
        verify_named_profile_boot_bytes(
            fresh, before[a_raw], profile_id="native-ci-rider")
        if any(p.read_bytes() != after_switch[p] for p in six):
            raise ValueError("Healthy A replay mutated damaged B or unrelated data")
    if (list(user_root.rglob("*.urrun")) or
        list(user_root.rglob("*.urmatch"))):
        raise ValueError("Cross-profile B crash recovery invented game Records")
    evidence = out / "fault-bytes"
    evidence.mkdir()
    labels = {
        "a-raw": a_raw, "a-typed": a_typed,
        "b-raw": b_raw, "b-typed": b_typed,
        "selector": selector, "roster": catalog,
    }
    receipt = {}
    for label, p in labels.items():
        for stage, state in (("selected", selected),
                             ("crash", crashed),
                             ("after", after_switch)):
            data = state[p]
            name = f"{label}.{stage}.bin"
            (evidence / name).write_bytes(data)
            receipt[name] = {"bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest()}
        latest = p.read_bytes()
        name = f"{label}.second-cold.bin"
        (evidence / name).write_bytes(latest)
        receipt[name] = {"bytes": len(latest),
                         "sha256": hashlib.sha256(latest).hexdigest()}
    if len(receipt) != 24:
        raise ValueError("F5 6-file, four-stage evidence count mismatch")
    (evidence / "file-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return {
        "original_windows_guest_b_post_raw_exit_86": True,
        "genuine_guest_b_raw_differs": True,
        "healthy_a_raw_typed_exact": True,
        "damaged_b_raw_typed_exact_after_switch": True,
        "explicit_same_exe_switch_to_a": True,
        "two_clean_original_a_cold_boots": True,
        "six_canonical_files_four_stages_archived": True,
        "no_invented_records": True,
        "release_gate_credit": 0,
    }


def run_native_three_profile_unrelated_damage(
    exe: Path, rom: Path, root: Path, fixture: Path, seed: Path,
    *, video: str, timeout: int,
) -> dict[str, object]:
    """Three genuinely rostered Modern racers, only source/target locked.

    Unrelated C typed damage and selected A raw damage are deliberate,
    synthetic fixture inputs. Both actual recovery and cold boot use the
    same compiled original native Windows executable as the full game.
    """
    out = root / "native_three_profile_unrelated_damage"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Three Catalogued Racers"
    user_root.mkdir()
    for args in (
        [str(fixture), str(user_root), str(seed)],
        [str(fixture), str(user_root), str(seed), "--add-second-keep-first"],
        [str(fixture), str(user_root), str(seed), "--add-third-keep-first"],
    ):
        subprocess.run(args, cwd=out, check=True, timeout=timeout,
                       capture_output=True, text=True)
    a = user_root / "saves/profile-native-ci-rider"
    b = user_root / "saves/profile-native-ci-second"
    c = user_root / "saves/profile-native-ci-third"
    a_raw, a_typed = a / "save.srm", a / "host-profile.txt"
    b_raw, b_typed = b / "save.srm", b / "host-profile.txt"
    c_raw, c_typed = c / "save.srm", c / "host-profile.txt"
    selector, roster = user_root / "host-state-v1.txt", user_root / "profiles-v1.txt"
    files = (a_raw, a_typed, b_raw, b_typed, c_raw, selector, roster)
    before = {p: p.read_bytes() for p in files}
    old_c_typed = c_typed.read_bytes()
    if (len(before[a_raw]) != 8192 or len(before[b_raw]) != 8192 or
        len(before[c_raw]) != 8192 or
        len({before[a_raw], before[b_raw], before[c_raw]}) != 3 or
        len(old_c_typed) < 8192):
        raise ValueError("Three-racer canonical fixture lacks distinct SRAM")
    c_typed.unlink()  # unrelated damaged C, never chosen or repaired
    changed = bytearray(before[a_raw])
    changed[0x0711] ^= 0x35
    a_raw.write_bytes(changed)
    damaged = {p: p.read_bytes() for p in files}
    if damaged[a_raw] == before[a_raw] or c_typed.exists():
        raise ValueError("Three-racer fixture damage did not hold")
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    short = out / "short.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    def invoke(overrides: dict[str, str] | None = None) -> tuple[int, str]:
        supplied = {**env, **(overrides or {})}
        p = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(short), str(rom)],
            cwd=out, env=supplied, capture_output=True, text=True,
            errors="replace", timeout=timeout)
        return p.returncode, p.stdout + "\n" + p.stderr
    rc, rejected = invoke()
    (out / "damaged-a-refusal.log").write_text(rejected, encoding="utf-8")
    if rc != 7 or "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in rejected:
        raise ValueError("Damaged selected A did not fail closed")
    rc, blocked = invoke({
        "UR_BALDOSA_RECOVERY_ACTION": "healthy",
        "UR_BALDOSA_RECOVERY_PROFILE_ID": "native-ci-third",
    })
    (out / "invalid-c-selection.log").write_text(blocked, encoding="utf-8")
    if rc != 88 or any(p.read_bytes() != damaged[p] for p in files):
        raise ValueError("Damaged third target became implicitly authorized")
    rc, switched = invoke({
        "UR_BALDOSA_RECOVERY_ACTION": "healthy",
        "UR_BALDOSA_RECOVERY_PROFILE_ID": "native-ci-second",
    })
    (out / "explicit-b-selection.log").write_text(switched, encoding="utf-8")
    if (rc != 89 or "choice=healthy" not in switched or
        "completed=1" not in switched or
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in switched):
        raise ValueError("Unrelated damaged C stranded otherwise valid B")
    selected = {p: p.read_bytes() for p in files}
    if (selected[selector] == damaged[selector] or
        any(selected[p] != damaged[p] for p in files if p != selector) or
        c_typed.exists()):
        raise ValueError("Three-catalog healthy switch changed another owner")
    for n in (1, 2):
        rc, log = invoke()
        (out / f"healthy-b-cold-{n}.log").write_text(
            log, encoding="utf-8")
        if rc != 0 or "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in log:
            raise ValueError("Healthy B could not cold boot with third broken")
        verify_named_profile_boot_bytes(
            log, before[b_raw], profile_id="native-ci-second")
        if (any(p.read_bytes() != selected[p] for p in files) or
            c_typed.exists()):
            raise ValueError("Three-profile cold guest altered unrelated damaged C")
    if list(user_root.rglob("*.urrun")) or list(user_root.rglob("*.urmatch")):
        raise ValueError("Three-profile emergency selection invented Records")
    evidence = out / "fault-bytes"
    evidence.mkdir()
    name_for = {
        a_raw: "a-raw", a_typed: "a-typed",
        b_raw: "b-raw", b_typed: "b-typed", c_raw: "c-raw",
        selector: "selector", roster: "roster",
    }
    exact = {}
    for p, label in name_for.items():
        for stage, snapshot in (("before", before),
                                ("damaged", damaged), ("after", selected)):
            name = f"{label}.{stage}.bin"
            data = snapshot[p]
            (evidence / name).write_bytes(data)
            exact[name] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        name = f"{label}.second-cold.bin"
        data = p.read_bytes()
        (evidence / name).write_bytes(data)
        exact[name] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
    (evidence / "c-typed.original-then-absent.bin").write_bytes(old_c_typed)
    exact["c-typed.original-then-absent.bin"] = {
        "sha256": hashlib.sha256(old_c_typed).hexdigest(),
        "bytes": len(old_c_typed),
    }
    (evidence / "file-receipt.json").write_text(
        json.dumps(exact, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    return {
        "registered_three_canonical_racers": True,
        "damaged_a_refused_before_guest": True,
        "unrelated_c_missing_typed_preserved": True,
        "invalid_c_target_rejected": True,
        "explicit_b_target_selected": True,
        "two_real_original_b_cold_boots": True,
        "only_selector_changed_after_explicit_selection": True,
        "source_storage_not_scanned_for_orphans": True,
        "all_canonical_evidence_bytes_retained": len(exact),
        "release_gate_credit": 0,
    }


def run_native_healthy_alternate_from_damaged_source(
    exe: Path, rom: Path, root: Path, fixture: Path, seed: Path,
    *, video: str, timeout: int,
) -> dict[str, object]:
    """A genuine fresh Windows binary leaves damaged P1 untouched and boots P2.

    Production source selector only; initial disposable raw-byte damage is a
    negative fixture, not a fabricated real guest crash. Original actual
    _Exit(86) is separately established by the adjacent bounded producer.
    """
    output = root / "native_recovery_healthy_alternate"
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Damaged P1 But Healthy P2"
    user_root.mkdir()
    subprocess.run(
        [str(fixture), str(user_root), str(seed)],
        cwd=output, check=True, capture_output=True,
        text=True, timeout=timeout)
    subprocess.run(
        [str(fixture), str(user_root), str(seed),
         "--add-second-keep-first"],
        cwd=output, check=True, capture_output=True,
        text=True, timeout=timeout)
    source = user_root / "saves/profile-native-ci-rider"
    healthy = user_root / "saves/profile-native-ci-second"
    s_raw, s_typed = source / "save.srm", source / "host-profile.txt"
    h_raw, h_typed = healthy / "save.srm", healthy / "host-profile.txt"
    catalog = user_root / "profiles-v1.txt"
    selector = user_root / "host-state-v1.txt"
    baseline = {p: p.read_bytes() for p in
                (s_raw, s_typed, h_raw, h_typed, catalog, selector)}
    changed = bytearray(baseline[s_raw])
    if len(changed) != 8192:
        raise ValueError("Disposal test source is not full native SRAM")
    changed[0x0711] ^= 0x35
    s_raw.write_bytes(changed)
    mismatch = s_raw.read_bytes()
    if mismatch == baseline[s_raw] or h_raw.read_bytes() != baseline[h_raw]:
        raise ValueError("No independent damaged source and healthy destination")
    script = output / "short.txt"
    script.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_PROFILE_BOOT_SRAM_WITNESS": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    args = [str(exe), "--no-launcher", "--config", str(config),
            "--script", str(script), str(rom)]
    refused = subprocess.run(
        args, env=env, cwd=output, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    refused_log = refused.stdout + "\n" + refused.stderr
    (output / "damaged-source-refusal.log").write_text(
        refused_log, encoding="utf-8")
    if refused.returncode != 7 or (
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in refused_log):
        raise ValueError("Real Windows guest started with unauthorised raw source")
    invalid = dict(env)
    invalid.update({
        "UR_BALDOSA_RECOVERY_ACTION": "healthy",
        "UR_BALDOSA_RECOVERY_PROFILE_ID": "unregistered",
    })
    bad = subprocess.run(
        args, env=invalid, cwd=output, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    if bad.returncode != 88 or selector.read_bytes() != baseline[selector]:
        raise ValueError("Unregistered emergency destination changed selector")
    confirmed = dict(invalid)
    confirmed["UR_BALDOSA_RECOVERY_PROFILE_ID"] = "native-ci-second"
    switched = subprocess.run(
        args, env=confirmed, cwd=output, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    switched_log = switched.stdout + "\n" + switched.stderr
    (output / "explicit-healthy-selection.log").write_text(
        switched_log, encoding="utf-8")
    if switched.returncode != 89 or (
        "UR_BALDOSA_RECOVERY_CHOICE choice=healthy" not in switched_log
    ) or "completed=1" not in switched_log or (
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in switched_log):
        raise ValueError("Original Win32 binary did not select healthy destination")
    if selector.read_bytes() == baseline[selector]:
        raise ValueError("Explicit selector publication did not occur")
    for p in (s_typed, h_raw, h_typed, catalog):
        if p.read_bytes() != baseline[p]:
            raise ValueError(f"Healthy selection mutated canonical nonselector {p}")
    if s_raw.read_bytes() != mismatch:
        raise ValueError("Healthy selection silently repaired damaged source SRAM")
    fresh = subprocess.run(
        args, env=env, cwd=output, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    log = fresh.stdout + "\n" + fresh.stderr
    (output / "fresh-healthy-guest.log").write_text(log, encoding="utf-8")
    if fresh.returncode:
        raise ValueError(
            f"Fresh native P2 rejected after explicit selector: {fresh.returncode}")
    verify_named_profile_boot_bytes(
        log, baseline[h_raw], profile_id="native-ci-second")
    if s_raw.read_bytes() != mismatch or s_typed.read_bytes() != baseline[s_typed]:
        raise ValueError("Fresh healthy guest modified damaged P1")
    if list(user_root.rglob("*.urrun")):
        raise ValueError("Healthy selector published invented Records")
    return {
        "real_windows_binary": True,
        "damaged_source_refused_before_guest": True,
        "unregistered_target_rejected": True,
        "healthy_target_selected_without_live_guest": True,
        "healthy_original_sram_booted_on_fresh_process": True,
        "damaged_raw_and_typed_preserved": True,
        "catalog_and_healthy_profile_unchanged": True,
        "records_invented": False,
    }


def run_native_prewrite_intent_abandon(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    """Actual native Win32 pre-raw process cut after durable write-ahead intent."""
    out = root / "native_prewrite_intent_abandon"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Original Guest Prewrite Cut"
    user_root.mkdir()
    subprocess.run([str(fixture), str(user_root), str(seed)],
                   check=True, cwd=out, capture_output=True,
                   text=True, timeout=timeout)
    profile = user_root / "saves/profile-native-ci-rider"
    raw = profile / "save.srm"
    typed = profile / "host-profile.txt"
    selector = user_root / "host-state-v1.txt"
    roster = user_root / "profiles-v1.txt"
    pending = profile / "native-sram-checkpoint.pending"
    sources = {
        "raw-sram": raw, "typed-profile": typed,
        "selector": selector, "roster": roster,
    }
    before = {name: path.read_bytes() for name, path in sources.items()}
    if len(before["raw-sram"]) != 8192 or before["raw-sram"] != seed.read_bytes():
        raise ValueError("F1 prewrite fault lacks genuine expected guest source SRAM")
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
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
        "UR_BALDOSA_QA_CRASH_AFTER_INTENT_BEFORE_RAW": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    original = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=out, env=env, capture_output=True, text=True,
        errors="replace", timeout=timeout)
    log = original.stdout + "\n" + original.stderr
    (out / "crash.log").write_text(log, encoding="utf-8")
    if (original.returncode != 84 or
        log.count("UR_BALDOSA_NATIVE_PROFILE QA_CRASH_PRE_RAW "
                  "exit=84 intent_durable=1 raw_not_written=1") != 1 or
        log.count("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1") != 1 or
        "UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_RAW_WRITE" in log or
        "UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=" in log):
        raise ValueError(
            f"Real Win32 process failed pre-raw source cut rc={original.returncode}"
            f" tail={log[-1200:]}")
    verify_named_profile_boot_bytes(log, before["raw-sram"])
    at_crash = {name: path.read_bytes() for name, path in sources.items()}
    if at_crash != before or not pending.is_file() or pending.is_symlink():
        raise ValueError("F1 prewrite fault mutated canonical files or lost intent")
    intent = pending.read_bytes()
    if len(intent) < 8192 or list(user_root.rglob("*.urrun")):
        raise ValueError("F1 prewrite crash lacked intact intent or fabricated Records")
    clean = env.copy()
    clean.pop("UR_BALDOSA_QA_CRASH_AFTER_INTENT_BEFORE_RAW", None)
    short = out / "fresh-short.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(short), str(rom)]
    stages = []
    for index in (1, 2):
        proc = subprocess.run(
            command, cwd=out, env=clean,
            capture_output=True, text=True,
            errors="replace", timeout=timeout)
        fresh = proc.stdout + "\n" + proc.stderr
        (out / f"cold-{index}.log").write_text(fresh, encoding="utf-8")
        if (proc.returncode != 0 or
            "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in fresh or
            "UR_BALDOSA_NATIVE_PROFILE REJECTED" in fresh):
            raise ValueError("F1 original cold Windows guest did not preserve old/old")
        verify_named_profile_boot_bytes(fresh, before["raw-sram"])
        snapshots = {name: path.read_bytes() for name, path in sources.items()}
        if snapshots != before or pending.exists():
            raise ValueError("F1 cold boot published unearned typed/raw or retained stale intent")
        stages.append(snapshots)
    evidence = out / "fault-bytes"
    evidence.mkdir()
    hashes = {}
    for label in sources:
        for stage, raw_files in (
            ("before", before),
            ("crash", at_crash),
            ("first-cold", stages[0]),
            ("second-cold", stages[1]),
        ):
            name = f"{label}.{stage}.bin"
            b = raw_files[label]
            (evidence / name).write_bytes(b)
            hashes[name] = {"sha256": hashlib.sha256(b).hexdigest(),
                            "bytes": len(b)}
    (evidence / "intent.pre-raw.bin").write_bytes(intent)
    hashes["intent.pre-raw.bin"] = {
        "sha256": hashlib.sha256(intent).hexdigest(), "bytes": len(intent)}
    (evidence / "file-receipt.json").write_text(
        json.dumps(hashes, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    if (len(hashes) != 17 or
        any(stages[i] != before for i in (0, 1))):
        raise ValueError("F1 prewrite evidence export incomplete")
    return {
        "genuine_original_win32_guest_frame": 1952,
        "source_process_cut_after_durable_intent": 84,
        "original_rtl_write_sram_not_executed": True,
        "canonical_raw_and_typed_unchanged_at_cut": True,
        "intent_retired_only_during_first_cold": True,
        "two_native_cold_boots_same_committed_generation": True,
        "all_17_evidence_files_SHA256_bound": True,
        "release_gate_credit": 0,
    }


def run_native_typed_commit_finalization_cut(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
) -> dict[str, object]:
    """Actual Win32 source guest process dies AFTER typed CAS, before intent retire."""
    out = root / "native_typed_before_intent_recovery"
    out.mkdir(parents=True, exist_ok=False)
    user_root = out / "Typed Commit Cut With Spaces"
    user_root.mkdir()
    subprocess.run(
        [str(fixture), str(user_root), str(seed)],
        check=True, capture_output=True, text=True, timeout=timeout)
    profile = user_root / "saves/profile-native-ci-rider"
    raw = profile / "save.srm"
    typed = profile / "host-profile.txt"
    selector = user_root / "host-state-v1.txt"
    catalog = user_root / "profiles-v1.txt"
    pending = profile / "native-sram-checkpoint.pending"
    files = (raw, typed, selector, catalog)
    before = {p: p.read_bytes() for p in files}
    if len(before[raw]) != 8192 or before[raw] != seed.read_bytes():
        raise ValueError("Typed-cut fixture did not start from exact original native SRAM")
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
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
        "UR_BALDOSA_QA_LEGACY_UNJOURNALED_CRASH": "0",
        "UR_BALDOSA_QA_CRASH_AFTER_TYPED_PROFILE_COMMIT": "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(script), str(rom)]
    crashed = subprocess.run(
        command, cwd=out, env=env, capture_output=True, text=True,
        errors="replace", timeout=timeout)
    log = crashed.stdout + "\n" + crashed.stderr
    (out / "crash.log").write_text(log, encoding="utf-8")
    if crashed.returncode != 87 or (
        log.count("UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_TYPED_COMMIT "
                  "exit=87 intent_retained=1") != 1
    ) or log.count("UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1") != 1:
        raise ValueError(
            "Native source did not die AFTER genuine typed CAS: "
            f"rc={crashed.returncode} log_tail={log[-1500:]}")
    if not pending.is_file() or pending.is_symlink():
        raise ValueError("Typed commit cut did not retain original prewrite intent")
    intent_bytes = pending.read_bytes()
    crash = {p: p.read_bytes() for p in files}
    if (crash[raw] == before[raw] or len(crash[raw]) != 8192 or
        crash[typed] == before[typed] or
        any(crash[p] != before[p] for p in (selector, catalog))):
        raise ValueError("Typed cut lacked exact raw+typed new/new state")
    archive_before = list(profile.glob("native-sram-recovered-*.txt"))
    if archive_before:
        raise ValueError("Typed fault finalized or archived intent before process death")
    clean = env.copy()
    clean.pop("UR_BALDOSA_QA_CRASH_AFTER_TYPED_PROFILE_COMMIT", None)
    short = out / "fresh-short.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    recovery_command = [
        str(exe), "--no-launcher", "--config", str(config),
        "--script", str(short), str(rom)]
    first = subprocess.run(
        recovery_command, cwd=out, env=clean, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    first_log = first.stdout + "\n" + first.stderr
    (out / "first-cold-boot.log").write_text(first_log, encoding="utf-8")
    if (first.returncode != 0 or
        first_log.count("UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED "
                        "exact_staged_guest_sram=1 no_records=1") != 1):
        raise ValueError(
            "New/new typed cut did not reconcile original intent once: "
            f"rc={first.returncode}, tail={first_log[-1400:]}")
    verify_named_profile_boot_bytes(first_log, crash[raw])
    after = {p: p.read_bytes() for p in files}
    if any(after[p] != crash[p] for p in files):
        raise ValueError("New/new cold replay fabricated a second typed generation")
    archives = list(profile.glob("native-sram-recovered-*.txt"))
    if len(archives) != 1 or archives[0].read_bytes() != intent_bytes:
        raise ValueError("New/new recovery did not archive exact prewrite intent")
    if pending.exists():
        raise ValueError("Original intent remained after new/new cold replay")
    second = subprocess.run(
        recovery_command, cwd=out, env=clean, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    second_log = second.stdout + "\n" + second.stderr
    (out / "second-cold-boot.log").write_text(second_log, encoding="utf-8")
    if (second.returncode or "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED"
        in second_log):
        raise ValueError("New/new second cold boot repeated typed publication")
    verify_named_profile_boot_bytes(second_log, crash[raw])
    if (any(p.read_bytes() != after[p] for p in files) or
        archives[0].read_bytes() != intent_bytes or pending.exists()):
        raise ValueError("Repeated source-native boot altered typed-cut state")
    if list(user_root.rglob("*.urrun")) or list(user_root.rglob("*.urmatch")):
        raise ValueError("Typed-cut recovery minted source-unearned Records")
    # Bounded disposable CI-owned receipt for independent byte checking.
    names = {
        "raw-sram": raw, "typed-profile": typed,
        "selector": selector, "roster": catalog,
    }
    evidence = out / "fault-bytes"
    evidence.mkdir()
    receipts = {}
    for label, p in names.items():
        # F3: retain independent actual disk bytes after BOTH fresh native
        # cold processes. The archive consumer can compare physical files,
        # not solely trust the source-produced log's recovery count.
        stages = {
            "before": before[p], "crash": crash[p], "after": after[p],
            "second-cold": p.read_bytes(),
        }
        for stage, data in stages.items():
            (evidence / f"{label}.{stage}.bin").write_bytes(data)
        receipts[label] = {stage + "_sha256": hashlib.sha256(data).hexdigest()
                           for stage, data in stages.items()}
    (evidence / "intent.crash.bin").write_bytes(intent_bytes)
    (evidence / "intent.archived.bin").write_bytes(archives[0].read_bytes())
    (evidence / "hashes.json").write_text(
        json.dumps(receipts, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {
        "genuine_original_native_guest": True,
        "typed_commit_before_exit_87": True,
        "intent_retained_at_fault": True,
        "raw_bytes_unchanged_on_recovery": True,
        "typed_generation_not_duplicated": True,
        "exact_intent_archived_once": True,
        "two_cold_boots_idempotent": True,
        "no_invented_records": True,
    }


def run_native_partial_raw_rollback_from_real_win32_cut(
    exe: Path, rom: Path, output: Path, original_root: Path,
    env: dict[str, str], config: Path, intent_bytes: bytes, *,
    timeout: int,
) -> dict[str, object]:
    """Explicit repair on COPY of an actual Win32 post-raw, pending-intent cut.

    Truncation itself is synthetic. This is NOT a tested Windows disk-full or
    ACL failure. The repair and two cold boots use the real native executable.
    """
    isolated = output / "simulated_partial_raw_explicit_rollback"
    isolated.mkdir()
    copied = isolated / "Disposable Interrupted Guest"
    shutil.copytree(original_root, copied, symlinks=True)
    profile = copied / "saves/profile-native-ci-rider"
    raw = profile / "save.srm"
    typed = profile / "host-profile.txt"
    pending = profile / "native-sram-checkpoint.pending"
    selector = copied / "host-state-v1.txt"
    catalog = copied / "profiles-v1.txt"
    before = {p: p.read_bytes() for p in (raw, typed, selector, catalog)}
    if (len(before[raw]) != 8192 or
        not pending.is_file() or pending.read_bytes() != intent_bytes):
        raise ValueError("Synthetic partial-write input lacked authentic Win32 intent")
    # Preserve an exact interrupted prefix from the *real* native writer.
    interrupted = before[raw][:513]
    raw.write_bytes(interrupted)
    copied_env = env.copy()
    copied_env["SNESRECOMP_USER_DATA_DIR"] = str(copied)
    copied_env.pop("UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE", None)
    copied_env.pop("UR_BALDOSA_QA_CRASH_AFTER_TYPED_PROFILE_COMMIT", None)
    script = isolated / "fresh-short.txt"
    script.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    args = [str(exe), "--no-launcher", "--config", str(config),
            "--script", str(script), str(rom)]
    refused = subprocess.run(
        args, cwd=isolated, env=copied_env, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    refused_log = refused.stdout + "\n" + refused.stderr
    (isolated / "cold-refusal.log").write_text(
        refused_log, encoding="utf-8")
    if (refused.returncode != 7 or
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in refused_log or
        raw.read_bytes() != interrupted or
        typed.read_bytes() != before[typed] or
        pending.read_bytes() != intent_bytes):
        raise ValueError("Original guest automatically trusted partial raw SRAM")
    explicit_env = copied_env.copy()
    explicit_env["UR_BALDOSA_RECOVERY_ACTION"] = "typed"
    repaired = subprocess.run(
        args, cwd=isolated, env=explicit_env, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    repair_log = repaired.stdout + "\n" + repaired.stderr
    (isolated / "explicit-typed-recovery.log").write_text(
        repair_log, encoding="utf-8")
    if (repaired.returncode != 89 or
        repair_log.count("UR_BALDOSA_RECOVERY_CHOICE choice=typed ") != 1 or
        "completed=1" not in repair_log or
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in repair_log):
        raise ValueError("Actual native Windows executable refused explicit typed rollback")
    if (raw.read_bytes() == interrupted or
        len(raw.read_bytes()) != 8192 or
        pending.exists() or typed.read_bytes() != before[typed] or
        selector.read_bytes() != before[selector] or
        catalog.read_bytes() != before[catalog]):
        raise ValueError("Explicit typed rollback failed or mutated unrelated authority")
    archives = list(profile.glob("native-sram-manual-archive-*.bin"))
    receipts = list(profile.glob("native-sram-recovered-*.txt"))
    if (len(archives) != 1 or interrupted not in archives[0].read_bytes() or
        len(receipts) != 1 or receipts[0].read_bytes() != intent_bytes):
        raise ValueError("Typed rollback omitted exact interrupted raw/intent archives")
    repaired_raw = raw.read_bytes()
    for index in (1, 2):
        clean = subprocess.run(
            args, cwd=isolated, env=copied_env, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        log = clean.stdout + "\n" + clean.stderr
        (isolated / f"clean-boot-{index}.log").write_text(
            log, encoding="utf-8")
        if (clean.returncode or
            "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in log):
            raise ValueError("Partial-raw rollback repeated or failed on cold boot")
        verify_named_profile_boot_bytes(log, repaired_raw)
        if (raw.read_bytes() != repaired_raw or
            typed.read_bytes() != before[typed] or
            receipts[0].read_bytes() != intent_bytes):
            raise ValueError("Repeated native cold boot mutated committed rollback bytes")
    if list(copied.rglob("*.urrun")) or list(copied.rglob("*.urmatch")):
        raise ValueError("Explicit partial rollback fabricated event records")
    # Expose CI-owned *original bytes* to the independent QA owner, not
    # just source-produced assertions about archived partial data. No ROM,
    # user-owned game state, executable or unbounded private root is copied.
    evidence = isolated / "fault-bytes"
    evidence.mkdir()
    evidence_sources = {
        "raw.original-source-win32.bin": before[raw],
        "raw.synthetic-partial.bin": interrupted,
        "raw.restored.bin": repaired_raw,
        "raw.second-cold.bin": raw.read_bytes(),
        "typed.old.bin": before[typed],
        "typed.restored.bin": typed.read_bytes(),
        "selector.before.bin": before[selector],
        "selector.after.bin": selector.read_bytes(),
        "roster.before.bin": before[catalog],
        "roster.after.bin": catalog.read_bytes(),
        "intent.crash.bin": intent_bytes,
        "intent.archived.bin": receipts[0].read_bytes(),
        "manual-raw-typed-archive.bin": archives[0].read_bytes(),
    }
    hashes = {}
    for label, data in sorted(evidence_sources.items()):
        (evidence / label).write_bytes(data)
        hashes[label] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
    if (len(hashes) != 13 or
        evidence_sources["raw.synthetic-partial.bin"] not in
            evidence_sources["manual-raw-typed-archive.bin"] or
        evidence_sources["intent.crash.bin"] !=
            evidence_sources["intent.archived.bin"] or
        evidence_sources["raw.restored.bin"] !=
            evidence_sources["raw.second-cold.bin"] or
        evidence_sources["typed.old.bin"] !=
            evidence_sources["typed.restored.bin"] or
        evidence_sources["selector.before.bin"] !=
            evidence_sources["selector.after.bin"] or
        evidence_sources["roster.before.bin"] !=
            evidence_sources["roster.after.bin"]):
        raise ValueError("Exact partial-raw recovery byte envelope inconsistent")
    (evidence / "hashes.json").write_text(
        json.dumps(hashes, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    report = {
        "input_real_original_win32_post_raw_cut": True,
        "truncation_is_synthetic_not_real_disk_io": True,
        "interrupted_prefix_bytes": len(interrupted),
        "synthetic_partial_raw_sha256": hashlib.sha256(interrupted).hexdigest(),
        "cold_boot_refused": True,
        "actual_win32_original_exe_explicit_restore_typed": True,
        "archived_original_partial_raw_and_intent": True,
        "two_subsequent_cold_boots_unmodified": True,
        "exact_original_and_preserved_bytes_archived": True,
        "evidence_file_count": len(evidence_sources),
        "release_gate_credit": 0,
    }
    (isolated / "receipt.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    return report


def run_native_win32_postraw_recovery_acl_denial(
    exe: Path, rom: Path, output: Path, source_root: Path,
    environment: dict[str, str], config: Path, intent_bytes: bytes, *,
    timeout: int,
) -> dict[str, object]:
    """Actual Win32 DACL refusal of cold reconciliation after a genuine raw write.

    Copy one source-original F2 post-raw / pretyped crash to a disposable root.
    No synthetic SRAM state or invented progress: the *denial* is genuine NTFS
    access control, but occurs on cold replay, not during the live raw writer.
    """
    isolated = output / "native_postraw_recovery_dacl_denial"
    isolated.mkdir()
    copied = isolated / "Disposable Authentic Interrupted SRAM"
    shutil.copytree(source_root, copied, symlinks=True)
    profile = copied / "saves/profile-native-ci-rider"
    files = {
        "raw-sram": profile / "save.srm",
        "typed-profile": profile / "host-profile.txt",
        "selector": copied / "host-state-v1.txt",
        "roster": copied / "profiles-v1.txt",
    }
    pending = profile / "native-sram-checkpoint.pending"
    before = {name: path.read_bytes() for name, path in files.items()}
    if (len(before["raw-sram"]) != 8192 or
        not pending.is_file() or pending.read_bytes() != intent_bytes or
        not before["typed-profile"] or
        list(copied.rglob("*.urrun")) or
        list(copied.rglob("*.urmatch"))):
        raise ValueError("ACL case missing authentic intact F2 Win32 source cut")
    sid_call = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"], capture_output=True,
        text=True, check=True, timeout=10)
    parsed = list(csv.reader(sid_call.stdout.splitlines()))
    if len(parsed) != 1 or not parsed[0] or not parsed[0][-1].startswith("S-1-5-"):
        raise ValueError("No real Windows SID for post-raw ACL denial")
    sid = parsed[0][-1]
    def acl(*params: str) -> None:
        process = subprocess.run(
            ["icacls", str(profile), *params, "/T"],
            capture_output=True, text=True, timeout=30)
        if process.returncode or "Successfully processed" not in process.stdout:
            raise ValueError("Win32 DACL change failed: " +
                             (process.stdout + process.stderr)[-1000:])
    script = isolated / "short-cold.txt"
    script.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    args = [str(exe), "--no-launcher", "--config", str(config),
            "--script", str(script), str(rom)]
    env = environment.copy()
    env["SNESRECOMP_USER_DATA_DIR"] = str(copied)
    for key in ("UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE",
                "UR_BALDOSA_QA_LEGACY_UNJOURNALED_CRASH",
                "UR_BALDOSA_QA_CRASH_AFTER_INTENT_BEFORE_RAW",
                "UR_BALDOSA_QA_CRASH_AFTER_TYPED_PROFILE_COMMIT",
                "UR_BALDOSA_RECOVERY_ACTION",
                "UR_BALDOSA_RECOVERY_PROFILE_ID"):
        env.pop(key, None)
    denied_applied = False
    denied_bytes = None
    rc = None
    refusal_log = ""
    try:
        acl("/deny", f"*{sid}:(WD,AD,WEA,WA,DE,DC)")
        denied_applied = True
        probe = profile / "_denial_probe_not_a_save.txt"
        try:
            with probe.open("xb") as handle:
                handle.write(b"not a guest save")
        except PermissionError:
            if probe.exists():
                raise ValueError("OS denied create but left unexpected probe file")
        else:
            probe.unlink(missing_ok=True)
            raise ValueError("Actual Win32 post-raw replay folder is still writable")
        attempted = subprocess.run(
            args, cwd=isolated, env=env, capture_output=True, text=True,
            errors="replace", timeout=timeout)
        rc = attempted.returncode
        refusal_log = attempted.stdout + "\n" + attempted.stderr
        (isolated / "cold-os-refusal.log").write_text(
            refusal_log, encoding="utf-8")
        denied_bytes = {name: path.read_bytes() for name, path in files.items()}
    finally:
        if denied_applied:
            acl("/remove:d", f"*{sid}")
    if (rc != 7 or denied_bytes != before or
        "UR_BALDOSA_NATIVE_PROFILE RECOVERY_REJECTED" not in refusal_log or
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in refusal_log or
        not pending.is_file() or pending.read_bytes() != intent_bytes or
        list(profile.glob("native-sram-recovered-*.txt"))):
        raise ValueError("Genuine denied NTFS cold replay changed authentic F2 state")
    result = subprocess.run(
        args, cwd=isolated, env=env, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    recovered_log = result.stdout + "\n" + result.stderr
    (isolated / "recovered-cold.log").write_text(recovered_log, encoding="utf-8")
    if (result.returncode or
        recovered_log.count("UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED "
                            "exact_staged_guest_sram=1 no_records=1") != 1 or
        "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in recovered_log):
        raise ValueError("OS restoration did not permit exact F2 reconciliation")
    verify_named_profile_boot_bytes(recovered_log, before["raw-sram"])
    recovered = {name: path.read_bytes() for name, path in files.items()}
    receipts = list(profile.glob("native-sram-recovered-*.txt"))
    if (recovered["raw-sram"] != before["raw-sram"] or
        recovered["typed-profile"] == before["typed-profile"] or
        (recovered["selector"], recovered["roster"]) !=
        (before["selector"], before["roster"]) or
        pending.exists() or len(receipts) != 1 or
        receipts[0].read_bytes() != intent_bytes):
        raise ValueError("Recovered OS fault did not preserve source-intent bytes")
    verified = subprocess.run(
        args, cwd=isolated, env=env, capture_output=True,
        text=True, errors="replace", timeout=timeout)
    repeated_log = verified.stdout + "\n" + verified.stderr
    (isolated / "second-cold.log").write_text(repeated_log, encoding="utf-8")
    final = {name: path.read_bytes() for name, path in files.items()}
    if (verified.returncode or
        "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in repeated_log or
        final != recovered or pending.exists() or
        receipts[0].read_bytes() != intent_bytes or
        list(copied.rglob("*.urrun")) or list(copied.rglob("*.urmatch"))):
        raise ValueError("Second cold boot failed exact idempotent replay invariant")
    verify_named_profile_boot_bytes(repeated_log, before["raw-sram"])
    evidence = isolated / "fault-bytes"
    evidence.mkdir()
    manifest = {}
    for stage, snapshot in (("before", before), ("denied", denied_bytes),
                            ("recovered", recovered), ("second-cold", final)):
        for name, data in snapshot.items():
            filename = name + "." + stage + ".bin"
            (evidence / filename).write_bytes(data)
            manifest[filename] = {
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            }
    for name, data in (("intent.authentic-F2.bin", intent_bytes),
                       ("intent.immutable-receipt.bin", receipts[0].read_bytes())):
        (evidence / name).write_bytes(data)
        manifest[name] = {"sha256": hashlib.sha256(data).hexdigest(),
                          "bytes": len(data)}
    if len(manifest) != 18:
        raise ValueError("Post-raw OS-denial evidence needs 18 source-byte objects")
    (evidence / "hashes.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return {
        "genuine_original_guest_post_raw_cut_reused_without_byte_edit": True,
        "real_win32_ntfs_acl_create_deny": True,
        "fresh_original_game_refused_before_guest": True,
        "four_canonical_files_unchanged_on_denial": True,
        "prewrite_intent_exact_and_immutable": True,
        "denial_removed_before_healthy_recovery": True,
        "exact_source_guest_sram_reconciled_once": True,
        "second_source_cold_boot_identical": True,
        "source_binary_receipt_members": 18,
        "live_native_postraw_typed_save_denial_proven": False,
        "simulated_disk_full_or_power_cut": False,
        "independent_qa_gate_credit": 0,
    }


def run_native_crash_between_raw_and_typed(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
    snapshot_dir: Path | None = None, journaled: bool = False,
) -> dict[str, object]:
    """Real paused guest, original SRAM writer, exact post-raw _Exit(86).

    Historical unjournaled negative remains reproducible in an isolated
    fixture. The new journaled case must resume the exact staged guest
    bytes in a SECOND genuine native Win32 process without inventing runs.
    """
    output = root / ("native_intent_restart_recovery" if journaled
                     else "native_post_raw_pre_typed_crash")
    output.mkdir(parents=True, exist_ok=False)
    user_root = output / "Crash QA Named Racer With Spaces"
    user_root.mkdir()
    subprocess.run(
        [str(fixture), str(user_root), str(seed)],
        cwd=output, timeout=timeout, capture_output=True, text=True, check=True,
    )
    profile = user_root / "saves/profile-native-ci-rider"
    raw = profile / "save.srm"
    typed = profile / "host-profile.txt"
    selector = user_root / "host-state-v1.txt"
    roster = user_root / "profiles-v1.txt"
    before = {p: p.read_bytes() for p in (raw, typed, selector, roster)}
    if len(before[raw]) != 8192 or before[raw] != seed.read_bytes():
        raise ValueError("Crash witness seed lacks exact authorized SRAM")
    initial = subprocess.run(
        [str(fixture), str(user_root), "native-ci-rider",
         "--verify-native-save"],
        capture_output=True, text=True, timeout=timeout,
    )
    if initial.returncode or "VERIFIED profile=native-ci-rider sram=8192" not in initial.stdout:
        raise ValueError("Crash witness began with an invalid typed/raw profile")

    config = output / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    env = os.environ.copy()
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(user_root),
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
        "UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE": "1",
        "UR_BALDOSA_QA_LEGACY_UNJOURNALED_CRASH": "0" if journaled else "1",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
    })
    crashed = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=output, env=env, capture_output=True, text=True,
        errors="replace", timeout=timeout,
    )
    log = crashed.stdout + "\n" + crashed.stderr
    (output / "crash.log").write_text(log, encoding="utf-8")
    if crashed.returncode != 86:
        raise ValueError(
            "The real native guest did not die exactly between raw SRAM "
            f"and typed CAS: rc={crashed.returncode} tail={log[-1800:]}")
    must_see = (
        "UR_BALDOSA_NATIVE_PAUSE ARMED guest=1952 live_race=1",
        "UR_BALDOSA_NATIVE_PAUSE_MENU QUIT_QUEUED=1 paused=1 guest_steps=0",
        "UR_BALDOSA_NATIVE_PROFILE QA_CRASH_AFTER_RAW_WRITE exit=86 typed_checkpoint=0",
    )
    if any(log.count(marker) != 1 for marker in must_see):
        raise ValueError("The crash was not in a verified paused real guest")
    if ("UR_BALDOSA_NATIVE_PROFILE CHECKPOINT profile=" in log or
        "UR_BALDOSA_NATIVE_PAUSE RELEASED " in log):
        raise ValueError("The faulty run crossed a forbidden typed/simulation boundary")
    verify_named_profile_boot_bytes(log, before[raw])
    for path in (typed, selector, roster):
        if path.read_bytes() != before[path]:
            raise ValueError(f"Crash mutated previously committed Modern metadata: {path}")
    after_raw = raw.read_bytes()
    if len(after_raw) != 8192:
        raise ValueError("Original guest write produced invalid raw SRAM length")
    if after_raw == before[raw]:
        raise ValueError(
            "This real race has no SRAM delta, so it cannot witness "
            "a raw/typed crash mismatch without altering game state")
    if (user_root / "saves/save.srm").exists() or list(user_root.rglob("*.urrun")):
        raise ValueError("Fault injected guest created an unrelated save or result")

    # A new source-backed process either rejects an unjournaled mismatch
    # before frame one or replays ONLY the validated pre-write intent.
    crash_state = {p: p.read_bytes() for p in (raw, typed, selector, roster)}
    pending = profile / "native-sram-checkpoint.pending"
    pending_crash_bytes = pending.read_bytes() if pending.is_file() else None
    if journaled and (pending_crash_bytes is None or
                      len(pending_crash_bytes) < 8192):
        raise ValueError("Durable prewrite intent absent from actual Win32 cut")
    if not journaled and pending_crash_bytes is not None:
        raise ValueError("Historical unjournaled witness unexpectedly had intent")
    real_acl_recovery = None
    if journaled and pending_crash_bytes is not None:
        real_acl_recovery = run_native_win32_postraw_recovery_acl_denial(
            exe, rom, output, user_root, env, config, pending_crash_bytes,
            timeout=timeout)
    partial_raw_rollback = None
    if journaled and pending_crash_bytes is not None:
        partial_raw_rollback = run_native_partial_raw_rollback_from_real_win32_cut(
            exe, rom, output, user_root, env, config, pending_crash_bytes,
            timeout=timeout)
    retry = output / "fresh_launch"
    retry.mkdir()
    short = retry / "no_guest.txt"
    short.write_text("turbo on\nwait 6\nquit\n", encoding="ascii")
    clean_env = env.copy()
    clean_env.pop("UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE", None)
    fresh = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(short), str(rom)],
        cwd=retry, env=clean_env, capture_output=True,
        text=True, errors="replace", timeout=timeout,
    )
    fresh_log = fresh.stdout + "\n" + fresh.stderr
    (output / ("fresh-recovery.log" if journaled else "fresh-rejection.log")
     ).write_text(fresh_log, encoding="utf-8")
    if journaled:
        if (fresh.returncode != 0 or
            fresh_log.count(
                "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED "
                "exact_staged_guest_sram=1 no_records=1") != 1 or
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in fresh_log or
            "UR_BALDOSA_NATIVE_PROFILE REJECTED" in fresh_log):
            raise ValueError(
                "Fresh native guest did not reconcile the exact durable intent: "
                f"rc={fresh.returncode} tail={fresh_log[-1600:]}")
        verify_named_profile_boot_bytes(fresh_log, after_raw)
        confirmed = subprocess.run(
            [str(fixture), str(user_root), "native-ci-rider",
             "--verify-native-save"],
            capture_output=True, text=True, timeout=timeout)
        if confirmed.returncode:
            raise ValueError(
                "Fresh process did not leave canonical typed/raw SRAM equal: "
                f"rc={confirmed.returncode} {confirmed.stdout} {confirmed.stderr}")
        if typed.read_bytes() == before[typed]:
            raise ValueError("Journal replay never committed changed guest bytes")
        receipts = list(profile.glob("native-sram-recovered-*.txt"))
        if len(receipts) != 1 or receipts[0].stat().st_size < 8192:
            raise ValueError("No single retained old/new recovery receipt")
        if selector.read_bytes() != before[selector] or roster.read_bytes() != before[roster]:
            raise ValueError("Intent replay changed a canonical selector or catalog")
        if pending.exists() or receipts[0].read_bytes() != pending_crash_bytes:
            raise ValueError("Recovered receipt does not exactly preserve Win32 intent")
        # Another actual cold guest must consume identical typed/raw bytes,
        # publish no second generation, and leave the same receipt intact.
        repaired_files = {p: p.read_bytes() for p in (raw, typed, selector, roster)}
        repeated = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(short), str(rom)],
            cwd=retry, env=clean_env, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        repeat_log = repeated.stdout + "\n" + repeated.stderr
        (output / "second-cold-recovery-boot.log").write_text(
            repeat_log, encoding="utf-8")
        if (repeated.returncode != 0 or
            "UR_BALDOSA_NATIVE_PROFILE RECOVERY_RECONCILED" in repeat_log):
            raise ValueError("Second cold boot repeated prior journal publication")
        verify_named_profile_boot_bytes(repeat_log, after_raw)
        if any(p.read_bytes() != expected
               for p, expected in repaired_files.items()):
            raise ValueError("Second cold boot changed already recovered raw/typed pair")
        if pending.exists() or receipts[0].read_bytes() != pending_crash_bytes:
            raise ValueError("Second cold boot modified recovery receipt")
    else:
        if (fresh.returncode != 7 or
            fresh_log.count(
                "UR_BALDOSA_NATIVE_PROFILE REJECTED reason="
                "selected_profile_sram_not_initialized") != 1 or
            "UR-STARTUP-SAVE-ROOT: selected Modern profile rejected" not in fresh_log or
            "UR-BALDOSA-SAVE-MISMATCH: Named racer SRAM differs from " not in fresh_log or
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in fresh_log):
            raise ValueError(
                "Fresh native process did not reject *unjournaled* divergence: "
                f"rc={fresh.returncode} tail={fresh_log[-1600:]}")
        for path in (typed, selector, roster):
            if path.read_bytes() != before[path]:
                raise ValueError("Rejected retry modified committed Modern metadata")
        if raw.read_bytes() != after_raw:
            raise ValueError("Unjournaled retry silently overwrote changed raw save")
    if (user_root / "saves/save.srm").exists() or list(user_root.rglob("*.urrun")):
        raise ValueError("Fresh guest invented anonymous save or Records")

    # Optional independent QA capture of ONLY these disposable fixture files.
    # The original test did not archive the raw/typed 8192-byte crash boundary,
    # so its producer report could not independently establish precise bytes.
    # Capture from the before-process in-memory originals and the unchanged
    # after-crash / after-refused-relaunch files, never a personal data root.
    if snapshot_dir is not None:
        snapshot_dir = snapshot_dir.resolve()
        if not snapshot_dir.is_relative_to(output.resolve()):
            raise ValueError("Crash-seam evidence may not escape its disposable test root")
        snapshot_dir.mkdir(parents=True, exist_ok=False)
        labels = {
            "raw-sram": raw,
            "typed-profile": typed,
            "selector": selector,
            "roster": roster,
        }
        file_receipt = {}
        for label, path in labels.items():
            previous, crashed_bytes, current = (
                before[path], crash_state[path], path.read_bytes())
            (snapshot_dir / f"{label}.before.bin").write_bytes(previous)
            (snapshot_dir / f"{label}.crash.bin").write_bytes(crashed_bytes)
            (snapshot_dir / f"{label}.after.bin").write_bytes(current)
            file_receipt[label] = {
                "before_sha256": hashlib.sha256(previous).hexdigest(),
                "crash_sha256": hashlib.sha256(crashed_bytes).hexdigest(),
                "after_sha256": hashlib.sha256(current).hexdigest(),
                "before_bytes": len(previous),
                "crash_bytes": len(crashed_bytes),
                "after_bytes": len(current),
                "crash_changed_byte_count": sum(a != b for a, b in zip(previous, crashed_bytes))
                    + abs(len(previous) - len(crashed_bytes)),
                "changed_byte_count": sum(a != b for a, b in zip(previous, current))
                    + abs(len(previous) - len(current)),
            }
        if (file_receipt["raw-sram"]["before_bytes"] != 8192 or
            file_receipt["raw-sram"]["crash_bytes"] != 8192 or
            file_receipt["raw-sram"]["crash_changed_byte_count"] == 0 or
            any(file_receipt[label]["crash_changed_byte_count"] for label in
                ("typed-profile", "selector", "roster"))):
            raise ValueError("Actual crash-seam bytes violate the P0 raw/typed cut")
        if journaled and (
            file_receipt["typed-profile"]["changed_byte_count"] == 0 or
            any(file_receipt[label]["changed_byte_count"] for label in
                ("selector", "roster"))):
            raise ValueError("Journal replay did not isolate typed update")
        if journaled:
            # Immutable exact journal+receipt bytes qualify independent
            # source-vs-disk comparisons. Never archive a ROM or personal root.
            assert pending_crash_bytes is not None
            recovered_archives = list(profile.glob("native-sram-recovered-*.txt"))
            if len(recovered_archives) != 1:
                raise ValueError("No unique journal receipt after cold replay")
            archived = recovered_archives[0].read_bytes()
            if archived != pending_crash_bytes:
                raise ValueError("Archived journal bytes differ from actual crash")
            (snapshot_dir / "intent.crash.bin").write_bytes(pending_crash_bytes)
            (snapshot_dir / "intent.recovered-receipt.bin").write_bytes(archived)
            intent_receipt = {
                "crash_sha256": hashlib.sha256(pending_crash_bytes).hexdigest(),
                "receipt_sha256": hashlib.sha256(archived).hexdigest(),
                "bytes": len(pending_crash_bytes),
                "byte_identical": True,
                "pending_retired": not pending.exists(),
            }
            (snapshot_dir / "intent-receipt.json").write_text(
                json.dumps(intent_receipt, sort_keys=True, indent=2) + "\n",
                encoding="utf-8")
            (snapshot_dir / "second-cold-recovery-boot.log").write_bytes(
                (output / "second-cold-recovery-boot.log").read_bytes())
            # The QA owner correctly distinguished a source log claiming no
            # repeat publication from separate after-SECOND-boot disk bytes.
            # Export and independently hash each actual canonical file after
            # the second native process. Keep the flat 18-member QA verifier
            # input UNCHANGED; these extra source files live only in the
            # owning original fault-bytes artifact.
            second_receipt = {}
            for label, path in labels.items():
                second_bytes = path.read_bytes()
                expected = repaired_files[path]
                if second_bytes != expected:
                    raise ValueError(
                        "Real second cold Win32 byte export differs: " + label)
                (snapshot_dir / f"{label}.second-cold.bin").write_bytes(
                    second_bytes)
                second_receipt[label] = {
                    "sha256": hashlib.sha256(second_bytes).hexdigest(),
                    "bytes": len(second_bytes),
                    "identical_to_first_recovered": True,
                }
            (snapshot_dir / "second-cold-file-receipt.json").write_text(
                json.dumps(second_receipt, sort_keys=True, indent=2) + "\n",
                encoding="utf-8")
        (snapshot_dir / "crash.log").write_text(log, encoding="utf-8")
        (snapshot_dir / ("cold-recovery.log" if journaled else "cold-refusal.log")
         ).write_text(fresh_log, encoding="utf-8")
        (snapshot_dir / "file-receipt.json").write_text(
            json.dumps(file_receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        if journaled:
            # Machine-readable *producer* export that matches the separate
            # independently owned QA02 read-only verifier. No QA authority
            # moves here: the consumer must separately re-download, pin
            # tested source/PE and independently verify these exact bytes.
            # Retain the ordinary FOUR-label file-receipt EXACTLY. The
            # independent QA02 read-only consumer requires its fifth
            # (intent) receipt as a SEPARATE JSON member, never a fabricated
            # "intent" key added to the four-file canonical manifest.
            # Check this compatibility in the owning Windows workflow
            # against QA's current actual verifier, without QA-gate credit.
            expected = {
                *(f"{name}.{stage}.bin"
                  for name in ("raw-sram", "typed-profile", "selector", "roster")
                  for stage in ("before", "crash", "after")),
                "crash.log", "cold-recovery.log",
                "second-cold-recovery-boot.log", "intent.crash.bin",
                "intent.recovered-receipt.bin", "file-receipt.json",
                "intent-receipt.json",
            }
            assert len(expected) == 19
            qa_zip = output / "qa02-journaled-snapshot.zip"
            with zipfile.ZipFile(qa_zip, "x") as archive:
                for name in sorted(expected):
                    data = (snapshot_dir / name).read_bytes()
                    info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, data)
            with zipfile.ZipFile(qa_zip) as archive:
                if (len(archive.namelist()) != len(expected) or
                    set(archive.namelist()) != expected or
                    archive.testzip() is not None):
                    raise ValueError("Exported flat journaled QA envelope invalid")
            if qa_zip.stat().st_size > 1_000_000:
                raise ValueError("Journaled QA envelope exceeds verifier budget")
            (output / "qa02-journaled-snapshot.sha256").write_text(
                sha256(qa_zip) + "  qa02-journaled-snapshot.zip\n",
                encoding="ascii")

    # Only AFTER the immutable historical failed-boot witness is captured,
    # exercise the explicit recovery choice and a third real source process.
    # The fixture performs the same canonical locked recovery backend; it is
    # never shipped as an implicit startup policy or called by the guest.
    legacy_choice_receipt = None
    if not journaled:
        # The same packaged original native executable now owns player
        # recovery. Refuse any unknown action, without a guest frame or save
        # mutation, before trying the explicit keep-raw choice.
        invalid_env = clean_env.copy()
        invalid_env["UR_BALDOSA_RECOVERY_ACTION"] = "invalid"
        invalid = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config), str(rom)],
            cwd=retry, env=invalid_env, capture_output=True, text=True,
            errors="replace", timeout=timeout)
        if invalid.returncode != 88 or raw.read_bytes() != after_raw or (
            typed.read_bytes() != before[typed]):
            raise ValueError("Unrecognized native recovery action changed save data")
        explicit_env = clean_env.copy()
        explicit_env["UR_BALDOSA_RECOVERY_ACTION"] = "raw"
        choice = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config), str(rom)],
            cwd=retry, env=explicit_env, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        decision_log = choice.stdout + "\n" + choice.stderr
        (output / "explicit-recovery-native-command.log").write_text(
            decision_log, encoding="utf-8")
        if choice.returncode != 89 or (
            decision_log.count("UR_BALDOSA_RECOVERY_CHOICE choice=raw ") != 1
        ) or "completed=1" not in decision_log or (
            "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" in decision_log):
            raise ValueError(
                "Original game did not complete explicit one-shot recovery "
                f"before guest: rc={choice.returncode} tail={decision_log[-1800:]}")
        if raw.read_bytes() != after_raw or typed.read_bytes() == before[typed]:
            raise ValueError("Manual recovery lost raw guest SRAM or failed typed CAS")
        archive = list(profile.glob("native-sram-manual-archive-*.bin"))
        if len(archive) != 1 or len(archive[0].read_bytes()) < 8192:
            raise ValueError("Manual repair did not durably archive both snapshots")
        recovered = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(config),
             "--script", str(short), str(rom)],
            cwd=retry, env=clean_env, capture_output=True,
            text=True, errors="replace", timeout=timeout)
        recovered_log = recovered.stdout + "\n" + recovered.stderr
        (output / "explicit-recovery-fresh-boot.log").write_text(
            recovered_log, encoding="utf-8")
        if recovered.returncode or "UR_BALDOSA_NATIVE_PROFILE BOOT_SRAM" not in recovered_log:
            raise ValueError(
                "Manual choice failed fresh authentic guest restart: "
                f"rc={recovered.returncode} tail={recovered_log[-1600:]}")
        verify_named_profile_boot_bytes(recovered_log, after_raw)
        confirmed = subprocess.run(
            [str(fixture), str(user_root), "native-ci-rider",
             "--verify-native-save"],
            capture_output=True, text=True, timeout=timeout)
        if confirmed.returncode:
            raise ValueError("Post-manual-repair guest left typed/raw divergent")
        if list(user_root.rglob("*.urrun")):
            raise ValueError("Manual repair published a fake Records run")
        legacy_choice_receipt = {
            "explicit": True,
            "same_original_game_binary_recovery": True,
            "unknown_action_no_mutation": True,
            "restarted_native_guest": True,
            "archived_both_snapshots": True,
            "original_guest_raw_unchanged_through_repair": True,
        }

    return {
        "real_native_guest_paused_at_frame": 1952,
        "real_raw_sram_write_completed": True,
        "forced_process_exit_code": 86,
        "typed_profile_and_roster_unchanged": True,
        "raw_and_typed_sram_divergence_reproduced": True,
        "fresh_process_rejected_before_guest": not journaled,
        "validated_intent_reconciled_on_fresh_guest": journaled,
        "synthetic_partial_raw_explicit_rollback": partial_raw_rollback,
        "real_postraw_acl_denied_cold_recovery": real_acl_recovery,
        "second_cold_boot_byte_identical": journaled,
        "actual_crash_intent_and_receipt_retained": journaled and snapshot_dir is not None,
        "qa02_flat_journaled_zip_exported": journaled and snapshot_dir is not None,
        "manual_legacy_raw_choice": legacy_choice_receipt,
        "no_implicit_recovery_or_fake_result": not journaled,
        "cross_file_crash_atomicity_proven": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-frames", type=int, default=2473)
    parser.add_argument("--video", default="windows")
    parser.add_argument("--profile-fixture", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=95)
    args = parser.parse_args()
    exe, rom, script, root, fixture = (p.resolve() for p in
                                       (args.exe, args.rom, args.script,
                                        args.out, args.profile_fixture))
    if not fixture.is_file():
        raise ValueError("Real existing Modern profile codec fixture is mandatory")
    if not exe.is_file() or not script.is_file():
        raise ValueError("Missing real Baldosa executable or supplied original route")
    rom_hash = sha256(rom)
    if rom_hash != USA_SHA256:
        raise ValueError(f"Wrong USA-ROM identity: {rom_hash}")
    if args.expected_frames <= 0:
        raise ValueError("A real positive guest-frame count is mandatory")
    root.mkdir(parents=True, exist_ok=False)
    assert_invalid_mutable_root_fails_closed(
        exe, rom, script, root, video=args.video, timeout=args.timeout)
    original, _ = run_route(exe, rom, script, root, pause=False,
                            video=args.video, timeout=args.timeout)
    candidate, log = run_route(exe, rom, script, root, pause=True,
                               video=args.video, timeout=args.timeout)
    if len(original) != args.expected_frames or len(candidate) != args.expected_frames:
        raise ValueError(f"Route frame count mismatch: original={len(original)} "
                         f"paused={len(candidate)} expected={args.expected_frames}")
    mismatch = next((i for i, (left, right) in enumerate(zip(original, candidate))
                     if left != right), None)
    if mismatch is not None:
        raise ValueError(f"Native guest drift at frame {mismatch + 1}: "
                         f"{original[mismatch]} vs {candidate[mismatch]}")
    proof = check_pause_log(log)
    delayed, delayed_log = run_route(
        exe, rom, script, root, pause=True, delayed_restart=True,
        video=args.video, timeout=args.timeout)
    if len(delayed) != args.expected_frames:
        raise ValueError(f"Delayed Restart route frames={len(delayed)} expected={args.expected_frames}")
    delayed_proof = check_delayed_restart_log(delayed_log, expected_request_frame=1952)
    host_trace_proof = check_delayed_restart_host_trace(
        (root / "baseline/log.txt").read_text(encoding="utf-8"),
        delayed_log)
    sram_seed = (root / "baseline/Modern Player Data With Spaces"
                 / "saves/save.srm")
    named_crc, named_log = run_route(
        exe, rom, script, root, pause=False, video=args.video,
        timeout=args.timeout, profile_fixture=fixture,
        profile_seed=sram_seed)
    named_frames = check_named_profile_guest_terminal(
        named_crc, named_log, clean_frames=args.expected_frames)
    named_proof = verify_named_profile_boot(named_log, sram_seed)
    fresh_process_proof = run_existing_named_profile_fresh_process(
        exe, rom, script, root, video=args.video, timeout=args.timeout,
        clean_frames=args.expected_frames, fixture=fixture)
    conflict_proof = run_native_pause_quit_selector_conflict(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    pause_quit_proof = run_native_pause_quit(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    post_raw_crash_proof = run_native_crash_between_raw_and_typed(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout,
        snapshot_dir=root / "native_post_raw_pre_typed_crash/fault-bytes")
    journal_recovery_proof = run_native_crash_between_raw_and_typed(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout, journaled=True,
        snapshot_dir=root / "native_intent_restart_recovery/fault-bytes")
    prewrite_cut_proof = run_native_prewrite_intent_abandon(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    typed_cut_proof = run_native_typed_commit_finalization_cut(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    three_profile_proof = run_native_three_profile_unrelated_damage(
        exe, rom, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    dual_game_proof = run_native_two_original_windows_games(
        exe, rom, script, root, fixture, sram_seed,
        timeout=args.timeout)
    # The source guest's *real* raw SRAM write is complete and OS path
    # leases remain held while an independent host applies an actual NTFS
    # deny. The original native typed CAS must fail; cold replay follows.
    from baldosa_win32_live_postraw_sharing_denial import (
        run_native_win32_live_postraw_typed_denial,
    )
    actual_live_postraw_os_denial = run_native_win32_live_postraw_typed_denial(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    real_dacl_prewrite_proof = run_native_real_win32_prewrite_directory_denial(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    journaled_b_a_proof = run_native_journaled_b_crash_then_a_isolation(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    real_b_crash_healthy_a_proof = run_native_real_crashed_second_healthy_first(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    healthy_alternate_proof = run_native_healthy_alternate_from_damaged_source(
        exe, rom, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    two_profiles_proof = run_second_named_profile_isolation(
        exe, rom, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    assert_corrupt_named_profile_rejected(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    root_p1_proof = run_native_modern_root_smoke(
        exe, rom, root, video=args.video, timeout=args.timeout, players=1)
    root_p2_proof = run_native_modern_root_smoke(
        exe, rom, root, video=args.video, timeout=args.timeout, players=2)
    named_records_proof = run_native_named_records_root(
        exe, rom, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    reentry_proof = run_native_modern_root_reentry(
        exe, rom, root, video=args.video, timeout=args.timeout)
    race_p1_proof = run_native_modern_race_entry(
        exe, rom, root, players=1, video=args.video, timeout=args.timeout)
    race_p2_proof = run_native_modern_race_entry(
        exe, rom, root, players=2, video=args.video, timeout=args.timeout)
    result = {
        "modern_root_source_menu_reentry": reentry_proof,
        "native_modern_paused_quit": pause_quit_proof,
        "native_post_raw_pre_typed_crash": post_raw_crash_proof,
        "native_journaled_post_raw_recovery": journal_recovery_proof,
        "native_typed_commit_before_intent_retirement": typed_cut_proof,
        "native_prewrite_intent_abandoned_without_raw_commit": prewrite_cut_proof,
        "native_healthy_alternate_after_damaged_p1": healthy_alternate_proof,
        "native_real_b_crash_healthy_a_recovery": real_b_crash_healthy_a_proof,
        "native_journaled_b_recovery_then_explicit_a": journaled_b_a_proof,
        "native_actual_win32_ntfs_directory_prewrite_denial": real_dacl_prewrite_proof,
        "native_actual_win32_live_postraw_typed_denial": actual_live_postraw_os_denial,
        "native_two_overlapping_original_games": dual_game_proof,
        "native_three_registered_unrelated_damaged_c": three_profile_proof,
        "native_paused_quit_selector_conflict": conflict_proof,
        "modern_root_race_entry_p1": race_p1_proof,
        "modern_root_race_entry_p2": race_p2_proof,
        "native_modern_root_p1": root_p1_proof,
        "native_modern_root_p2": root_p2_proof,
        "native_named_readonly_records": named_records_proof,
        "classification": "windows_native_pause_and_named_profile_smoke_only",
        "rom_sha256": rom_hash,
        "exe_sha256": sha256(exe),
        "script_sha256": sha256(script),
        "video_driver": args.video,
        "guest_frames": len(original),
        "per_frame_wram_crc_identical": True,
        "native_pause": proof,
        "modern_lifecycle_abi_exercised": True,
        "native_modern_user_data_root_isolation": True,
        "native_real_named_modern_profile_boot": named_proof,
        "native_existing_modern_profile_fresh_process": fresh_process_proof,
        "native_two_named_profile_isolation": two_profiles_proof,
        "native_corrupt_selected_profile_fails_closed": True,
        "native_invalid_explicit_root_fails_closed": True,
        "physical_sdl_event_pump_exercised": True,
        "native_same_boundary_restart_restored": True,
        "native_delayed_guest_restart_restored": True,
        "native_delayed_restart": delayed_proof,
        "native_delayed_host_frame_wram_evidence": host_trace_proof,
        "native_guest_indexed_dump_note": (
            "guest snapshot frame filenames can be overwritten by a real rewind; "
            "proof uses append-only host frame + full WRAM instead"
        ),
        "native_multi_frame_replay_restart_proven": False,
        "physical_keyboard_hardware_tested": False,
        "physical_gamepad_hardware_tested": False,
        "course_complete_credit": 0,
        "modern_frontend_connected": False,
        "packaged_windows_product": False,
    }
    (root / "report.json").write_text(json.dumps(result, indent=2) + "\n",
                                       encoding="utf-8")
    print(f"PASS: Win32 Baldosa native execution, {len(original)} per-frame WRAM CRCs; "
          "same-frame native pause CRC identical; delayed SDL R rewinds actual guest while frozen; "
          "named Modern SRAM boot and same-profile second-process boot preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
