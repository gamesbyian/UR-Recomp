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
        if (user_root / "saves/save.srm").exists():
            raise RuntimeError(f"{name}: named guest wrote unrelated default-profile SRAM")
        if not (user_root / "saves/profile-native-ci-rider/save.srm").is_file():
            raise RuntimeError(f"{name}: named guest did not preserve selected-profile SRAM")
    elif not (user_root / "saves/save.srm").is_file():
        raise RuntimeError(f"{name}: real guest SRAM not saved under Modern user root")
    if any((output / "saves").iterdir()):
        raise RuntimeError(f"{name}: guest created package/cwd-local saves")
    return frame_crcs(framedump), log


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


def verify_named_profile_boot(log: str, seed: Path) -> dict[str, str]:
    # The title's stock before_run_frame callback fires AFTER RtlReadSram
    # but before the first actual RtlRunFrame. Compare the entire 8192 bytes
    # using an independent hash of the real previous native guest's SRAM.
    proof = PROFILE_BOOT_SRAM.findall(log)
    if len(proof) != 1:
        raise ValueError("No unique first-frame named Modern guest SRAM witness")
    if "UR_BALDOSA_NATIVE_PROFILE APPLIED profile=native-ci-rider root=" not in log:
        raise ValueError("No acknowledged native active-profile root selection")
    raw = seed.read_bytes()
    if len(raw) != 8192 or proof[0].lower() != fnv32(raw):
        raise ValueError("Native guest did not load exactly the selected profile's SRAM")
    return {"bytes": len(raw), "fnv32": proof[0].lower()}


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
    assert_corrupt_named_profile_rejected(
        exe, rom, script, root, fixture, sram_seed,
        video=args.video, timeout=args.timeout)
    result = {
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
          "real named Modern profile SRAM loaded before first guest frame")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
