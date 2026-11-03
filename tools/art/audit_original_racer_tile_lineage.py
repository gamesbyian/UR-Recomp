#!/usr/bin/env python3
"""Authenticated ROM source-tile lineage across original racer compositions.

A repeated 8x8 ROM tile is evidence of 2D source asset reuse, never proof of
one anatomical part, one 1994 animation frame or an original 3D rig.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

SCHEMA = "UR-ART4K-ORIGINAL-RACER-SOURCE-TILE-LINEAGE/1"
WIDTH = HEIGHT = 64
X_OFFSET = 1
ROWS, COLUMNS = 5, 6


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_tile(raw: bytes) -> tuple[int, ...]:
    """SNES 4bpp planar, one 8x8 tile, with palette zero preserved."""
    if not isinstance(raw, bytes) or len(raw) != 32:
        raise ValueError("exact 32-byte source 4bpp tile required")
    out = []
    for y in range(8):
        b0, b1 = raw[2*y:2*y+2]
        b2, b3 = raw[16+2*y:18+2*y]
        for x in range(8):
            n = 7-x
            out.append(((b0>>n)&1) | (((b1>>n)&1)<<1) |
                       (((b2>>n)&1)<<2) | (((b3>>n)&1)<<3))
    return tuple(out)


def compose_tile_lineage(composition: dict, player: str, tile_loader) -> dict:
    """Reconstruct the source tile raster, retaining content identity and slot.

    tile_loader(word:int) returns (32-byte tile, exact source metadata); the
    production caller passes the existing original ROM piece_source_tile.
    """
    if player not in ("p1", "p2") or not isinstance(composition, dict):
        raise ValueError("source player/composition invalid")
    cells = composition.get("cells")
    if not isinstance(cells, list) or len(cells) != 70:
        raise ValueError("expected full 5x14 original staging grid")
    plane = bytearray(WIDTH*HEIGHT)
    touched = bytearray(WIDTH*HEIGHT)
    slots = set()
    entries = []
    for cell in cells:
        if not isinstance(cell, dict):
            raise ValueError("malformed original stage cell")
        if cell.get("player") != player:
            continue
        row, column = cell.get("major_slot"), cell.get("minor_slot")
        if (type(row) is not int or type(column) is not int or
                not 0 <= row < ROWS or not 0 <= column < COLUMNS or
                (row, column) in slots):
            raise ValueError("duplicate/out-of-range original source tile slot")
        slots.add((row, column))
        word = cell.get("word_hex")
        if word is None:
            continue
        if (not isinstance(word, str) or not word.startswith("0x") or
                len(word) != 6):
            raise ValueError("original packed source tile word invalid")
        number = int(word, 16)
        source, meta = tile_loader(number)
        if (not isinstance(meta, dict) or
                meta.get("source_sha256") != digest(source) or
                not isinstance(meta.get("source_snes"), str) or
                not isinstance(meta.get("source_rom_offset"), int)):
            raise ValueError("unverified original source-tile bytes or identity")
        indices = decode_tile(source)
        gx, gy = X_OFFSET+column, row
        for dy in range(8):
            for dx in range(8):
                q = (gy*8+dy)*WIDTH+gx*8+dx
                if touched[q]:
                    raise ValueError("source staging tiles overlap")
                plane[q] = indices[dy*8+dx]
                touched[q] = 1
        hist = Counter(indices)
        entries.append({
            "row": row, "column": column, "source_word": word,
            "source_tile_snes": meta["source_snes"],
            "source_tile_rom_offset": meta["source_rom_offset"],
            "source_tile_sha256": digest(source),
            "palette_index_pixels": {str(i): hist[i] for i in sorted(hist)},
            "opaque_pixels": 64-hist[0],
            "source_stream_choice": cell.get("choice"),
        })
    if len(slots) != 30:
        raise ValueError("incomplete original player staging cells")
    if not any(plane):
        raise ValueError("source representation lacks opaque original racer tiles")
    return {
        "source_4bpp_index_sha256": digest(plane),
        "source_tile_written_sha256": digest(touched),
        "tile_slots_written": len(entries),
        "opaque_source_pixels": sum(bool(i) for i in plane),
        "explicit_transparent_source_pixels": sum(1 for i,t in zip(plane,touched) if t and not i),
        "entries": sorted(entries,key=lambda x:(x["row"],x["column"])),
        "_indices": bytes(plane), "_touched": bytes(touched),
    }


def summarize_lineages(rows: list[dict]) -> dict:
    """Deduplicate colourways by index SHA before counting tile reuse."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("no authenticated source tile representations")
    by_plane = {}
    all_labels = set()
    for row in rows:
        label = row.get("representation_id")
        source = row.get("lineage")
        if not isinstance(label, str) or not label or label in all_labels or not isinstance(source,dict):
            raise ValueError("source tile representation identities invalid or reused")
        all_labels.add(label)
        plane_sha = source["source_4bpp_index_sha256"]
        tiles = source["entries"]
        if (digest(source["_indices"]) != plane_sha or
                digest(source["_touched"]) != source["source_tile_written_sha256"]):
            raise ValueError("source indices changed after tile lineage")
        # Asset content, position and pixel index must remain immutable for a
        # given index-plane SHA, even across different palette colourways.
        shape = tuple((t["row"],t["column"],t["source_tile_sha256"]) for t in tiles)
        frozen = by_plane.setdefault(plane_sha, {
            "shape":shape, "rows":[], "tile_hashes":set(),
            "opaque_tile_hashes":set()})
        if frozen["shape"] != shape:
            raise ValueError("identical source index plane has conflicting 8x8 tile bytes")
        frozen["rows"].append(label)
        frozen["tile_hashes"].update(x[2] for x in shape)
        frozen["opaque_tile_hashes"].update(t["source_tile_sha256"]
                                            for t in tiles if t["opaque_pixels"])
    tile_poses = defaultdict(set)
    tile_slots = defaultdict(set)
    for plane, rec in by_plane.items():
        for row,col,asset in rec["shape"]:
            tile_slots[asset].add((row,col))
            if asset in rec["opaque_tile_hashes"]:
                tile_poses[asset].add(plane)
    source_pairs = []
    keys = sorted(by_plane)
    for i, left in enumerate(keys):
        for right in keys[i+1:]:
            same = by_plane[left]["opaque_tile_hashes"] & by_plane[right]["opaque_tile_hashes"]
            if same:
                source_pairs.append({
                    "left_source_index_sha256":left,"right_source_index_sha256":right,
                    "shared_nonblank_exact_tile_contents":len(same)})
    unique_tiles = sorted(tile_slots)
    return {
        "schema":SCHEMA,
        "original_source_representations":len(rows),
        "unique_original_index_planes":len(keys),
        "unique_exact_8x8_tile_payloads":len(unique_tiles),
        "exact_nonblank_tile_payloads_reused_in_multiple_source_planes":
            sum(len(poses)>1 for poses in tile_poses.values()),
        "tile_payloads_observed_at_multiple_source_slots":
            sum(len(slots)>1 for slots in tile_slots.values()),
        "distinct_original_pose_pairs_with_shared_nonblank_8x8_tiles":len(source_pairs),
        "per_original_index_plane":{
            key:{
                "representation_count":len(by_plane[key]["rows"]),
                "original_representation_ids":sorted(by_plane[key]["rows"]),
                "source_tile_slots":len(by_plane[key]["shape"]),
                "distinct_nonblank_tile_contents":len(by_plane[key]["opaque_tile_hashes"]),
            } for key in keys
        },
        "shared_exact_opaque_tile_pairs":source_pairs,
        "original_live_PPU_capture_verified":False,
        "original_animation_sequence_verified":False,
        "original_1994_anatomical_part_correspondence_verified":False,
        "original_3d_geometry_recovered":False,
        "owner_likeness_approved":False,
    }


def produce(rom_path: Path, registry_path: Path, source_zip: Path) -> dict:
    """Require the complete earlier authenticated source producer as a gate."""
    from tools.art.audit_original_racer_palette_indices import (
        original_source_audit, composition_for_registry_entry,
        rasterize_composed_palette_indices)
    from tools.extract_racer_presentation_family import piece_source_tile
    original = original_source_audit(rom_path, registry_path, source_zip)
    if (original["registered_original_representations"] != 59 or
            original["unique_source_RGBA_images"] != 41 or
            original["unique_source_binary_silhouettes"] != 35):
        raise ValueError("not the authenticated 59/41/35 source ROM corpus")
    rom = rom_path.read_bytes()
    registry = json.loads(registry_path.read_bytes())["entries"]
    entries = {x["representation_id"]:x for x in registry}
    rows = []
    for audit in original["per_original_representation"]:
        identity = audit["registered_original_representation_id"]
        entry = entries[identity]
        player = entry["player"]
        composition = composition_for_registry_entry(rom,entry)
        lineage = compose_tile_lineage(
            composition,player,lambda word:piece_source_tile(rom,word))
        independent,touched = rasterize_composed_palette_indices(
            rom,composition,player,return_touched=True)
        if (lineage["_indices"] != independent or
                lineage["_touched"] != touched or
                lineage["source_4bpp_index_sha256"] != audit["original_4bpp_index_plane_sha256"] or
                lineage["source_tile_written_sha256"] != audit["original_4bpp_tile_written_mask_sha256"]):
            raise ValueError("8x8 provenance disagrees with authenticated original 4bpp raster")
        rows.append({"representation_id":identity,"lineage":lineage})
    result = summarize_lineages(rows)
    if result["unique_original_index_planes"] != 35 or result["original_source_representations"] != 59:
        raise ValueError("original source tile lineage cohort changed")
    result.update({
        "source_rom_sha256": original["original_USA_ROM_sha256"],
        "source_registry_sha256": original["original_registry_sha256"],
        "source_manifest_sha256":original["canonical_original_source_corpus_sha256"],
        "source_verified_original_4bpp_png_roundtrips":True,
    })
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom",type=Path,required=True)
    parser.add_argument("--registry",type=Path,required=True)
    parser.add_argument("--source-zip",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    opts=parser.parse_args()
    report=produce(opts.rom,opts.registry,opts.source_zip)
    from tools.art.no_replace_report import publish_text_once
    publish_text_once(opts.out,json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in
                      ("per_original_index_plane","shared_exact_opaque_tile_pairs")},
                     sort_keys=True,indent=2))


if __name__=="__main__":
    main()
