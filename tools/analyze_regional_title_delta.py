#!/usr/bin/env python3
"""Localize USA-retail vs Europe-retail title presentation deltas.

Consumes matched snesref dump directories produced by compare_retail_frontend.py.
The output is deliberately presentation/evidence oriented: framebuffer bounds,
VRAM byte/tile deltas, CGRAM color deltas, and cross-checkpoint stable sets.
It does not infer that every stable delta belongs to the game logo.

When two or more checkpoints prove the same settled USA/Europe framebuffer
pair, --asset-out can also retain a compact exact Europe crop. The crop is
palette-indexed and Base85 encoded so the shipping presenter can remain
provenance-bound without carrying a second ROM or mutating guest VRAM.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from compare_framebuffers import compare_frames

DEFAULT_CHECKPOINTS = ("boot-300", "boot-360", "boot-420")
VRAM_BYTES = 0x10000
CGRAM_BYTES = 0x200
SNES_4BPP_TILE_BYTES = 32
FRAME_WIDTH = 256
FRAME_HEIGHT = 224
FRAME_BPP = 4


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fnv1a64(data: bytes) -> str:
    value = 1469598103934665603
    for byte in data:
        value ^= byte
        value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"0x{value:016x}"


def bgr_bytes(bgrx: bytes) -> bytes:
    if len(bgrx) % FRAME_BPP:
        raise ValueError("BGRX payload length is not pixel-aligned")
    out = bytearray()
    for offset in range(0, len(bgrx), FRAME_BPP):
        out.extend(bgrx[offset:offset + 3])
    return bytes(out)


def rgb_bytes(bgrx: bytes) -> bytes:
    if len(bgrx) % FRAME_BPP:
        raise ValueError("BGRX payload length is not pixel-aligned")
    out = bytearray()
    for offset in range(0, len(bgrx), FRAME_BPP):
        b, g, r = bgrx[offset:offset + 3]
        out.extend((r, g, b))
    return bytes(out)


def changed_offsets(a: bytes, b: bytes) -> list[int]:
    if len(a) != len(b):
        raise ValueError(f"binary sizes differ: {len(a)} != {len(b)}")
    return [i for i, (left, right) in enumerate(zip(a, b)) if left != right]


def contiguous_ranges(offsets: list[int]) -> list[dict]:
    if not offsets:
        return []
    rows: list[dict] = []
    start = previous = offsets[0]
    for offset in offsets[1:]:
        if offset != previous + 1:
            rows.append(
                {
                    "start": start,
                    "end_exclusive": previous + 1,
                    "length": previous + 1 - start,
                }
            )
            start = offset
        previous = offset
    rows.append(
        {
            "start": start,
            "end_exclusive": previous + 1,
            "length": previous + 1 - start,
        }
    )
    return rows


def compare_blob(
    a: bytes,
    b: bytes,
    *,
    expected_size: int | None = None,
    grouping: int | None = None,
) -> dict:
    if expected_size is not None and (len(a) != expected_size or len(b) != expected_size):
        raise ValueError(
            f"unexpected blob size: {len(a)} / {len(b)}; expected {expected_size}"
        )
    offsets = changed_offsets(a, b)
    row = {
        "bytes": len(a),
        "changed_bytes": len(offsets),
        "changed_fraction": len(offsets) / len(a) if a else 0.0,
        "ranges": contiguous_ranges(offsets),
        "usa_sha256": sha256(a),
        "europe_sha256": sha256(b),
    }
    if grouping:
        row["changed_groups"] = sorted({offset // grouping for offset in offsets})
    return row


def _load_pair(
    usa_dir: Path,
    europe_dir: Path,
    checkpoint: str,
    suffix: str,
) -> tuple[bytes, bytes] | None:
    usa = usa_dir / f"{checkpoint}.{suffix}"
    europe = europe_dir / f"{checkpoint}.{suffix}"
    if not usa.is_file() or not europe.is_file():
        return None
    return usa.read_bytes(), europe.read_bytes()


def compare_checkpoint(
    usa_dir: Path,
    europe_dir: Path,
    checkpoint: str,
) -> dict:
    row: dict = {
        "checkpoint": checkpoint,
        "framebuffer": None,
        "vram": None,
        "cgram": None,
    }

    pair = _load_pair(usa_dir, europe_dir, checkpoint, "fb.bgrx")
    if pair:
        row["framebuffer"] = compare_frames(
            pair[0], pair[1], width=FRAME_WIDTH, bytes_per_pixel=FRAME_BPP
        )

    pair = _load_pair(usa_dir, europe_dir, checkpoint, "vram.bin")
    if pair:
        row["vram"] = compare_blob(
            pair[0],
            pair[1],
            expected_size=VRAM_BYTES,
            grouping=SNES_4BPP_TILE_BYTES,
        )
        row["vram"]["changed_tile_indices"] = row["vram"].pop("changed_groups")

    pair = _load_pair(usa_dir, europe_dir, checkpoint, "cgram.bin")
    if pair:
        row["cgram"] = compare_blob(
            pair[0],
            pair[1],
            expected_size=CGRAM_BYTES,
            grouping=2,
        )
        row["cgram"]["changed_color_indices"] = row["cgram"].pop("changed_groups")

    return row


def _stable_sets(rows: list[dict], section: str, field: str) -> dict:
    present = [
        set(row[section][field])
        for row in rows
        if row.get(section) is not None
    ]
    if not present:
        return {"checkpoint_count": 0, "intersection": [], "union": []}
    return {
        "checkpoint_count": len(present),
        "intersection": sorted(set.intersection(*present)),
        "union": sorted(set.union(*present)),
    }


def _crop(
    frame: bytes,
    bbox: list[int],
    *,
    width: int = FRAME_WIDTH,
    bytes_per_pixel: int = FRAME_BPP,
) -> bytes:
    x0, y0, x1, y1 = bbox
    if x0 < 0 or y0 < 0 or x1 < x0 or y1 < y0 or x1 >= width:
        raise ValueError(f"invalid framebuffer crop {bbox!r}")
    height = len(frame) // (width * bytes_per_pixel)
    if y1 >= height:
        raise ValueError(f"crop exceeds framebuffer height: {bbox!r} / {height}")
    out = bytearray()
    for y in range(y0, y1 + 1):
        start = (y * width + x0) * bytes_per_pixel
        end = (y * width + x1 + 1) * bytes_per_pixel
        out.extend(frame[start:end])
    return bytes(out)


def build_settled_asset(
    usa_dir: Path,
    europe_dir: Path,
    rows: list[dict],
) -> dict:
    """Build an exact raster asset only from a repeated settled frame pair.

    A one-off checkpoint is insufficient because it may be an animation or
    cadence phase. At least two checkpoints must have identical full USA and
    Europe framebuffer hashes and the same bounded regional-delta rectangle.
    """
    groups: dict[tuple[str, str, tuple[int, ...]], list[str]] = defaultdict(list)
    by_checkpoint = {row["checkpoint"]: row for row in rows}
    for row in rows:
        fb = row.get("framebuffer")
        if not fb or not fb.get("bbox") or not fb.get("changed_pixels"):
            continue
        key = (
            fb["a_sha256"],
            fb["b_sha256"],
            tuple(fb["bbox"]),
        )
        groups[key].append(row["checkpoint"])

    repeated = [(key, cps) for key, cps in groups.items() if len(cps) >= 2]
    if not repeated:
        raise ValueError("no repeated settled USA/Europe title framebuffer pair")

    repeated.sort(key=lambda item: (-len(item[1]), item[1]))
    (usa_full_sha, europe_full_sha, bbox_tuple), checkpoints = repeated[0]
    bbox = list(bbox_tuple)
    first = checkpoints[0]
    pair = _load_pair(usa_dir, europe_dir, first, "fb.bgrx")
    if pair is None:
        raise ValueError(f"missing framebuffer pair for {first}")
    usa_crop = _crop(pair[0], bbox)
    europe_crop = _crop(pair[1], bbox)

    for checkpoint in checkpoints[1:]:
        other = _load_pair(usa_dir, europe_dir, checkpoint, "fb.bgrx")
        if other is None:
            raise ValueError(f"missing framebuffer pair for {checkpoint}")
        if _crop(other[0], bbox) != usa_crop or _crop(other[1], bbox) != europe_crop:
            raise ValueError("repeated framebuffer hashes disagree at crop level")

    def indexed_payload(crop: bytes) -> tuple[list[int], bytes, bytes]:
        palette = sorted(
            {
                int.from_bytes(crop[i:i + FRAME_BPP], "little")
                for i in range(0, len(crop), FRAME_BPP)
            }
        )
        if len(palette) > 256:
            raise ValueError(f"settled title crop needs {len(palette)} colors")
        palette_index = {value: index for index, value in enumerate(palette)}
        indices = bytes(
            palette_index[int.from_bytes(crop[i:i + FRAME_BPP], "little")]
            for i in range(0, len(crop), FRAME_BPP)
        )
        padded = indices + bytes((-len(indices)) % 4)
        return palette, indices, padded

    source_palette, source_indices, source_padded_indices = indexed_payload(usa_crop)
    palette, indices, padded_indices = indexed_payload(europe_crop)
    cgram_identical = all(
        by_checkpoint[checkpoint].get("cgram") is not None
        and by_checkpoint[checkpoint]["cgram"]["changed_bytes"] == 0
        for checkpoint in checkpoints
    )
    x0, y0, x1, y1 = bbox
    return {
        "schema_version": 1,
        "kind": "regional-settled-title-raster",
        "format": "BGRX8888 palette-indexed",
        "evidence_checkpoints": checkpoints,
        "source_full_frame_sha256": usa_full_sha,
        "target_full_frame_sha256": europe_full_sha,
        "source_crop_sha256": sha256(usa_crop),
        "target_crop_sha256": sha256(europe_crop),
        "source_crop_fnv1a64": fnv1a64(usa_crop),
        "target_crop_fnv1a64": fnv1a64(europe_crop),
        "source_crop_bgr_fnv1a64": fnv1a64(bgr_bytes(usa_crop)),
        "target_crop_bgr_fnv1a64": fnv1a64(bgr_bytes(europe_crop)),
        "source_crop_rgb_sha256": sha256(rgb_bytes(usa_crop)),
        "target_crop_rgb_sha256": sha256(rgb_bytes(europe_crop)),
        "bbox_inclusive": bbox,
        "origin": [x0, y0],
        "width": x1 - x0 + 1,
        "height": y1 - y0 + 1,
        "source_palette_u32_le": [f"0x{value:08x}" for value in source_palette],
        "source_indices_encoding": "python-base85-padded-to-4",
        "source_indices_base85": base64.b85encode(source_padded_indices).decode("ascii"),
        "source_indices_decoded_bytes": len(source_indices),
        "source_indices_padded_bytes": len(source_padded_indices),
        "palette_u32_le": [f"0x{value:08x}" for value in palette],
        "indices_encoding": "python-base85-padded-to-4",
        "indices_base85": base64.b85encode(padded_indices).decode("ascii"),
        "indices_decoded_bytes": len(indices),
        "indices_padded_bytes": len(padded_indices),
        "cgram_identical_across_evidence": cgram_identical,
        "admission": (
            "Apply only on the Modern idle title surface when the current "
            "canonical crop hashes exactly to source_crop_sha256. Otherwise "
            "fail closed to canonical Uniracers presentation."
        ),
    }


def analyze(
    usa_dir: Path,
    europe_dir: Path,
    checkpoints: list[str] | tuple[str, ...] = DEFAULT_CHECKPOINTS,
) -> dict:
    rows = [compare_checkpoint(usa_dir, europe_dir, cp) for cp in checkpoints]
    matched = sum(
        1
        for row in rows
        if row["framebuffer"] is not None
        or row["vram"] is not None
        or row["cgram"] is not None
    )
    report = {
        "schema_version": 2,
        "purpose": (
            "Bound and fingerprint presentation deltas at matched USA/Europe "
            "retail title checkpoints without assigning semantics by assumption."
        ),
        "checkpoints": rows,
        "summary": {
            "requested_checkpoint_count": len(rows),
            "matched_checkpoint_count": matched,
            "stable_vram_tiles": _stable_sets(
                rows, "vram", "changed_tile_indices"
            ),
            "stable_cgram_colors": _stable_sets(
                rows, "cgram", "changed_color_indices"
            ),
        },
    }
    try:
        asset = build_settled_asset(usa_dir, europe_dir, rows)
    except ValueError as exc:
        report["summary"]["settled_framebuffer_candidate"] = {
            "available": False,
            "reason": str(exc),
        }
    else:
        report["summary"]["settled_framebuffer_candidate"] = {
            "available": True,
            "evidence_checkpoints": asset["evidence_checkpoints"],
            "bbox_inclusive": asset["bbox_inclusive"],
            "source_crop_sha256": asset["source_crop_sha256"],
            "target_crop_sha256": asset["target_crop_sha256"],
            "source_crop_fnv1a64": asset["source_crop_fnv1a64"],
            "target_crop_fnv1a64": asset["target_crop_fnv1a64"],
            "source_crop_bgr_fnv1a64": asset["source_crop_bgr_fnv1a64"],
            "target_crop_bgr_fnv1a64": asset["target_crop_bgr_fnv1a64"],
            "source_crop_rgb_sha256": asset["source_crop_rgb_sha256"],
            "target_crop_rgb_sha256": asset["target_crop_rgb_sha256"],
            "palette_entries": len(asset["palette_u32_le"]),
            "cgram_identical_across_evidence": asset[
                "cgram_identical_across_evidence"
            ],
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("usa_dir", type=Path)
    parser.add_argument("europe_dir", type=Path)
    parser.add_argument(
        "--checkpoint",
        action="append",
        dest="checkpoints",
        help="checkpoint tag; repeatable (default: boot-300/360/420)",
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--asset-out", type=Path)
    args = parser.parse_args()

    checkpoints = args.checkpoints or list(DEFAULT_CHECKPOINTS)
    report = analyze(args.usa_dir, args.europe_dir, checkpoints)
    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    if args.asset_out:
        rows = [compare_checkpoint(args.usa_dir, args.europe_dir, cp) for cp in checkpoints]
        asset = build_settled_asset(args.usa_dir, args.europe_dir, rows)
        args.asset_out.parent.mkdir(parents=True, exist_ok=True)
        args.asset_out.write_text(
            json.dumps(asset, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
