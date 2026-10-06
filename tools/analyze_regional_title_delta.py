#!/usr/bin/env python3
"""Localize USA-retail vs Europe-retail title presentation deltas.

Consumes matched snesref dump directories produced by compare_retail_frontend.py.
The output is deliberately presentation/evidence oriented: framebuffer bounds,
VRAM byte/tile deltas, CGRAM color deltas, and cross-checkpoint stable sets.
It does not infer that every stable delta belongs to the game logo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from compare_framebuffers import compare_frames

DEFAULT_CHECKPOINTS = ("boot-300", "boot-360", "boot-420")
VRAM_BYTES = 0x10000
CGRAM_BYTES = 0x200
SNES_4BPP_TILE_BYTES = 32


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
            pair[0], pair[1], width=256, bytes_per_pixel=4
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
    return {
        "schema_version": 1,
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
    args = parser.parse_args()

    report = analyze(
        args.usa_dir,
        args.europe_dir,
        args.checkpoints or list(DEFAULT_CHECKPOINTS),
    )
    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
