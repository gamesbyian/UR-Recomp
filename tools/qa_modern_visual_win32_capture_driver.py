#!/usr/bin/env python3
"""Run one real native Win32 Modern root SDL screenshot, source-bound and ROM-free on export.

On the bounded Windows QA runner: launch exact prepared Baldosa PE and personal
canonical ROM with a disposable clean save root, record full process log,
actual SDL readback/P7 and lossless PNG, and emit an explicitly *unapproved*
receipt. No physical controller or human approval. Do not archive the ROM or
private save root in GitHub Actions. Uses actual SDL3/SDL2 renderer output, never a source framebuffer or resized image.
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

try:
    from tools.qa_modern_visual_pam_png import convert
    from tools.baldosa_windows_native_pause_route import USA_SHA256
except ModuleNotFoundError:  # direct python tools/... command
    from qa_modern_visual_pam_png import convert
    from baldosa_windows_native_pause_route import USA_SHA256

READBACK = re.compile(
    r"UR_MODERN_VISUAL_SDL_CAPTURE (?:status=saved draw=\d+ guest_frame=\d+ output="
    r"|refused=output-size draw=\d+ observed=)([0-9]+)x([0-9]+)")
EXPECTED_SOURCE = re.compile(r"^[0-9a-f]{40}$")
MAX_DIM = (3840, 2160)
# Exact in-repo test-only native semantic routes, never synthetic guest writes.
# Draw ordinal is a paced REAL SDL EndDraw count, not a simulation index.
ROUTES = {
    "root-quit": ("14", 40, ""),
    "records-keyboard": ("1", 64, "UR_BALDOSA_MODERN_ROOT records_opened=1"),
    "options-p1": ("12", 74, "UR_BALDOSA_MODERN_ROOT options_opened"),
    "profile-first-p1": ("8", 66, "UR_BALDOSA_MODERN_ROOT first_racer_opened=1"),
    "authentic-stock": ("0", 40, ""),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def launch(exe: Path, rom: Path, root: Path, name: str,
           expected: tuple[int, int], video: str, timeout: int,
           window_size: tuple[int, int] | None = None,
           route: str = "root-quit") -> dict:
    stage = root / name
    stage.mkdir(parents=True, exist_ok=False)
    home = stage / "Fresh Modern Screenshot State"
    home.mkdir()
    config = stage / "config.ini"
    size_config = (f"[Graphics]\nWindowSize = {window_size[0]}x{window_size[1]}\n"
                   if window_size is not None else "")
    config.write_text(size_config + "[Sound]\nEnableAudio = 0\n", encoding="ascii")
    script = stage / "stock-guest.route"
    # Capture host PRESENT 40, not guest frame 40. Turbo can simulate 62
    # guest frames in ~60ms while SDL draws only three frames, making that
    # ordinal unreachable. Use the normal native 60Hz presentation clock.
    script.write_text("wait 480\nquit\n", encoding="ascii")
    capture = stage / "actual-sdl-drawable.pam"
    smoke, capture_draw, stage_marker = ROUTES[route]
    execution_mode = "authentic" if route == "authentic-stock" else "modern"
    env = dict(os.environ)
    env.update({
        "SNESRECOMP_USER_DATA_DIR": str(home),
        "UR_EXECUTION_MODE": execution_mode,
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_INPUT": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": smoke,
        "SDL_VIDEODRIVER": video,
        "SDL_AUDIODRIVER": "dummy",
        "UR_MODERN_VISUAL_SDL_CAPTURE_DRAW": str(capture_draw),
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
    if not (320 <= found[0] <= MAX_DIM[0] and
            224 <= found[1] <= MAX_DIM[1]):
        raise RuntimeError("Unqualified SDL drawable geometry: " + str(found))
    root_opened = "UR_BALDOSA_MODERN_ROOT opened=1" in log
    if execution_mode == "authentic":
        if root_opened or "UR_BALDOSA_MODERN_ROOT painted=1" in log:
            raise RuntimeError("Modern frontend leaked into Authentic execution")
        if "[snes_load]" not in log:
            raise RuntimeError("Authentic guest ROM load was not observed")
    elif not root_opened:
        raise RuntimeError("Actual native Modern root not observed")
    if stage_marker and stage_marker not in log:
        raise RuntimeError("Requested real native destination route not observed: " + route)
    return {
        "stage": stage,
        "log": log,
        "capture": capture,
        "expected": expected,
        "route": route,
        "execution_mode": execution_mode,
        "capture_draw": capture_draw,
        "observed": found,
        "readback_saved": (
            f"output={found[0]}x{found[1]} source=SDL_RenderReadPixels" in log
            and capture.is_file()),
    }


def run(exe: Path, rom: Path, out: Path, source_sha: str, video: str,
        timeout: int, window_size: tuple[int, int] | None = None,
        route: str = "root-quit") -> dict:
    if (not EXPECTED_SOURCE.fullmatch(source_sha) or
            not exe.is_file() or exe.is_symlink() or
            not rom.is_file() or rom.is_symlink() or
            sha256(rom) != USA_SHA256):
        raise ValueError("Missing native executable, exact USA ROM or source SHA")
    # Validate caller geometry before creating any evidence root. An invalid
    # cohort may never leave a directory that a later exact-size run mistakes
    # for a prior native screenshot, including on unattended retry.
    if window_size is not None and (
            len(window_size) != 2 or
            not (320 <= window_size[0] <= MAX_DIM[0] and
                 224 <= window_size[1] <= MAX_DIM[1])):
        raise ValueError("Unsafe exact native Win32 output request")
    if route not in ROUTES:
        raise ValueError("Unknown native semantic route")
    if out.exists() or out.is_symlink():
        raise ValueError("Output directory already exists")
    out.mkdir(parents=True)
    if window_size is not None:
        first = launch(exe, rom, out, "probe_first", window_size, video, timeout,
                       window_size=window_size, route=route)
        # Never silently downgrade an explicit 16:9/4:3 Windows request to
        # the host's default 640x480 and then label it as a requested capture.
        if not first["readback_saved"]:
            raise RuntimeError("Exact requested SDL drawable was not observed: " +
                               str(window_size) + " actual=" + str(first["observed"]))
        selected = first
    else:
        first = launch(exe, rom, out, "probe_first", (1280, 720), video, timeout,
                       route=route)
        selected = first
        # Default drawable can differ; this is ONLY automatic baseline mode.
        if not first["readback_saved"]:
            selected = launch(exe, rom, out, "capture_observed",
                              first["observed"], video, timeout, route=route)
    if not selected["readback_saved"] or selected["observed"] != selected["expected"]:
        raise RuntimeError("Exact-size real SDL drawable not captured")
    raw = selected["capture"]
    png = out / "actual-sdl-drawable.png"
    conversion = convert(raw, png, selected["observed"])
    receipt = {
        "schema_version": 1,
        "scope": "one real Windows native display baseline/control, not four-agent visual integration",
        "source_sha": source_sha,
        "exe_sha256": sha256(exe),
        "native_process_exit": 0,
        "actual_sdl_renderer_output": list(selected["observed"]),
        "observed_in_draw": selected["capture_draw"],
        "native_semantic_route": route,
        "execution_mode": selected["execution_mode"],
        "native_route_marker_observed": bool(ROUTES[route][2]),

        "requested_window_size": list(window_size) if window_size else None,
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
    # Upload workflow lists fixed receipts, PNG/P7 and logs only. Per-process
    # private user root and copyrighted ROM never belong in the artifact.
    return receipt


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--video", default="windows")
    p.add_argument("--route", choices=tuple(ROUTES), default="root-quit",
                   help="Exact existing native semantic input journey")
    p.add_argument("--window-size",
                   help="Exact native WindowSize WxH; no fallback, no rescaling")
    p.add_argument("--timeout", type=int, default=95)
    args = p.parse_args()
    try:
        window = None
        if args.window_size is not None:
            if not re.fullmatch(r"[0-9]{3,4}x[0-9]{3,4}", args.window_size):
                raise ValueError("Invalid explicit WidthxHeight size")
            window = tuple(map(int, args.window_size.split("x")))
        result = run(args.exe, args.rom, args.out, args.source_sha,
                     args.video, args.timeout, window_size=window,
                     route=args.route)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print("UR_MODERN_NATIVE_VISUAL_CAPTURE_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
