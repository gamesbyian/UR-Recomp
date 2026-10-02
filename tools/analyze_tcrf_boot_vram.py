#!/usr/bin/env python3
"""Locate the preserved TCRF boot graphic in startup VRAM snapshots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_tcrf_unused_content import (
    _canonical_color_signature,
    _palette_mapping_for_pair,
    decode_indexed_png,
    decode_snes_4bpp_tile,
    encode_snes_4bpp_tiles,
    sha256,
)


def aligned_tiles(data: bytes) -> list[bytes]:
    return [data[i:i + 32] for i in range(0, len(data) - 31, 32)]


def _mapping_key(mapping: dict[int, int]) -> str:
    return ",".join(f"{k}>{v}" for k, v in sorted(mapping.items()))


def _global_palette_mapping_candidates(
    vram_tiles: list[bytes], target_tiles: list[bytes]
) -> list[dict]:
    sig_index: dict[tuple[int, ...], list[tuple[int, list[list[int]]]]] = {}
    for index, tile in enumerate(vram_tiles):
        pixels = decode_snes_4bpp_tile(tile)
        sig_index.setdefault(_canonical_color_signature(pixels), []).append((index, pixels))

    support: dict[str, dict] = {}
    for target_index, tile in enumerate(target_tiles):
        source = decode_snes_4bpp_tile(tile)
        if len({v for row in source for v in row}) < 3:
            continue
        sig = _canonical_color_signature(source)
        for vram_index, target in sig_index.get(sig, []):
            mapping = _palette_mapping_for_pair(source, target)
            if mapping is None:
                continue
            key = _mapping_key(mapping)
            row = support.setdefault(
                key,
                {
                    "mapping": {str(k): v for k, v in sorted(mapping.items())},
                    "target_tile_indices": set(),
                    "vram_tile_indices": set(),
                    "pairs": [],
                },
            )
            row["target_tile_indices"].add(target_index)
            row["vram_tile_indices"].add(vram_index)
            if len(row["pairs"]) < 32:
                row["pairs"].append(
                    {"target_tile_index": target_index, "vram_tile_index": vram_index}
                )

    rows = []
    for row in support.values():
        rows.append({
            "mapping": row["mapping"],
            "distinct_target_tile_support": len(row["target_tile_indices"]),
            "distinct_vram_tile_support": len(row["vram_tile_indices"]),
            "target_tile_indices": sorted(row["target_tile_indices"]),
            "vram_tile_indices": sorted(row["vram_tile_indices"]),
            "pairs": row["pairs"],
        })
    rows.sort(
        key=lambda x: (
            x["distinct_target_tile_support"],
            x["distinct_vram_tile_support"],
        ),
        reverse=True,
    )
    return rows[:16]


def snapshot_match(vram: bytes, target_tiles: list[bytes]) -> dict:
    vram_tiles = aligned_tiles(vram)
    exact_index: dict[bytes, list[int]] = {}
    sig_index: dict[tuple[int, ...], list[int]] = {}
    for i, tile in enumerate(vram_tiles):
        exact_index.setdefault(tile, []).append(i)
        sig = _canonical_color_signature(decode_snes_4bpp_tile(tile))
        sig_index.setdefault(sig, []).append(i)

    distinct_targets = list(dict.fromkeys(target_tiles))
    exact_matches = [tile for tile in distinct_targets if tile in exact_index]

    nontrivial_targets = []
    invariant_matches = []
    for tile in distinct_targets:
        pixels = decode_snes_4bpp_tile(tile)
        color_count = len({v for row in pixels for v in row})
        if color_count < 3:
            continue
        nontrivial_targets.append(tile)
        sig = _canonical_color_signature(pixels)
        if sig in sig_index:
            invariant_matches.append(tile)

    mapping_candidates = _global_palette_mapping_candidates(vram_tiles, distinct_targets)

    return {
        "vram_size": len(vram),
        "vram_sha256": sha256(vram),
        "target_distinct_tiles": len(distinct_targets),
        "exact_distinct_target_tiles_present": len(exact_matches),
        "exact_distinct_target_fraction": (
            len(exact_matches) / len(distinct_targets) if distinct_targets else 0
        ),
        "nontrivial_distinct_target_tiles": len(nontrivial_targets),
        "palette_invariant_nontrivial_tiles_present": len(invariant_matches),
        "palette_invariant_nontrivial_fraction": (
            len(invariant_matches) / len(nontrivial_targets)
            if nontrivial_targets else 0
        ),
        "global_palette_mapping_candidates": mapping_candidates,
        "exact_target_tile_vram_indices": {
            str(i): exact_index[tile][:16]
            for i, tile in enumerate(target_tiles)
            if tile in exact_index
        },
    }


def analyze(boot_png: Path, dump_dir: Path) -> dict:
    meta, pixels = decode_indexed_png(boot_png)
    encoded = encode_snes_4bpp_tiles(pixels)
    target_tiles = aligned_tiles(encoded)
    snapshots = []
    for path in sorted(dump_dir.glob("*.vram.bin")):
        row = snapshot_match(path.read_bytes(), target_tiles)
        row["tag"] = path.name.removesuffix(".vram.bin")
        row["path"] = str(path)
        snapshots.append(row)

    best_exact = max(
        snapshots,
        key=lambda x: x["exact_distinct_target_tiles_present"],
        default=None,
    )
    best_invariant = max(
        snapshots,
        key=lambda x: x["palette_invariant_nontrivial_tiles_present"],
        default=None,
    )
    return {
        "schema_version": 1,
        "purpose": "Test whether the preserved TCRF 'used by decomp' graphic appears in startup VRAM.",
        "boot_graphic": {
            "path": str(boot_png),
            "png_sha256": meta["sha256"],
            "width": meta["ihdr"]["width"],
            "height": meta["ihdr"]["height"],
            "tile_count": len(target_tiles),
            "distinct_tile_count": len(set(target_tiles)),
            "encoded_snes_4bpp_sha256": sha256(encoded),
        },
        "snapshots": snapshots,
        "best_exact": best_exact,
        "best_palette_invariant": best_invariant,
        "interpretation": {
            "exact_full_presence_threshold": 1.0,
            "note": (
                "Exact tile presence is strongest evidence. Palette-invariant matching is retained "
                "as a weaker discriminator for reference images whose palette indices were normalized."
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot-png", type=Path, default=Path("reference/imported/tcrf/Uniracers-Decomp.png"))
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = analyze(args.boot_png, args.dump_dir)
    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
