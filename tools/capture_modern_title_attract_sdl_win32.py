#!/usr/bin/env python3
"""Native first-original-attract full-title/demo and safe wake: final SDL evidence.

Only the same exact original Win32 AOT game and already-installed SDL3
readback observer may generate pixels. No second renderer, extracted asset,
fabricated controller, changed guest data, or default-attract activation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

try:
    from tools.capture_modern_title_entry_sdl_win32 import (
        USA, HEADER, SAVED, read_p7, rgb_differences)
    from tools.probe_baldosa_modern_title_attract_win32 import verify_source_driven_preview
    from tools.qa_modern_visual_pam_png import convert
except ModuleNotFoundError:
    from capture_modern_title_entry_sdl_win32 import (
        USA, HEADER, SAVED, read_p7, rgb_differences)
    from probe_baldosa_modern_title_attract_win32 import verify_source_driven_preview
    from qa_modern_visual_pam_png import convert

# The original guest owns frames at 943/1532; native host owns explicit
# wake frame1600 and new confirm frame1660. These are observed source
# events, not title art invented at a guessed host timeout.
STAGES = (
    ("original-title", 1000, "original"),
    ("original-demo", 1584, "original"),
    ("woken-modern", 1616, "modern"),
    ("confirmed-root", 1696, "root"),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_original_source_p6(path: Path) -> dict:
    """Exact guest/host P6 preceding SDL, never retroactively synthesized."""
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing genuine original-source pre-SDL witness")
    b = path.read_bytes()
    m = re.match(rb"\AP6\n(\d+) (\d+)\n255\n", b)
    if not m:
        raise ValueError("Malformed original guest P6 header")
    w, h = map(int, m.groups())
    if not (w in (256, 342) and h == 224) or len(b) != m.end() + w*h*3:
        raise ValueError("Original P6 raster/length mismatch")
    pixels = memoryview(b)[m.end():]
    count = sum(any(pixels[i:i+3]) for i in range(0, len(pixels), 3))
    return {"source_raster": [w,h], "nonblack_rgb_pixels": count,
            "sha256": digest(path)}


def verify_actual_attract_frames(frames: dict[str, bytes],
                                 drawable: tuple[int, int]) -> dict:
    if set(frames) != {name for name, _, _ in STAGES}:
        raise ValueError("Missing genuine original attract or wake SDL stage")
    w, h = drawable
    for name, raw in frames.items():
        if len(raw) != w * h * 4:
            raise ValueError("Malformed SDL pixel buffer in " + name)
        if not any(raw[i] or raw[i + 1] or raw[i + 2]
                   for i in range(0, len(raw), 4)):
            raise ValueError("Blank native window in " + name)
    diffs = {}
    for a, b in zip(STAGES, STAGES[1:]):
        key = a[0] + "_to_" + b[0]
        changed = rgb_differences(frames[a[0]], frames[b[0]], w, h)
        if changed == 0:
            raise ValueError("Native original/Modern SDL journey never changed: " + key)
        diffs[key] = changed
    return diffs


def run(exe: Path, rom: Path, out: Path, aspect: str,
        source_sha: str, timeout: int = 110,
        diagnose_title_only: bool = False) -> dict:
    if aspect not in ("wide", "4:3"):
        raise ValueError("Invalid original SDL aspect")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("Invalid exact native source head")
    if not 45 <= timeout <= 150:
        raise ValueError("Invalid original SDL capture timeout")
    if not exe.is_file() or exe.is_symlink():
        raise ValueError("Missing/redirected Windows AOT game")
    with exe.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("Original stock game not Windows PE")
    if not rom.is_file() or rom.is_symlink() or len(USA) != 64 or digest(rom) != USA:
        raise ValueError("Original USA retail ROM digest/identity mismatch")
    if out.exists() or out.is_symlink():
        raise ValueError("Native original-attract evidence directory already exists")
    drawable = (1280, 720) if aspect == "wide" else (1024, 768)
    out.mkdir(parents=True, exist_ok=False)
    frames = {}
    evidence = []
    stages_to_run = STAGES[:1] if diagnose_title_only else STAGES
    source_title_diagnostic = None
    for name, draw, expected_mode in stages_to_run:
        stage = out / name
        stage.mkdir()
        user = stage / "throwaway-test-user"
        user.mkdir()
        cfg = stage / "config.ini"
        cfg.write_text(
            f"[Graphics]\nWindowSize = {drawable[0]}x{drawable[1]}\n"
            "[Sound]\nEnableAudio = 0\n", encoding="ascii")
        script = stage / "guest.script"
        # No turbo: SDL draw identity must be observed at the real host.
        script.write_text("wait 1770\nquit\n", encoding="ascii")
        raw_file = stage / "native-sdl.pam"
        env = dict(os.environ)
        env.update({
            "SDL_VIDEODRIVER": "windows",
            "SDL_AUDIODRIVER": "dummy",
            "SNESRECOMP_USER_DATA_DIR": str(user),
            "UR_EXECUTION_MODE": "modern",
            "UR_BALDOSA_MODERN_ROOT": "1",
            "UR_BALDOSA_MODERN_INPUT": "1",
            "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
            "UR_BALDOSA_MODERN_TITLE_ATTRACT_PROBE": "1",
            "UR_MODERN_TITLE_STOCK_ATTRACT_PREVIEW": "1",
            "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "19",
            "UR_REDUCED_MOTION": "0",
            "UR_MODERN_VISUAL_SDL_CAPTURE_DRAW": str(draw),
            "UR_MODERN_VISUAL_SDL_CAPTURE_FILE": str(raw_file),
            "UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_WIDTH": str(drawable[0]),
            "UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_HEIGHT": str(drawable[1]),
        })
        if name == "original-title":
            # Genuine guest renderer after original PPU/OSD, before SDL3 upload.
            env["SNESRECOMP_SCREENSHOT"] = str(stage / "original-presdl.ppm")
            env["SNESRECOMP_SCREENSHOT_FRAME"] = str(draw)
        proc = subprocess.run(
            [str(exe), "--no-launcher", "--config", str(cfg),
             "--script", str(script), str(rom)],
            cwd=stage, env=env, timeout=timeout,
            capture_output=True, text=True, errors="replace")
        log = proc.stdout + "\n" + proc.stderr
        log_path = stage / "native-process.log"
        log_path.write_bytes(log.encode("utf-8"))
        if proc.returncode:
            raise ValueError("Native original-attract game exited unsuccessfully: " + name)
        original_source_events = verify_source_driven_preview(log, "p1")
        matches = list(SAVED.finditer(log))
        if len(matches) != 1 or "UR_MODERN_VISUAL_SDL_CAPTURE refused=" in log:
            raise ValueError("Missing/unqualified real final SDL readback: " + name)
        if tuple(map(int, matches[0].groups())) != (draw, draw, *drawable):
            raise ValueError("Genuine original SDL draw/guest clock or geometry drift: " + name)
        if ("UR_BALDOSA_MODERN_ROOT opened=1" not in log or
                "UR_MODERN_TITLE_STOCK_ATTRACT source_revealed=1 frame=943" not in log or
                "UR_MODERN_TITLE_STOCK_ATTRACT restored_title=1 frame=1600" not in log or
                "UR_BALDOSA_MODERN_TITLE entered_root=1 frame=1674" not in log):
            raise ValueError("Genuine original demo and native Modern wake were not observed")
        frames[name] = read_p7(raw_file, drawable)
        if name == "original-title":
            p6 = read_original_source_p6(stage / "original-presdl.ppm")
            rgb = frames[name]
            sdl_nonblack = sum(bool(rgb[i] or rgb[i+1] or rgb[i+2])
                               for i in range(0, len(rgb), 4))
            source_title_diagnostic = {
                "guest_frame": draw,
                "original_rendered_before_sdl": p6,
                "actual_sdl_rgb_nonblack_pixels": sdl_nonblack,
                "actual_sdl_pixel_buffer_sha256": hashlib.sha256(rgb).hexdigest(),
                "original_title_visible_in_source": p6["nonblack_rgb_pixels"] > 0,
                "original_title_visible_in_sdl": sdl_nonblack > 0,
                "source_versus_final_sdl_parity_proven": False,
                "diagnostic_only": True, "release_gate_credit": 0,
            }
            (stage / "original-title-source-vs-sdl.json").write_text(
                json.dumps(source_title_diagnostic, indent=2) + "\n", encoding="utf-8")
        png = stage / "native-sdl.png"
        convert(raw_file, png, expected_size=drawable)
        evidence.append({
            "stage": name, "actual_sdl_draw": draw,
            "observed_guest_frame": draw, "expected_mode": expected_mode,
            "sdl_raw_p7_sha256": digest(raw_file),
            "lossless_png_sha256": digest(png),
            "original_native_process_log_sha256": digest(log_path),
            "actual_original_source_events": original_source_events,
        })
    if diagnose_title_only:
        if source_title_diagnostic is None:
            raise ValueError("No original-title diagnostic witness")
        receipt = {
            "schema_version": 1, "source_head": source_sha,
            "actual_native_windows_executable_sha256": digest(exe),
            "original_usa_rom_sha256": USA,
            "drawable": list(drawable),
            "source_guest_original_title_vs_sdl": source_title_diagnostic,
            "art_and_hardware_approved": False,
            "title_full_attract_sdl_accepted": False,
            "release_gate_credit": 0,
        }
        (out / "original-title-diagnostic-only.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return receipt
    diffs = verify_actual_attract_frames(frames, drawable)
    receipt = {
        "schema_version": 1,
        "exact_native_source_sha": source_sha,
        "one_actual_windows_aot_pe_sha256": digest(exe),
        "canonical_original_usa_rom_sha256": USA,
        "actual_native_sdl_output": list(drawable),
        "requested_aspect": aspect,
        "real_original_guest_and_controller_source_stage_log": evidence,
        "observed_original_native_sdl_rgb_transitions": diffs,
        "uses_original_game_renderer": True,
        "real_original_demo_guest_writes_by_test": False,
        "default_stock_attract_enabled": False,
        "test_only_native_semantic_P1_wake_confirm": True,
        "source_authenticity_independently_approved": False,
        "physical_gamepad_or_monitor_verified": False,
        "human_visual_approval": False,
        "release_gate_credit": 0
    }
    (out / "real-stock-title-demo-wake-sdl-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--aspect", choices=("wide", "4:3"), default="wide")
    p.add_argument("--timeout", type=int, default=110)
    p.add_argument("--diagnose-title-only", action="store_true",
                   help="Only one original-source P6 versus final SDL draw, no acceptance verdict")
    args = p.parse_args()
    result = run(args.exe, args.rom, args.out, args.aspect,
                 args.source_sha, args.timeout, args.diagnose_title_only)
    print("UR_MODERN_ORIGINAL_TITLE_P6_P7_DIAGNOSTIC=collected" if args.diagnose_title_only
          else "UR_MODERN_ORIGINAL_ATTRACT_REAL_SDL=passed")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
