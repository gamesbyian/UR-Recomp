#!/usr/bin/env python3
"""Independent Authentic-mode no-op proof for Modern title hooks.

Runs the SAME pinned Windows AOT image twice with the genuine Baldosa
script and ROM, toggling only UR_BALDOSA_MODERN_ROOT while forcing
UR_EXECUTION_MODE=authentic. Verifies original WRAM CRC timeline, original
256-wide host-presented raster, and absence of Modern title/root UI ink.
This is not a reference-SNES oracle or physical-display certification.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from capture_baldosa_modern_title_win32 import read_present_ppm, EXPECTED_USA_ROM

CRC = re.compile(r'"crc32_wram":\s*"(0x[0-9a-fA-F]+)"')


def source_wram_crcs(folder: Path) -> list[str]:
    files = sorted(folder.glob("frame_*.json"))
    if len(files) < 100:
        raise ValueError("Authentic source frame run produced fewer than 100 actual frames")
    result = []
    for index, path in enumerate(files):
        if path.name != f"frame_{index:06d}.json":
            raise ValueError("Unexpected missing/duplicate/renumbered source frame")
        match = CRC.search(path.read_text(encoding="utf-8"))
        if match is None:
            raise ValueError(f"Frame {index} has no original WRAM CRC")
        result.append(match.group(1).lower())
    return result


def authentic_presents(folder: Path) -> dict[int, bytes]:
    table = folder / "presents.csv"
    if not table.is_file():
        raise ValueError("Original Authentic host emitted no presentation CSV")
    with table.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["present", "frame", "alpha", "crc32", "luma"]:
            raise ValueError("Authentic presentation manifest schema drift")
        rows = list(reader)
    if not 2 <= len(rows) <= 30:
        raise ValueError("Authentic did not present a bounded guest timeline")
    pairs = {}
    for index, row in enumerate(rows):
        if int(row["present"]) != index:
            raise ValueError("Authentic present indices skipped/reordered")
        frame = int(row["frame"])
        _, _, rgb = read_present_ppm(folder / f"present_{index:06d}.ppm", 256)
        if frame in pairs and pairs[frame] != rgb:
            raise ValueError("Same-frame Authentic host output changed unexpectedly")
        pairs[frame] = rgb
    return pairs


def authentic_ink_visible(rgb: bytes) -> bool:
    """Reject early black/uniform host images as original-picture evidence.

    Samples ORIGINAL host RGB pixels, with no fabricated/overlaid replacement.
    A real source title/race frame must contain at least five RGB triplets
    and at least 1% nonblack pixels to distinguish from a blank clear.
    """
    if len(rgb) != 256 * 224 * 3:
        return False
    palette = set()
    painted = 0
    for start in range(0, len(rgb), 3):
        color = rgb[start:start + 3]
        if color != b"\x00\x00\x00":
            painted += 1
        if len(palette) < 5:
            palette.add(color)
    return len(palette) >= 5 and painted >= (256 * 224) // 100


def check_inert(source: dict, enabled: dict) -> dict:
    for label, run in (("original", source), ("title-enabled", enabled)):
        if "UR_BALDOSA_MODERN_TITLE painted=1" in run["log"] or (
            "UR_BALDOSA_MODERN_ROOT opened=1" in run["log"]
        ):
            raise ValueError(f"{label}: Modern frontend activated inside Authentic")
    if source["crc"] != enabled["crc"]:
        raise ValueError("Modern title root toggle changed the original WRAM CRC timeline")
    common = sorted(set(source["frames"]) & set(enabled["frames"]))
    if len(common) < 3:
        raise ValueError("Fewer than three common actual Authentic host presents")
    for frame in common:
        if source["frames"][frame] != enabled["frames"][frame]:
            raise ValueError(f"Modern title toggled Authentic displayed pixels at frame {frame}")
    # Early Authentic guest startup can yield genuine all-black frames.
    # Those prove timeline parity but say nothing about eventual visible
    # original title/game output. Require a *late* native source-rendered
    # image with materially varied ink from the very same matched frames.
    visible = [frame for frame in common if frame >= 224 and
               authentic_ink_visible(source["frames"][frame])]
    if not visible:
        raise ValueError(
            "Authentic original host output remained blank/uniform after "
            "frame 224; do not credit identical black captures")
    digest = hashlib.sha256("".join(source["crc"]).encode("ascii")).hexdigest()
    return {
        "original_frames": len(source["crc"]),
        "common_present_frames": common,
        "visible_original_guest_present_frames": visible,
        "source_wram_crc_timeline_sha256": digest,
        "identical_host_presented_pixels": True,
        "modern_title_or_root_present": False,
        "authentic_output_raster": "256x224",
    }


def run_once(exe: Path, rom: Path, script: Path, target: Path,
             root_enabled: bool, timeout: int) -> dict:
    target.mkdir(parents=True, exist_ok=False)
    dump = target / "framedump"
    shots = target / "presented"
    data = target / "userdata"
    for p in (dump, shots, data):
        p.mkdir()
    config = target / "config.ini"
    config.write_text(
        "[Sound]\nEnableAudio = 0\n[Graphics]\nWindowSize = 960x720\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_USER_DATA_DIR": str(data),
        "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
        "SNESRECOMP_SCREENSHOT_DIR": str(shots),
        "SNESRECOMP_SCREENSHOT_FROM": "0",
        "SNESRECOMP_SCREENSHOT_TO": "320",
        "UR_EXECUTION_MODE": "authentic",
        "UR_BALDOSA_MODERN_ROOT": "1" if root_enabled else "0",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
    })
    cmd = [str(exe), "--no-launcher", "--config", str(config),
           "--script", str(script), "--framedump", str(dump), str(rom)]
    result = subprocess.run(cmd, cwd=target, env=env,
                            timeout=timeout, capture_output=True,
                            text=True, errors="replace")
    log = result.stdout + "\n" + result.stderr
    (target / "original-host.log").write_text(log, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Authentic source process returned {result.returncode}: {log[-1500:]}")
    return {"log": log, "crc": source_wram_crcs(dump),
            "frames": authentic_presents(shots)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=100)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Native Authentic AOT verification requires real Windows")
    exe, rom, script = (
        path.resolve(strict=True) for path in (args.exe, args.rom, args.script))
    if hashlib.sha256(rom.read_bytes()).hexdigest() != EXPECTED_USA_ROM:
        raise ValueError("Authentic control must use the original pinned USA ROM")
    if not exe.read_bytes().startswith(b"MZ"):
        raise ValueError("Authentic control requires the actual Windows PE")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    reference = run_once(exe, rom, script, out / "authentic-root-disabled",
                         False, args.timeout)
    variant = run_once(exe, rom, script, out / "authentic-root-enabled",
                       True, args.timeout)
    receipt = check_inert(reference, variant)
    receipt.update({"executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
                    "original_rom_sha256": EXPECTED_USA_ROM,
                    "release_gate_credit": 0})
    (out / "authentic-title-inert-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("UR_MODERN_TITLE_AUTHENTIC_INERT=passed")
    print(json.dumps({k: v for k, v in receipt.items()
                      if k != "common_present_frames"}, sort_keys=True))
    # Keep the actual source logs and receipt, not hundreds of RAM/screenshot
    # frames; exact feature toggles have been checked with their original bytes.
    for target in (out / "authentic-root-disabled", out / "authentic-root-enabled"):
        import shutil
        shutil.rmtree(target / "framedump")
        shutil.rmtree(target / "presented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
