#!/usr/bin/env python3
"""Localize the first +8 Widescreen sprite/OAM presentation divergence."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

TAGS = [f"object-tail-{i:03d}" for i in range(160, 181)]


def read_bmp32(path: Path) -> tuple[bytes, int, int]:
    blob = path.read_bytes()
    if len(blob) < 54 or blob[:2] != b"BM":
        raise ValueError(f"{path}: not a BMP")
    offset = struct.unpack_from("<I", blob, 10)[0]
    width = struct.unpack_from("<i", blob, 18)[0]
    signed_height = struct.unpack_from("<i", blob, 22)[0]
    bpp = struct.unpack_from("<H", blob, 28)[0]
    if width <= 0 or signed_height == 0 or bpp != 32:
        raise ValueError(f"{path}: unsupported BMP")
    height = abs(signed_height)
    raw = blob[offset : offset + width * height * 4]
    if signed_height > 0:
        rows = [raw[y * width * 4 : (y + 1) * width * 4] for y in range(height)]
        raw = b"".join(reversed(rows))
    return raw, width, height


def center_crop(raw: bytes, width: int, height: int, x0: int) -> bytes:
    return b"".join(
        raw[(y * width + x0) * 4 : (y * width + x0 + 256) * 4]
        for y in range(height)
    )


def decode_oam(blob: bytes) -> list[dict]:
    if len(blob) != 0x220:
        raise ValueError(f"expected 0x220 OAM bytes, got {len(blob):#x}")
    low = blob[:0x200]
    high = blob[0x200:]
    out = []
    for i in range(128):
        off = i * 4
        xlo, y, tile, attr = low[off : off + 4]
        pair = high[i // 4]
        bits = (pair >> ((i & 3) * 2)) & 0x3
        xraw = xlo | ((bits & 1) << 8)
        x = xraw - 512 if xraw >= 256 else xraw
        out.append({
            "slot": i,
            "x": x,
            "x_raw": xraw,
            "y": y,
            "tile": tile,
            "attr": attr,
            "large": bool(bits & 2),
            "raw_low": [xlo, y, tile, attr],
            "raw_high_bits": bits,
        })
    return out


def changed_slots(a: bytes, b: bytes) -> list[dict]:
    da, db = decode_oam(a), decode_oam(b)
    rows = []
    for x, y in zip(da, db):
        if x != y:
            rows.append({"slot": x["slot"], "control": x, "plus8": y})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    ap.add_argument("--unlimited-root", type=Path)
    ap.add_argument("--obj-root", type=Path)
    args = ap.parse_args()

    rows = []
    for tag in TAGS:
        samples = {}
        for margin in (0, 8):
            d = args.root / f"margin-{margin}"
            info = json.loads((d / "state" / f"{tag}.info.json").read_text())
            frame = int(info["frame"])
            presented = frame - 1
            oam = (d / "state" / f"{tag}.oam.bin").read_bytes()
            fb_path = d / "frames" / f"frame_{presented:06d}.bmp"
            center = None
            if fb_path.is_file():
                fb, width, height = read_bmp32(fb_path)
                center = center_crop(fb, width, height, margin)
            samples[margin] = {
                "frame": frame,
                "presented": presented,
                "oam": oam,
                "center": center,
            }

        ctrl, wide = samples[0], samples[8]
        slot_diffs = changed_slots(ctrl["oam"], wide["oam"])
        pixel_diff = None
        if ctrl["center"] is not None and wide["center"] is not None:
            pixel_diff = sum(
                ctrl["center"][i:i+4] != wide["center"][i:i+4]
                for i in range(0, len(ctrl["center"]), 4)
            )
        rows.append({
            "tag": tag,
            "control_frame": ctrl["frame"],
            "plus8_frame": wide["frame"],
            "guest_frame_delta": wide["frame"] - ctrl["frame"],
            "center_diff_pixels": pixel_diff,
            "oam_equal": not slot_diffs,
            "changed_oam_slots": slot_diffs,
        })

    first_pixel = next(
        (r for r in rows if (r["center_diff_pixels"] or 0) > 0),
        None,
    )
    first_oam = next((r for r in rows if not r["oam_equal"]), None)
    if first_pixel is None:
        classification = "no-center-divergence-in-window"
    elif first_pixel["oam_equal"]:
        classification = "identical-oam-host-raster-divergence"
    else:
        classification = "guest-oam-presentation-state-divergence"

    unlimited_first_pixel = None
    if args.unlimited_root:
        for tag in TAGS:
            centers = {}
            frames = {}
            for margin in (0, 8):
                d = args.unlimited_root / f"margin-{margin}"
                info_path = d / "state" / f"{tag}.info.json"
                if not info_path.is_file():
                    centers = {}
                    break
                info = json.loads(info_path.read_text())
                frame = int(info["frame"])
                fb_path = d / "frames" / f"frame_{frame - 1:06d}.bmp"
                if not fb_path.is_file():
                    centers = {}
                    break
                fb, width, height = read_bmp32(fb_path)
                centers[margin] = center_crop(fb, width, height, margin)
                frames[margin] = frame
            if len(centers) != 2:
                continue
            diff = sum(
                centers[0][i:i+4] != centers[8][i:i+4]
                for i in range(0, len(centers[0]), 4)
            )
            if diff:
                unlimited_first_pixel = {
                    "tag": tag,
                    "center_diff_pixels": diff,
                    "control_frame": frames[0],
                    "plus8_frame": frames[8],
                    "guest_frame_delta": frames[8] - frames[0],
                }
                break

    sprite_limit_discriminator = None
    if args.unlimited_root and first_pixel is not None:
        sprite_limit_discriminator = (
            "width-divergence-eliminated-without-sprite-limits"
            if unlimited_first_pixel is None
            else "width-divergence-persists-without-sprite-limits"
        )

    obj_first_pixel = None
    if args.obj_root:
        for tag in TAGS:
            centers = {}
            frames = {}
            for margin in (0, 8):
                d = args.obj_root / f"margin-{margin}"
                info_path = d / "state" / f"{tag}.info.json"
                if not info_path.is_file():
                    centers = {}
                    break
                info = json.loads(info_path.read_text())
                frame = int(info["frame"])
                fb_path = d / "frames" / f"frame_{frame - 1:06d}.bmp"
                if not fb_path.is_file():
                    centers = {}
                    break
                fb, width, height = read_bmp32(fb_path)
                centers[margin] = center_crop(fb, width, height, margin)
                frames[margin] = frame
            if len(centers) != 2:
                continue
            diff = sum(
                centers[0][i:i+4] != centers[8][i:i+4]
                for i in range(0, len(centers[0]), 4)
            )
            if diff:
                obj_first_pixel = {
                    "tag": tag,
                    "center_diff_pixels": diff,
                    "control_frame": frames[0],
                    "plus8_frame": frames[8],
                    "guest_frame_delta": frames[8] - frames[0],
                }
                break

    obj_discriminator = None
    if args.obj_root and first_pixel is not None:
        obj_discriminator = (
            "divergence-present-in-obj-raster"
            if obj_first_pixel is not None
            else "obj-raster-matches-composite-stage-diverges"
        )

    report = {
        "fixture": "tests/input/object-activation-dragster-tail.script",
        "margins": [0, 8],
        "classification": classification,
        "first_center_divergence": first_pixel,
        "first_oam_divergence": first_oam,
        "unlimited_first_center_divergence": unlimited_first_pixel,
        "sprite_limit_discriminator": sprite_limit_discriminator,
        "obj_first_center_divergence": obj_first_pixel,
        "obj_discriminator": obj_discriminator,
        "samples": rows,
    }

    lines = [
        "# +8 Widescreen OAM boundary",
        "",
        f"Classification: **{classification}**",
        "",
        "| tag | frame delta | center diff px | OAM | changed slots |",
        "|---|---:|---:|---|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['tag']} | {r['guest_frame_delta']} | "
            f"{'-' if r['center_diff_pixels'] is None else r['center_diff_pixels']} | "
            f"{'match' if r['oam_equal'] else 'DIFF'} | "
            f"{len(r['changed_oam_slots'])} |"
        )

    if first_pixel:
        lines += [
            "",
            f"First center divergence: {first_pixel['tag']} "
            f"({first_pixel['center_diff_pixels']} pixels).",
            f"OAM at that event is {'identical' if first_pixel['oam_equal'] else 'different'}.",
        ]
    if sprite_limit_discriminator:
        lines += [
            "",
            f"Sprite-limit discriminator: **{sprite_limit_discriminator}**.",
            "Unlimited first center divergence: "
            + ("none in sampled window" if unlimited_first_pixel is None else unlimited_first_pixel["tag"]),
        ]

    if obj_discriminator:
        lines += [
            "",
            f"OBJ-only discriminator: **{obj_discriminator}**.",
            "OBJ-only first center divergence: "
            + ("none in sampled window" if obj_first_pixel is None else obj_first_pixel["tag"]),
        ]

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
