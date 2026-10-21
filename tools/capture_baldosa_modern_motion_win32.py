#!/usr/bin/env python3
"""One REAL pinned Windows PE native Modern root motion compositor experiment.

Uses the already compiled Baldosa/UR game, original USA retail ROM and the
production Modern root host (not a mock, no new emulator or game renderer).
The root is reached through the genuine frozen-guest menu; no controller
events, user files, guest memory or save writes are injected by this tool.

Deliberately measures only P6 native root compositor paints. This does not
certify post-SDL P7, natural frame cadence, controller hardware, 4K, hero art
or full release acceptance. Never upload ROM, PE, SRAM or source sprite art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_modern_menu_motion_capture import verify_log

USA_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
EXPECTED_CAPTURE_ENV = {
    "UR_EXECUTION_MODE": "modern",
    "UR_BALDOSA_MODERN_ROOT": "1",
    "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "0",
    "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
    "UR_BALDOSA_MODERN_INPUT": "1",
    "UR_BALDOSA_PAUSE_SMOKE": "0",
    "UR_REDUCED_MOTION": "0",
    "UR_MODERN_MENU_TEST_TICK60": "0",
    "UR_MODERN_MENU_TEST_ADVANCE_PER_PRESENT": "1",
    "SDL_VIDEODRIVER": "dummy",
    "SDL_AUDIODRIVER": "dummy",
}
FRAMES = 840  # source root admitted by guest main mode D7, before idle attract


def validate_paths(exe: Path, rom: Path, out: Path) -> tuple[str, str]:
    if os.name != "nt":
        raise ValueError("real native Modern motion capture requires Windows")
    for p in (exe, rom):
        if p.is_symlink() or not p.is_file():
            raise ValueError("missing or redirected original Windows native input")
    exe_bytes = exe.read_bytes()
    if (len(exe_bytes) <= 65536 or exe_bytes[:2] != b"MZ" or
        exe.suffix.lower() != ".exe"):
        raise ValueError("not an actual native Windows x64 executable")
    pe = struct.unpack_from("<I", exe_bytes, 0x3C)[0]
    if pe > len(exe_bytes) - 26 or exe_bytes[pe:pe + 4] != b"PE\x00\x00":
        raise ValueError("original game has invalid PE source signature")
    if (struct.unpack_from("<H", exe_bytes, pe + 4)[0] != 0x8664 or
        struct.unpack_from("<H", exe_bytes, pe + 24)[0] != 0x20B):
        raise ValueError("original game is not native Windows x64 PE32+")
    rom_hash = hashlib.sha256(rom.read_bytes()).hexdigest()
    if rom_hash != USA_SHA256:
        raise ValueError("canonical retail USA ROM hash mismatch")
    if out.exists():
        raise ValueError("motion output directory must not pre-exist")
    return hashlib.sha256(exe_bytes).hexdigest(), rom_hash


def run_native(exe: Path, rom: Path, out: Path, *,
               timeout: int = 120, video: str = "dummy") -> dict:
    if not 30 <= timeout <= 150:
        raise ValueError("native motion process timeout must be 30..150 seconds")
    if video != "dummy":
        raise ValueError("this bounded test uses dummy SDL display only")
    exe = exe.resolve(strict=True)
    rom = rom.resolve(strict=True)
    out = out.resolve()
    exe_hash, rom_hash = validate_paths(exe, rom, out)
    out.mkdir(parents=True)
    user = out / "fresh-test-user"
    user.mkdir()
    config = out / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    route = out / "source-idle-root.script"
    # 840 genuine, ordinarily paced guest frames; do not turbo/skip the
    # 440-frame source-menu admission or accidentally cross idle attract.
    route.write_text(f"wait {FRAMES}\nquit\n", encoding="ascii")
    env = {**os.environ, **EXPECTED_CAPTURE_ENV,
           "SNESRECOMP_USER_DATA_DIR": str(user)}
    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(route), str(rom)]
    proc = subprocess.run(command, cwd=out, env=env, timeout=timeout,
                          text=True, capture_output=True, errors="replace")
    log = proc.stdout + "\n" + proc.stderr
    (out / "native-game.log").write_text(log, encoding="utf-8")
    if proc.returncode:
        raise ValueError(f"native game process exited {proc.returncode}: "
                         f"{log[-1500:]}")
    if log.count("UR_BALDOSA_MODERN_ROOT opened=1") != 1:
        raise ValueError("source-admitted native root did not open exactly once")
    if "UR_BALDOSA_MODERN_ROOT selected=" in log:
        raise ValueError("motion capture unexpectedly injected native navigation")
    receipt = verify_log(log, min_frames=40)
    if receipt["session_count"] != 1:
        raise ValueError("captured unexpected native root re-entry")
    session = receipt["sessions"][0]
    if (session["logical_width"], session["logical_height"],
        session["root_x"], session["root_width"]) != (256, 224, 8, 240):
        raise ValueError("native compact source root geometry is not qualified")
    if session["reduced_motion_frames"]:
        raise ValueError("default native root unexpectedly enabled reduced motion")
    receipt["source_commit"] = os.environ.get("GITHUB_SHA")
    receipt["exe_sha256"] = exe_hash
    receipt["rom_sha256"] = rom_hash
    receipt["source_guest_script_frames"] = FRAMES
    receipt["video_driver"] = video
    receipt["host_original_mode_admitted"] = True
    receipt["real_windows_game_process"] = True
    receipt["test_clock_per_native_root_draw"] = True
    receipt["not_proven"].extend([
        "SDL P7 final-screen motion", "input-driven cursor navigation",
        "true Modern 342-wide root", "frame-to-swap pacing",
    ])
    report = out / "motion-native-draw-receipt.json"
    report.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    report = run_native(args.exe, args.rom, args.out, timeout=args.timeout)
    print("ACTUAL_WIN32_NATIVE_ROOT_MOTION_P6_OK")
    print("exe_sha256=" + report["exe_sha256"])
    print("native_root_draws=" + str(report["native_draw_count"]))
    print("source_60hz_model=passed")
    print("sdl_p7_or_human_approval=not_proven")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
