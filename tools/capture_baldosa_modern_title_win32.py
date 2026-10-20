#!/usr/bin/env python3
"""Bounded genuine Win32 native Modern title -> root source-pixel acceptance.

Run against the existing pinned Baldosa Windows AOT candidate. No synthetic
screenshots, no guest writes, no independent renderer or release certification.
An actual SDL drawable still needs #2041 independent capture/inspection.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import re
import subprocess

EXPECTED_USA_ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
EXPECTED_RETAIL_BGR_FNV = 0xD998C3B6CC123D5F
K_FNV_BASIS = 1469598103934665603
K_FNV_PRIME = 1099511628211
PPM_HEADER = re.compile(rb"\AP6\n(\d+) (\d+)\n255\n")
PAM_HEADER = re.compile(
    rb"\AP7\nWIDTH (\d+)\nHEIGHT (\d+)\nDEPTH 4\n"
    rb"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
)


def read_pam(path: Path, expected_width: int = 342) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    header = PAM_HEADER.match(data)
    if not header:
        raise ValueError(f"{path}: not an actual P7 RGBA native source capture")
    width, height = (int(x) for x in header.groups())
    payload = data[header.end():]
    if width != expected_width or height != 224 or len(payload) != 4 * width * height:
        raise ValueError(f"{path}: incorrect original-source raster geometry")
    return width, height, payload


def read_present_ppm(path: Path) -> tuple[int, int, bytes]:
    raw = path.read_bytes()
    match = PPM_HEADER.match(raw)
    if match is None:
        raise ValueError(f"{path}: not a host P6 presented screenshot")
    w, h = (int(x) for x in match.groups())
    payload = raw[match.end():]
    if w != 342 or h != 224 or len(payload) != w * h * 3:
        raise ValueError(f"{path}: invalid host-presented raster dimensions")
    return w, h, payload


def _pixel_match(reference: bytes, output: bytes,
                 width: int, bounds: tuple[int, int, int, int]) -> float:
    x0, y0, rw, rh = bounds
    if min(x0, y0, rw, rh) < 0 or x0 + rw > width or y0 + rh > 224:
        raise ValueError("comparison bounds outside host frame")
    matched = 0
    for y in range(y0, y0 + rh):
        for x in range(x0, x0 + rw):
            src = (y * width + x) * 4
            dst = (y * width + x) * 3
            matched += (
                reference[src:src+3] == output[dst:dst+3])
    return matched / (rw * rh)


def verify_native_presented_frames(present_dir: Path, source_dir: Path) -> dict:
    """Require both title and root to reach the real host's present path.

    SNESRecomp's WritePpm is AFTER RtlDrawPpuFrame/ComposeOsd and BEFORE
    SDL texture upload, not a GPU backbuffer read. The guest-frame receipt
    and exact-host executable identity are separately checked elsewhere.
    """
    table = present_dir / "presents.csv"
    if not table.is_file():
        raise ValueError("missing native present-frame CSV")
    with table.open(newline="", encoding="utf-8") as inp:
        reader = csv.DictReader(inp)
        if reader.fieldnames != ["present", "frame", "alpha", "crc32", "luma"]:
            raise ValueError("native present CSV schema changed")
        records = list(reader)
    if not records or len(records) > 30:
        raise ValueError("unexpected native presentation count")
    photos = []
    for row in records:
        index = int(row["present"])
        frame = int(row["frame"])
        if index != len(photos) or frame < 0 or frame > 180:
            raise ValueError("native presentation indices/clock invalid")
        if len(row["crc32"]) != 8:
            raise ValueError("missing native presented CRC")
        file = present_dir / f"present_{index:06d}.ppm"
        width, height, rgb = read_present_ppm(file)
        photos.append((frame, rgb, file))
    matches = {}
    for stage, bounds in (
        ("title", ((342 - 238) // 2, 27, 238, 81)),
        ("root", (61, 17, 218, 142)),
    ):
        _, _, source = read_pam(source_dir /
                               f"modern-native-{stage}-342x224.pam")
        best = max(
            (( _pixel_match(source, rgb, 342, bounds), frame, file)
             for frame, rgb, file in photos),
            key=lambda result: result[0])
        ratio, frame, file = best
        if ratio < 0.995:
            raise ValueError(
                f"{stage} never reached native host-presented pixels; "
                f"best matching fraction {ratio:.6f}")
        keep = present_dir / f"presented-{stage}.ppm"
        keep.write_bytes(file.read_bytes())
        matches[stage] = {
            "present_frame": frame,
            "source_match_fraction": round(ratio, 6),
            "file": keep.name,
            "sha256": hashlib.sha256(keep.read_bytes()).hexdigest(),
        }
    if matches["title"]["present_frame"] >= matches["root"]["present_frame"]:
        raise ValueError("host-presented root precedes title")
    # Retain just the actual two host-presented matches and indexed CSV.
    for _, _, f in photos:
        f.unlink()
    return {"presentations_examined": len(photos), "matched": matches}


def fnv_pixels(pixels: bytes) -> int:
    hash_ = K_FNV_BASIS
    for component in pixels:
        hash_ = ((hash_ ^ component) * K_FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return hash_


def retail_art_digest(width: int, rgba: bytes) -> int:
    # The source title painter installs the verified 238x81 retail asset at
    # y=27, centre x=(logical_width-238)//2, without touching pixels later.
    offset = (width - 238) // 2
    bgr = bytearray()
    for y in range(27, 108):
        for x in range(offset, offset + 238):
            i = (y * width + x) * 4
            bgr.extend((rgba[i + 2], rgba[i + 1], rgba[i]))
    return fnv_pixels(bgr)


def validate_native_capture(folder: Path, log: str, *, exe_sha256: str) -> dict:
    witness = (
        "UR_BALDOSA_MODERN_ROOT opened=1",
        "UR_BALDOSA_MODERN_TITLE native_p1_start=1 frame=60",
        "UR_BALDOSA_MODERN_TITLE entered_root=1",
        "UR_BALDOSA_MODERN_ROOT painted=1",
    )
    prev = -1
    for marker in witness:
        pos = log.find(marker, prev + 1)
        if pos < 0:
            raise ValueError(f"missing/out-of-order genuine native guest witness: {marker}")
        prev = pos
    output = {"executable_sha256": exe_sha256, "captures": []}
    for stage in ("title", "root"):
        name = f"modern-native-{stage}-342x224.pam"
        file = folder / name
        w, h, rgba = read_pam(file)
        if len(set(rgba)) < 3:
            raise ValueError(f"{name}: implausibly uniform native image")
        stamp = re.search(
            r"UR_BALDOSA_MODERN_TITLE native_capture=1 stage=" +
            stage + r" guest_frame=(\d+) raster=(\d+)x(\d+) "
            r"rgba_fnv1a64=([0-9a-f]{16}) path=([^\n]+)", log)
        if not stamp:
            raise ValueError(f"{name}: missing source frame and digest witness")
        frame, sw, sh, claimed, path = stamp.groups()
        if (int(sw), int(sh)) != (w, h):
            raise ValueError(f"{name}: native log dimensions conflict with PAM")
        if int(claimed, 16) != fnv_pixels(rgba):
            raise ValueError(f"{name}: source pixels disagree with logged digest")
        if Path(path.strip()).resolve() != file.resolve():
            raise ValueError(f"{name}: capture path does not belong to output")
        output["captures"].append({
            "name": name, "stage": stage, "guest_frame": int(frame),
            "width": w, "height": h,
            "rgba_fnv1a64": claimed, "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
        })
        if stage == "title" and retail_art_digest(w, rgba) != EXPECTED_RETAIL_BGR_FNV:
            raise ValueError("native title crop differs from verified original USA retail pixels")
    if output["captures"][0]["guest_frame"] >= output["captures"][1]["guest_frame"]:
        raise ValueError("title/root pixel frames not independently source-ordered")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=100)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("real Windows AOT title capture requires Windows runner")
    if not 30 <= args.timeout <= 120:
        parser.error("timeout must be 30..120s")
    exe, rom, script = (p.resolve(strict=True) for p in
                        (args.exe, args.rom, args.script))
    if hashlib.sha256(rom.read_bytes()).hexdigest() != EXPECTED_USA_ROM:
        raise ValueError("original retail ROM hash mismatch")
    image = exe.read_bytes()
    if image[:2] != b"MZ":
        raise ValueError("not native Windows PE executable")
    target = args.out.resolve()
    target.mkdir(parents=True, exist_ok=False)
    captures = target / "captures"
    captures.mkdir()
    presented = target / "presented"
    presented.mkdir()
    user = target / "player"
    user.mkdir()
    (target / "saves").mkdir()
    framedump = target / "framedump"
    framedump.mkdir()
    config = target / "config.ini"
    config.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    environment = dict(os.environ)
    environment.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "15",
        "UR_BALDOSA_MODERN_TITLE_CAPTURE_DIR": str(captures),
        "SNESRECOMP_SCREENSHOT_DIR": str(presented),
        "SNESRECOMP_SCREENSHOT_FROM": "0",
        "SNESRECOMP_SCREENSHOT_TO": "180",
        "SNESRECOMP_FRAMEDUMP_PIXELS": "0",
        "SNESRECOMP_DUMP_DIR": str(target / "saves"),
    })
    command = [str(exe), "--no-launcher", "--config", str(config),
               "--script", str(script), "--framedump", str(framedump), str(rom)]
    try:
        result = subprocess.run(command, cwd=target, env=environment,
                                capture_output=True, text=True,
                                timeout=args.timeout, errors="replace")
        log = result.stdout + "\n" + result.stderr
        (target / "native-title-run.log").write_text(log, encoding="utf-8")
    except subprocess.TimeoutExpired as e:
        (target / "native-title-timeout.txt").write_text(str(e))
        raise
    if result.returncode != 0:
        raise RuntimeError(f"native title process exit {result.returncode}: {log[-2400:]}")
    exe_hash = hashlib.sha256(image).hexdigest()
    receipt = validate_native_capture(captures, log, exe_sha256=exe_hash)
    receipt["native_presented"] = verify_native_presented_frames(presented, captures)
    import json
    (target / "native-title-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("UR_MODERN_TITLE_NATIVE_CAPTURE=passed")
    print("UR_MODERN_TITLE_HOST_PRESENT=passed")
    print(f"exe_sha256={exe_hash}")
    for c in receipt["captures"]:
        print(f"stage={c['stage']} guest_frame={c['guest_frame']} "
              f"source_raster={c['width']}x{c['height']} sha256={c['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
