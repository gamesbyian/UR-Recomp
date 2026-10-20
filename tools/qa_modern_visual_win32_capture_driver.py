#!/usr/bin/env python3
"""Run one real native Win32 Modern root SDL screenshot, source-bound and ROM-free on export.

On the bounded Windows QA runner: launch exact prepared Baldosa PE and personal
canonical ROM with a disposable clean save root, record full process log,
actual SDL readback/P7 and lossless PNG, and emit an explicitly *unapproved*
receipt. No physical controller or human approval. Do not archive the ROM or
private save root in GitHub Actions. Supports only the real SDL2 drawable probe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from qa_modern_visual_pam_png import convert
from baldosa_windows_native_pause_route import USA_SHA256

READBACK = re.compile(
    r"UR_MODERN_VISUAL_SDL_CAPTURE (?:status=saved draw=\d+ guest_frame=\d+ output="
    r"|refused=output-size draw=\d+ observed=)([0-9]+)x([0-9]+)")
EXPECTED_SOURCE = re.compile(r"^[0-9a-f]{40}$")
MAX_DIM = (3840, 2160)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def launch(exe: Path, rom: Path, root: Path, name: str,
           expected: tuple[int, int], video: str, timeout: int) -> dict:
    stage = root / name
    stage.mkdir(parents=True, exist_ok=False)
    home = stage / "Fresh Modern Screenshot State"
    home.mkdir()
    config = stage / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="ascii")
    script = stage / "stock-guest.route"
    script.write_text("turbo on\nwait 480\nquit\n", encoding="ascii")
    capture = stage / "actual-sdl-drawable.pam"
    env = dict(os.environ)
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(home),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "14",
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
        "UR_MODERN_VISUAL_SDL_CAPTURE_DRAW": "40",
        "UR_MODERN_VISUAL_SDL_CAPTURE_FILE": str(capture),
        "UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_WIDTH": str(expected[0]),
        "UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_HEIGHT": str(expected[1]),
    })
    p = subprocess.run(
        [str(exe), "--no-launcher", "--config", str(config),
         "--script", str(script), str(rom)],
        cwd=stage, env=env, capture_output=True, text=True, errors="replace",
        timeout=timeout)
    log = p.stdout + "\n" + p.stderr
    (stage / "native-process.log").write_text(log, encoding="utf-8")
    if p.returncode:
        raise RuntimeError(
            f"genuine Windows game exited {p.returncode} ({name})\n" +
            log[-2400:])
    matches = READBACK.findall(log)
    if len(matches) != 1:
        raise RuntimeError("No unambiguous actual SDL readback size in " + name +
                           "\n" + log[-2800:])
    found = tuple(int(x) for x in matches[0])
    if not all(320 <= found[0] <= MAX_DIM[0] and 224 <= found[1] <= MAX_DIM[1]
               for _ in (0,)):
        raise RuntimeError("Unqualified SDL drawable geometry: " + str(found))
    if "UR_BALDOSA_MODERN_ROOT opened=1" not in log:
        raise RuntimeError("Actual native Modern root not observed")
    return {
        "stage": stage,
        "log": log,
        "capture": capture,
        "expected": expected,
        "observed": found,
        "readback_saved": (
            f"output={found[0]}x{found[1]} source=SDL_RenderReadPixels" in log
            and capture.is_file()),
    }


def run(exe: Path, rom: Path, out: Path, source_sha: str, video: str,
        timeout: int) -> dict:
    if (not EXPECTED_SOURCE.fullmatch(source_sha) or
            not exe.is_file() or exe.is_symlink() or
            not rom.is_file() or rom.is_symlink() or
            sha256(rom) != USA_SHA256):
        raise ValueError("Missing native executable, exact USA ROM or source SHA")
    if out.exists() or out.is_symlink():
        raise ValueError("Output directory already exists")
    out.mkdir(parents=True)
    first = launch(exe, rom, out, "probe_first", (1280, 720), video, timeout)
    selected = first
    # The default SDL drawable need not be 1280x720. Record its *actual* size
    # and make a second genuine fresh-state native process only if needed.
    if not first["readback_saved"]:
        selected = launch(exe, rom, out, "capture_observed",
                          first["observed"], video, timeout)
    if not selected["readback_saved"] or selected["observed"] != selected["expected"]:
        raise RuntimeError("Exact-size real SDL drawable not captured")
    raw = selected["capture"]
    png = out / "actual-sdl-drawable.png"
    conversion = convert(raw, png, selected["observed"])
    receipt = {
        "schema_version": 1,
        "scope": "one real Windows Modern *baseline* root, not four-agent visual integration",
        "source_sha": source_sha,
        "exe_sha256": sha256(exe),
        "native_process_exit": 0,
        "actual_sdl_renderer_output": list(selected["observed"]),
        "observed_in_draw": 40,
        "SDL_driver": video,
        "native_process_log_sha256": sha256(selected["stage"] / "native-process.log"),
        "p7_sha256": sha256(raw),
        "png_sha256": sha256(png),
        "conversion": conversion,
        "source_bound_by_independent_rebuild": False,
        "controller": "scripted semantic host path, no physical joystick",
        "visual_approved": False,
        "hardware_approved": False,
        "authentic_isolation_approved": False,
        "release_gate_credit": 0,
    }
    (out / "readback-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    # Do not archive raw user state or ROM, only bounded diagnostic bytes/log.
    for stage in (out / "probe_first", out / "capture_observed"):
        if stage.exists():
            (stage / "Fresh Modern Screenshot State").rename(
                stage / "save-root-DO-NOT-ARCHIVE")
    return receipt


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--video", default="windows")
    p.add_argument("--timeout", type=int, default=95)
    args = p.parse_args()
    try:
        result = run(args.exe, args.rom, args.out, args.source_sha,
                     args.video, args.timeout)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("UR_MODERN_NATIVE_VISUAL_CAPTURE_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
