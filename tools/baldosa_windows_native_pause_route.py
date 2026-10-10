#!/usr/bin/env python3
"""Run the *existing* pinned Baldosa 2P route in isolated native Windows dirs.

No substitute guest driver or new input grammar: this launches the actual
UniracersSNESRecomp executable with Baldosa's original --script/--framedump
arguments. Two clean processes differ only by the opt-in 24-event-pump host
pause/resume witness. Neither touches the user's profile/save root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

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
    if profile_id not in ("native-ci-rider", "native-ci-second"):
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
            "UR_BALDOSA_MODERN_ROOT route=3 unavailable=1",
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


def run_native_pause_quit_selector_conflict(
    exe: Path, rom: Path, script: Path, root: Path,
    fixture: Path, seed: Path, *, video: str, timeout: int,
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
            gate.write_text("writer-B-committed\n", encoding="ascii")
            process.wait(timeout=timeout)
        except BaseException:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=timeout)
            raise

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
    reentry_proof = run_native_modern_root_reentry(
        exe, rom, root, video=args.video, timeout=args.timeout)
    race_p1_proof = run_native_modern_race_entry(
        exe, rom, root, players=1, video=args.video, timeout=args.timeout)
    race_p2_proof = run_native_modern_race_entry(
        exe, rom, root, players=2, video=args.video, timeout=args.timeout)
    result = {
        "modern_root_source_menu_reentry": reentry_proof,
        "native_modern_paused_quit": pause_quit_proof,
        "native_paused_quit_selector_conflict": conflict_proof,
        "modern_root_race_entry_p1": race_p1_proof,
        "modern_root_race_entry_p2": race_p2_proof,
        "native_modern_root_p1": root_p1_proof,
        "native_modern_root_p2": root_p2_proof,
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
