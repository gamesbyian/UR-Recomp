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


def read_present_ppm(path: Path, expected_width: int = 342) -> tuple[int, int, bytes]:
    raw = path.read_bytes()
    match = PPM_HEADER.match(raw)
    if match is None:
        raise ValueError(f"{path}: not a host P6 presented screenshot")
    w, h = (int(x) for x in match.groups())
    payload = raw[match.end():]
    if w != expected_width or h != 224 or len(payload) != w * h * 3:
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


def verify_native_presented_frames(
    present_dir: Path, source_dir: Path, expected_width: int = 342,
    reduced_motion: bool = False) -> dict:
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
        width, height, rgb = read_present_ppm(file, expected_width)
        photos.append((frame, rgb, file))
    matches = {}
    for stage, bounds in (
        ("title", ((expected_width - 238) // 2, 27, 238, 81)),
        ("root", ((expected_width - 240) // 2 + 10, 17, 218, 142)),
    ):
        _, _, source = read_pam(source_dir /
                               f"modern-native-{stage}-{expected_width}x224.pam",
                               expected_width)
        best = max(
            ((_pixel_match(source, rgb, expected_width, bounds), frame, file)
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
    if reduced_motion:
        _, _, title_source = read_pam(
            source_dir / f"modern-native-title-{expected_width}x224.pam",
            expected_width)
        original_logo_region = ((expected_width - 238) // 2, 27, 238, 81)
        before_confirm = [(frame, rgb) for frame, rgb, _ in photos if frame < 60]
        if len(before_confirm) < 2:
            raise ValueError("reduced-motion title needs two distinct pre-confirm presents")
        for frame, rgb in before_confirm:
            if _pixel_match(title_source, rgb, expected_width,
                            original_logo_region) < 0.995:
                raise ValueError(
                    f"reduced-motion original title moved at present frame {frame}")
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


def verify_native_title_entry(log: str, *, reduced_motion: bool = False) -> None:
    # Real native P1 A is applied INSIDE the gamepad callback. With reduced
    # motion it immediately enters root before the CI script can report the
    # *successful* gamepad call; ordinary motion logs only after 14 frames.
    # Both orders are causally correct but MUST be explicitly selected.
    opened = "UR_BALDOSA_MODERN_ROOT opened=1"
    input_ack = "UR_BALDOSA_MODERN_TITLE native_p1_start=1 frame=60"
    entered = "UR_BALDOSA_MODERN_TITLE entered_root=1"
    root_paint = "UR_BALDOSA_MODERN_ROOT painted=1"
    witness = (
        (opened, entered, input_ack, root_paint) if reduced_motion
        else (opened, input_ack, entered, root_paint)
    )
    prev = -1
    for marker in witness:
        if log.count(marker) != 1:
            raise ValueError(f"missing/duplicate genuine native guest witness: {marker}")
        pos = log.find(marker, prev + 1)
        if pos < 0:
            raise ValueError(f"missing/out-of-order genuine native guest witness: {marker}")
        prev = pos


def validate_native_capture(
    folder: Path, log: str, *, exe_sha256: str,
    expected_width: int = 342, reduced_motion: bool = False) -> dict:
    verify_native_title_entry(log, reduced_motion=reduced_motion)
    output = {"executable_sha256": exe_sha256, "captures": []}
    for stage in ("title", "root"):
        name = f"modern-native-{stage}-{expected_width}x224.pam"
        file = folder / name
        w, h, rgba = read_pam(file, expected_width)
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
    parser.add_argument("--reduced-motion", action="store_true",
                        help="require steady stock title art before P1 confirm")
    parser.add_argument("--aspect", choices=("wide", "4:3"), default="wide",
                        help="actual native SDL drawable shape, not crop")
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
    config.write_text("[Sound]\nEnableAudio = 0\n" +
                      ("[Graphics]\nWindowSize = 960x720\n"
                       if args.aspect == "4:3" else ""), encoding="utf-8")
    environment = dict(os.environ)
    environment.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "SNESRECOMP_USER_DATA_DIR": str(user),
        "UR_EXECUTION_MODE": "modern",
        "UR_BALDOSA_MODERN_ROOT": "1",
        "UR_BALDOSA_MODERN_PROFILE_SELECT": "0",
        "UR_BALDOSA_MODERN_ROOT_KEY_SMOKE": "15",
        "UR_REDUCED_MOTION": "1" if args.reduced_motion else "0",
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
    expected_width = 256 if args.aspect == "4:3" else 342
    receipt = validate_native_capture(
        captures, log, exe_sha256=exe_hash, expected_width=expected_width,
        reduced_motion=args.reduced_motion)
    receipt["native_presented"] = verify_native_presented_frames(
        presented, captures, expected_width=expected_width,
        reduced_motion=args.reduced_motion)
    receipt["drawable_aspect"] = args.aspect
    receipt["reduced_motion"] = args.reduced_motion
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
