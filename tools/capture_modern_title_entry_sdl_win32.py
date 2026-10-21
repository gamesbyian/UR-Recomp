#!/usr/bin/env python3
"""Source-bound REAL Windows SDL Modern title entry/exit, no synthetic renderer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

try:
    from tools.qa_modern_visual_pam_png import convert
except ModuleNotFoundError:
    from qa_modern_visual_pam_png import convert

USA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa97bd6ed478"
STAGES = (("entry", 16, False), ("settled", 40, False),
          ("leaving", 64, False), ("root", 100, False),
          ("reduced-early", 16, True), ("reduced-late", 40, True))
HEADER = re.compile(rb"\AP7\nWIDTH (\d+)\nHEIGHT (\d+)\nDEPTH 4\n"
                    rb"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n")
SAVED = re.compile(r"^UR_MODERN_VISUAL_SDL_CAPTURE status=saved draw=(\d+) "
                   r"guest_frame=(\d+) output=(\d+)x(\d+) "
                   r"source=SDL_RenderReadPixels\b", re.MULTILINE)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_p7(path, size):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing/redirected SDL P7")
    raw = path.read_bytes()
    m = HEADER.match(raw)
    if not m or tuple(map(int, m.groups())) != size:
        raise ValueError("Wrong SDL P7 header/size")
    if len(raw) != m.end() + size[0] * size[1] * 4:
        raise ValueError("SDL P7 pixel length mismatch")
    return raw[m.end():]


def rgb_differences(a, b, w, h, region="full"):
    if len(a) != w * h * 4 or len(b) != len(a):
        raise ValueError("Wrong pixel buffer length")
    if region == "logo":
        x0, x1, y0, y1 = w // 16, w * 15 // 16, h // 8, h // 2
    elif region == "prompt":
        x0, x1, y0, y1 = 0, w, h * 4 // 5, h
    elif region == "full":
        x0, x1, y0, y1 = 0, w, 0, h
    else:
        raise ValueError("Invalid title region")
    return sum(a[i:i + 3] != b[i:i + 3]
               for y in range(y0, y1)
               for x in range(x0, x1)
               for i in ((y * w + x) * 4,))


def verify_frames(frames, size):
    if set(frames) != {name for name, _, _ in STAGES}:
        raise ValueError("Missing SDL motion stage")
    w, h = size
    for name, frame in frames.items():
        if len(frame) != w * h * 4:
            raise ValueError("Bad SDL byte count: " + name)
        if not any(frame[i] or frame[i + 1] or frame[i + 2]
                   for i in range(0, len(frame), 4)):
            raise ValueError("Blank native SDL: " + name)
    changes = {
        "enter_logo": rgb_differences(frames["entry"], frames["settled"], w, h, "logo"),
        "leave_logo": rgb_differences(frames["settled"], frames["leaving"], w, h, "logo"),
        "leave_prompt": rgb_differences(frames["settled"], frames["leaving"], w, h, "prompt"),
        "enter_root": rgb_differences(frames["leaving"], frames["root"], w, h),
        "reduced_still": rgb_differences(frames["reduced-early"], frames["reduced-late"], w, h),
    }
    if not changes["enter_logo"] or changes["leave_logo"] or not changes["leave_prompt"] or not changes["enter_root"] or changes["reduced_still"]:
        raise ValueError("SDL title motion/guard evidence failed: " + str(changes))
    return changes


def run(exe, rom, out, aspect, source_sha, timeout=90):
    if (aspect not in ("wide", "4:3") or not re.fullmatch(r"[0-9a-f]{40}", source_sha)
            or not 30 <= timeout <= 120 or not exe.is_file() or exe.is_symlink()
            or exe.read_bytes()[:2] != b"MZ"
            or not rom.is_file() or rom.is_symlink() or sha(rom) != USA
            or out.exists() or out.is_symlink()):
        raise ValueError("Unqualified title SDL inputs")
    size = (1280, 720) if aspect == "wide" else (1024, 768)
    out.mkdir(parents=True, exist_ok=False)
    frames = {}
    records = []
    for name, draw, reduced in STAGES:
        stage = out / name
        stage.mkdir()
        (stage / "fresh-user").mkdir()
        config = stage / "config.ini"
        config.write_text(f"[Graphics]\nWindowSize = {size[0]}x{size[1]}\n[Sound]\nEnableAudio = 0\n", encoding="ascii")
        script = stage / "guest.script"
        script.write_text("wait 130\nquit\n", encoding="ascii")  # deliberately no turbo
        p7 = stage / "sdl.pam"
        env = dict(os.environ)
        env.update({
            "SDL_VIDEODRIVER": "windows", "SDL_AUDIODRIVER": "dummy",
            "SNESRECOMP_USER_DATA_DIR": str(stage / "fresh-user"),
            "UR_EXECUTION_MODE": "modern", "UR_BALDOSA_MODERN_ROOT": "1",
            "UR_BALDOSA_MODERN_INPUT": "1",
            "UR_BALDOSA_MODERN_PROFILE_SELECT": "1",
            "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "15",
            "UR_REDUCED_MOTION": "1" if reduced else "0",
            "UR_MODERN_VISUAL_SDL_CAPTURE_DRAW": str(draw),
            "UR_MODERN_VISUAL_SDL_CAPTURE_FILE": str(p7),
            "UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_WIDTH": str(size[0]),
            "UR_MODERN_VISUAL_SDL_CAPTURE_EXPECT_HEIGHT": str(size[1]),
        })
        result = subprocess.run([str(exe), "--no-launcher", "--config", str(config),
                                 "--script", str(script), str(rom)],
                                cwd=stage, env=env, timeout=timeout,
                                capture_output=True, text=True, errors="replace")
        log = result.stdout + "\n" + result.stderr
        logfile = stage / "native-process.log"
        logfile.write_bytes(log.encode("utf-8"))
        match = list(SAVED.finditer(log))
        if (result.returncode or len(match) != 1
                or "UR_MODERN_VISUAL_SDL_CAPTURE refused=" in log
                or "[snes_load] name=UNIRACERS" not in log
                or "UR_BALDOSA_MODERN_ROOT opened=1" not in log
                or f"UR_BALDOSA_MODERN_TITLE painted=1 raster={342 if aspect == 'wide' else 256}x224" not in log):
            raise ValueError("Missing original-game native SDL title witness: " + name)
        if tuple(map(int, match[0].groups())) != (draw, draw, *size):
            raise ValueError("SDL/guest frame or drawable drift: " + name)
        frames[name] = read_p7(p7, size)
        png = stage / "sdl.png"
        convert(p7, png, expected_size=size)
        records.append({
            "stage": name, "sdl_draw": draw, "guest_frame": draw,
            "reduced_motion": reduced,
            "raw_p7_sha256": sha(p7), "png_sha256": sha(png),
            "native_log_sha256": sha(logfile)
        })
    changes = verify_frames(frames, size)
    receipt = {
        "schema_version": 1, "source_head": source_sha,
        "native_windows_executable_sha256": sha(exe),
        "canonical_usa_rom_sha256": USA, "aspect": aspect,
        "actual_sdl_drawable": list(size), "stages": records,
        "native_final_sdl_motion_rgb_differences": changes,
        "native_semantic_p1_button_not_physical": True,
        "original_guest_modified": False, "authentic_mode_modified": False,
        "human_art_approved": False, "hardware_approved": False,
        "release_gate_credit": 0,
    }
    (out / "native-title-sdl-motion-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--aspect", choices=("wide", "4:3"), default="wide")
    p.add_argument("--source-sha", required=True)
    p.add_argument("--timeout", type=int, default=90)
    args = p.parse_args()
    print(json.dumps(run(args.exe, args.rom, args.out, args.aspect,
                         args.source_sha, args.timeout), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
