#!/usr/bin/env python3
"""Find the minimal BG/OBJ layer combination that reproduces the +8 center-edge regression."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

TAGS = ("object-tail-167", "object-tail-168", "object-tail-169")
MASKS = (16, 17, 18, 19, 20, 21, 22, 23)


def read_bmp32(path: Path) -> tuple[bytes, int, int]:
    blob = path.read_bytes()
    if len(blob) < 54 or blob[:2] != b"BM":
        raise ValueError(f"{path}: not BMP")
    offset = struct.unpack_from("<I", blob, 10)[0]
    width = struct.unpack_from("<i", blob, 18)[0]
    signed_height = struct.unpack_from("<i", blob, 22)[0]
    bpp = struct.unpack_from("<H", blob, 28)[0]
    if width <= 0 or signed_height == 0 or bpp != 32:
        raise ValueError(f"{path}: unsupported BMP")
    height = abs(signed_height)
    raw = blob[offset:offset + width * height * 4]
    if signed_height > 0:
        rows = [raw[y*width*4:(y+1)*width*4] for y in range(height)]
        raw = b"".join(reversed(rows))
    return raw, width, height


def center(raw: bytes, width: int, height: int, margin: int) -> bytes:
    return b"".join(
        raw[(y * width + margin) * 4:(y * width + margin + 256) * 4]
        for y in range(height)
    )


def diff_pixels(a: bytes, b: bytes) -> list[dict]:
    out = []
    width = 256
    for p in range(len(a) // 4):
        aa, bb = a[p*4:p*4+4], b[p*4:p*4+4]
        if aa != bb:
            out.append({
                "x": p % width,
                "y": p // width,
                "control_bgra": list(aa),
                "plus8_bgra": list(bb),
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    rows = []
    for mask in MASKS:
        for tag in TAGS:
            samples = {}
            for margin in (0, 8):
                d = args.root / f"mask-{mask}" / f"margin-{margin}"
                info = json.loads((d / "state" / f"{tag}.info.json").read_text())
                frame = int(info["frame"])
                fb, width, height = read_bmp32(d / "frames" / f"frame_{frame - 1:06d}.bmp")
                samples[margin] = {
                    "frame": frame,
                    "center": center(fb, width, height, margin),
                }
            diffs = diff_pixels(samples[0]["center"], samples[8]["center"])
            rows.append({
                "mask": mask,
                "tag": tag,
                "guest_frame_delta": samples[8]["frame"] - samples[0]["frame"],
                "diff_count": len(diffs),
                "diffs": diffs,
            })

    at168 = [r for r in rows if r["tag"] == "object-tail-168"]
    reproducing = [r["mask"] for r in at168 if r["diff_count"]]
    minimal = []
    for mask in reproducing:
        bg = mask & 0x0F
        if not any(
            other != mask
            and (other & 0x10)
            and ((other & 0x0F) & bg) == (other & 0x0F)
            and (other & 0x0F) != bg
            and other in reproducing
            for other in reproducing
        ):
            minimal.append(mask)

    report = {
        "fixture": "tests/input/object-activation-dragster-tail.script",
        "tags": list(TAGS),
        "masks": list(MASKS),
        "reproducing_masks_at_168": reproducing,
        "minimal_reproducing_masks_at_168": minimal,
        "rows": rows,
    }

    names = {
        16: "OBJ",
        17: "OBJ+BG1",
        18: "OBJ+BG2",
        19: "OBJ+BG1+BG2",
        20: "OBJ+BG3",
        21: "OBJ+BG1+BG3",
        22: "OBJ+BG2+BG3",
        23: "OBJ+BG1+BG2+BG3",
    }
    lines = [
        "# +8 composition interaction matrix",
        "",
        "| mask | layers | diff @167 | diff @168 | diff @169 |",
        "|---:|---|---:|---:|---:|",
    ]
    by = {(r["mask"], r["tag"]): r for r in rows}
    for mask in MASKS:
        lines.append(
            f"| {mask} | {names[mask]} | "
            f"{by[(mask, TAGS[0])]['diff_count']} | "
            f"{by[(mask, TAGS[1])]['diff_count']} | "
            f"{by[(mask, TAGS[2])]['diff_count']} |"
        )
    lines += [
        "",
        "Masks reproducing the object-tail-168 center regression: "
        + (", ".join(f"{m} ({names[m]})" for m in reproducing) or "none"),
        "",
        "Minimal reproducing masks: "
        + (", ".join(f"{m} ({names[m]})" for m in minimal) or "none"),
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
