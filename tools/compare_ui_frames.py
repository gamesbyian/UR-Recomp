#!/usr/bin/env python3
"""Compare named UI framebuffer BMP captures and summarize visual deltas."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Iterable


def load_bmp(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError(f"{path}: not a BMP")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40:
        raise ValueError(f"{path}: unsupported BMP DIB header {dib_size}")
    width = struct.unpack_from("<i", data, 18)[0]
    height_signed = struct.unpack_from("<i", data, 22)[0]
    planes = struct.unpack_from("<H", data, 26)[0]
    bpp = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if planes != 1 or width <= 0 or height_signed == 0:
        raise ValueError(f"{path}: invalid BMP geometry")
    if bpp not in (24, 32) or compression != 0:
        raise ValueError(f"{path}: only uncompressed 24/32-bit BMP is supported")

    height = abs(height_signed)
    top_down = height_signed < 0
    bytes_per_pixel = bpp // 8
    row_stride = ((width * bytes_per_pixel + 3) // 4) * 4
    need = pixel_offset + row_stride * height
    if need > len(data):
        raise ValueError(f"{path}: truncated BMP pixel data")

    rows: list[list[tuple[int, int, int]]] = []
    for stored_y in range(height):
        start = pixel_offset + stored_y * row_stride
        row = []
        for x in range(width):
            p = start + x * bytes_per_pixel
            b, g, r = data[p : p + 3]
            row.append((r, g, b))
        rows.append(row)
    if not top_down:
        rows.reverse()
    pixels = [px for row in rows for px in row]
    return width, height, pixels


def find_capture(tag: str, roots: Iterable[Path]) -> Path | None:
    for root in roots:
        path = root / f"{tag}.fb.bmp"
        if path.is_file():
            return path
    return None


def compare(before: Path, after: Path) -> dict:
    bw, bh, bp = load_bmp(before)
    aw, ah, ap = load_bmp(after)
    if (bw, bh) != (aw, ah):
        return {
            "status": "dimension-mismatch",
            "before_dimensions": [bw, bh],
            "after_dimensions": [aw, ah],
        }

    changed = 0
    total_abs = 0
    max_channel_delta = 0
    min_x = bw
    min_y = bh
    max_x = -1
    max_y = -1

    for i, (a, b) in enumerate(zip(bp, ap)):
        if a == b:
            continue
        changed += 1
        x = i % bw
        y = i // bw
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
        deltas = [abs(a[c] - b[c]) for c in range(3)]
        total_abs += sum(deltas)
        max_channel_delta = max(max_channel_delta, *deltas)

    total = bw * bh
    bbox = None if changed == 0 else [min_x, min_y, max_x, max_y]
    mean_abs_changed_channel = (
        total_abs / (changed * 3) if changed else 0.0
    )
    return {
        "status": "ok",
        "dimensions": [bw, bh],
        "changed_pixels": changed,
        "total_pixels": total,
        "changed_fraction": changed / total if total else 0.0,
        "change_bbox": bbox,
        "mean_abs_channel_delta_on_changed_pixels": mean_abs_changed_channel,
        "max_channel_delta": max_channel_delta,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# UI Frame Comparison Report",
        "",
        "| Pair | Changed pixels | Fraction | Bounding box | Mean delta | Status |",
        "|---|---:|---:|---|---:|---|",
    ]
    for item in report["pairs"]:
        result = item["result"]
        if result["status"] == "ok":
            bbox = result["change_bbox"]
            bbox_text = "" if bbox is None else ",".join(map(str, bbox))
            lines.append(
                f"| {item['id']} | {result['changed_pixels']} | "
                f"{result['changed_fraction']:.6f} | {bbox_text} | "
                f"{result['mean_abs_channel_delta_on_changed_pixels']:.2f} | ok |"
            )
        else:
            lines.append(f"| {item['id']} |  |  |  |  | {result['status']} |")
    lines += [
        "",
        "Interpretation aid:",
        "- tiny/local bounding box usually suggests cursor/indicator animation;",
        "- broad/full-frame deltas suggest a screen/state transition or major presentation change;",
        "- exact thresholds are scene-specific and should not be promoted without visual confirmation.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=Path("analysis/ui-frame-comparisons.json"))
    ap.add_argument("--dump-dir", action="append", type=Path, required=True)
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--out-md", type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    out = []
    for pair in manifest["pairs"]:
        before = find_capture(pair["before"], args.dump_dir)
        after = find_capture(pair["after"], args.dump_dir)
        if before is None or after is None:
            result = {
                "status": "missing",
                "missing": [
                    tag
                    for tag, path in ((pair["before"], before), (pair["after"], after))
                    if path is None
                ],
            }
        else:
            result = compare(before, after)
        out.append({
            "id": pair["id"],
            "before": pair["before"],
            "after": pair["after"],
            "purpose": pair.get("purpose"),
            "result": result,
        })

    report = {"schema_version": 1, "pairs": out}
    encoded = json.dumps(report, indent=2) + "\n"
    md = render_markdown(report)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(encoded)
    else:
        print(encoded, end="")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(md + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
