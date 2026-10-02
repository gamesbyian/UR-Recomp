#!/usr/bin/env python3
"""Build a presentation-facing spatial/resource contract for Dragster."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from analyze_course_resource_lists import parse_course_resource_list
from analyze_rnc_streams import find_streams
from compare_europe_usa_snes2asm_homologs import cpu_to_offset
from rnc_method1 import unpack_method1

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
LANDMARKS = ROOT / "analysis/generated/dessyreqt-course-landmarks.json"
JSON_OUT = ROOT / "analysis/generated/dragster-presentation-spatial-contract.json"
MD_OUT = ROOT / "analysis/generated/dragster-presentation-spatial-contract.md"

COARSE_TABLE_BASE = 0x000F
FINE_TABLE_BASE = 0x800F
COARSE_TABLE_BYTES = FINE_TABLE_BASE - COARSE_TABLE_BASE
COARSE_ENTRY_BYTES = 2
FINE_RECORD_BYTES = 32
COARSE_WORLD_UNITS = 64
FINE_WORLD_UNITS = 16
RESOURCE_DESC_TABLE_CPU = "82:B7DA"
KNOWN_DRAGSTER_C000 = [0x00, 0x00, 0x12, 0x1C, 0x00, 0x00] + [0x14] * 9 + [0x02] * 5


def dim_value(raw: int) -> int:
    return 256 if raw == 0 else raw


def le16(data: bytes, off: int) -> int:
    return data[off] | (data[off + 1] << 8)


def descriptor(rom: bytes, rid: int) -> dict:
    base = cpu_to_offset(RESOURCE_DESC_TABLE_CPU)
    raw = rom[base + rid * 5 : base + rid * 5 + 5]
    size = raw[3] | (raw[4] << 8)
    return {
        "resource_id": rid,
        "resource_id_hex": f"{rid:02X}",
        "descriptor_bytes": raw.hex(" "),
        "source_bank": raw[0] & 0x7F,
        "source_offset": raw[1] | (raw[2] << 8),
        "special_or_compressed_flag": bool(raw[0] & 0x80),
        "size": size,
        "a000_span": size >> 2,
        "c000_span": size >> 7,
    }


def owner_for_slot(resources: list[dict], slot: int) -> dict | None:
    for item in resources:
        lo, hi = item["c000_range"]
        if lo <= slot <= hi:
            return item
    return None


def decode_surface_word(word: int, resources: list[dict]) -> dict:
    out = {
        "word": word,
        "word_hex": f"{word:04X}",
        "low10_nonzero": bool(word & 0x03FF),
        "control_bits_10_12": (word & 0x1C00) >> 10,
        "bit14": bool(word & 0x4000),
    }
    if not out["low10_nonzero"]:
        out.update({
            "kind": "special_or_empty",
            "c000_slot": None,
            "a000_range": None,
            "resource_id": None,
            "resource_id_hex": None,
        })
        return out

    # 81:8C11..8C2C derives X from the low ten bits, reads C000[X],
    # and uses X*32 as the paired A000 block base.
    slot = ((word & 0x000F) >> 1) + ((word & 0x03F0) >> 2)
    owner = owner_for_slot(resources, slot)
    out.update({
        "kind": "materialized_surface",
        "c000_slot": slot,
        "a000_range": [slot * 32, slot * 32 + 31],
        "resource_id": owner["resource_id"] if owner else None,
        "resource_id_hex": owner["resource_id_hex"] if owner else None,
    })
    return out


def row_runs(values: list[int]) -> list[dict]:
    runs = []
    start = 0
    for i in range(1, len(values) + 1):
        if i == len(values) or values[i] != values[start]:
            runs.append({
                "x_sector_start": start,
                "x_sector_end": i - 1,
                "record_id": values[start],
            })
            start = i
    return runs


def query_world_rect(contract: dict, rect: tuple[int, int, int, int]) -> dict:
    x0, y0, x1, y1 = rect
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    width, height = contract["world_contract"]["world_extent"]
    if not (0 <= x0 <= x1 < width and 0 <= y0 <= y1 < height):
        raise ValueError(
            f"query rectangle {rect} lies outside Dragster extent "
            f"0..{width - 1},0..{height - 1}"
        )

    coarse = contract["spatial_tables"]["coarse_sector_index"]
    fine = contract["spatial_tables"]["fine_record_table"]["records"]
    row_maps = {}
    for row in coarse["rows_rle"]:
        vals = {}
        for run in row["runs"]:
            for sx in range(run["x_sector_start"], run["x_sector_end"] + 1):
                vals[sx] = run["record_id"]
        row_maps[row["y_sector"]] = vals

    resources = set()
    records = set()
    cells = []
    for fy in range(y0 // 16, y1 // 16 + 1):
        for fx in range(x0 // 16, x1 // 16 + 1):
            sx, sy = fx // 4, fy // 4
            lx, ly = fx % 4, fy % 4
            rid = row_maps[sy][sx]
            cell = fine[rid]["cells"][ly * 4 + lx]
            records.add(rid)
            if cell["resource_id"] is not None:
                resources.add(cell["resource_id"])
            cells.append({
                "world_rect": [fx * 16, fy * 16, fx * 16 + 15, fy * 16 + 15],
                "coarse_sector": [sx, sy],
                "fine_record_id": rid,
                "local_cell": [lx, ly],
                "surface_word": cell["word"],
                "surface_word_hex": cell["word_hex"],
                "kind": cell["kind"],
                "c000_slot": cell["c000_slot"],
                "a000_range": cell["a000_range"],
                "resource_id": cell["resource_id"],
                "resource_id_hex": cell["resource_id_hex"],
            })
    return {
        "world_rect": [x0, y0, x1, y1],
        "fine_cell_count": len(cells),
        "fine_record_ids": sorted(records),
        "resource_ids": sorted(resources),
        "cells": cells,
    }


def build(query_rect: tuple[int, int, int, int] | None = None) -> dict:
    rom = ROM.read_bytes()
    streams = list(find_streams(rom))
    if len(streams) != 45:
        raise SystemExit(f"expected 45 validated RNC streams, got {len(streams)}")
    rom_off, packed, _ = streams[0]
    decoded = unpack_method1(packed)
    parsed = parse_course_resource_list(decoded)
    cursor = parsed["resource_cursor_initial"]

    raw_x, raw_y = decoded[13], decoded[14]
    dim_x, dim_y = dim_value(raw_x), dim_value(raw_y)
    coarse_cols = dim_x * 4
    coarse_rows = dim_y * 4
    coarse_count = coarse_cols * coarse_rows
    if coarse_count != COARSE_TABLE_BYTES // COARSE_ENTRY_BYTES:
        raise SystemExit(
            f"runtime grid {coarse_cols}x{coarse_rows}={coarse_count} "
            f"does not fill the fixed u16 sector table"
        )
    if cursor <= FINE_TABLE_BASE or (cursor - FINE_TABLE_BASE) % FINE_RECORD_BYTES:
        raise SystemExit("fine-record region does not end on a 32-byte boundary")

    resources = []
    a_cursor = c_cursor = 0
    for rid in parsed["resource_ids"]:
        item = descriptor(rom, rid)
        item["a000_range"] = [a_cursor, a_cursor + item["a000_span"] - 1]
        item["c000_range"] = [c_cursor, c_cursor + item["c000_span"] - 1]
        a_cursor += item["a000_span"]
        c_cursor += item["c000_span"]
        resources.append(item)
    if c_cursor != len(KNOWN_DRAGSTER_C000):
        raise SystemExit("descriptor-derived C000 size disagrees with runtime snapshot")

    coarse = [le16(decoded, COARSE_TABLE_BASE + i * 2) for i in range(coarse_count)]
    record_count = (cursor - FINE_TABLE_BASE) // FINE_RECORD_BYTES
    used_records = sorted(set(coarse))
    if not used_records or used_records[-1] >= record_count:
        raise SystemExit(
            f"sector table references record {used_records[-1] if used_records else 'none'} "
            f"but only {record_count} fine records exist"
        )

    fine_records = []
    invalid_slots = []
    for record_id in range(record_count):
        base = FINE_TABLE_BASE + record_id * FINE_RECORD_BYTES
        cells = []
        for cell_index in range(16):
            word = le16(decoded, base + cell_index * 2)
            cell = decode_surface_word(word, resources)
            if cell["kind"] == "materialized_surface" and cell["resource_id"] is None:
                invalid_slots.append((record_id, cell_index, cell["c000_slot"], word))
            cell["local_x"] = cell_index % 4
            cell["local_y"] = cell_index // 4
            cells.append(cell)
        fine_records.append({
            "record_id": record_id,
            "decoded_offset": base,
            "used_by_sector_table": record_id in used_records,
            "cells": cells,
        })
    if invalid_slots:
        raise SystemExit(f"normal surface words reference unmapped C000 slots: {invalid_slots[:8]}")

    record_sector_counts = Counter(coarse)
    coarse_rows_rle = []
    checkpoint_id = 0x24
    checkpoint_range = next(
        item["c000_range"] for item in resources if item["resource_id"] == checkpoint_id
    )
    checkpoint_records = {}
    for record in fine_records:
        matches = [
            {
                "local_x": cell["local_x"],
                "local_y": cell["local_y"],
                "c000_slot": cell["c000_slot"],
                "word_hex": cell["word_hex"],
            }
            for cell in record["cells"]
            if cell["resource_id"] == checkpoint_id
        ]
        if matches:
            checkpoint_records[record["record_id"]] = matches

    checkpoint_sector_placements = []
    for sy in range(coarse_rows):
        row = coarse[sy * coarse_cols : (sy + 1) * coarse_cols]
        coarse_rows_rle.append({"y_sector": sy, "runs": row_runs(row)})
        for sx, rid in enumerate(row):
            if rid in checkpoint_records:
                checkpoint_sector_placements.append({
                    "x_sector": sx,
                    "y_sector": sy,
                    "world_rect": [
                        sx * 64,
                        sy * 64,
                        (sx + 1) * 64 - 1,
                        (sy + 1) * 64 - 1,
                    ],
                    "record_id": rid,
                    "checkpoint_local_cells": checkpoint_records[rid],
                })

    lm = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    drag = next(t for t in lm["tracks"] if t["track_id"] == 0)
    spawn_x = parsed["spawn_or_landmark_a"][0] * 16
    spawn_y = parsed["spawn_or_landmark_a"][1] * 16

    result = {
        "schema_version": 2,
        "course": {
            "name": "Dragster",
            "stream_index": 1,
            "rom_offset": rom_off,
            "decoded_size": len(decoded),
            "header_raw_dims": [raw_x, raw_y],
            "header_dims": [dim_x, dim_y],
            "spawn_world": [spawn_x, spawn_y],
            "historical_finish_x_probe": drag["finish_x"],
        },
        "world_contract": {
            "coarse_sector_world_units": 64,
            "fine_cell_world_units": 16,
            "coarse_grid": [coarse_cols, coarse_rows],
            "world_extent": [coarse_cols * 64, coarse_rows * 64],
            "world_x_range": [0, coarse_cols * 64 - 1],
            "world_y_range": [0, coarse_rows * 64 - 1],
            "camera_wrap_or_clamp_masks": {
                "x_0D49": coarse_cols * 64 - 1,
                "y_0D47": coarse_rows * 64 - 1,
                "evidence": "81:A313..A51F configures 04F1/04F3 and 0D49/0D47 from 7F:000D",
            },
        },
        "spatial_tables": {
            "coarse_sector_index": {
                "decoded_base": COARSE_TABLE_BASE,
                "runtime_base": "7F:000F",
                "entry_type": "u16_le_fine_record_id",
                "entry_count": coarse_count,
                "byte_length": COARSE_TABLE_BYTES,
                "linear_index": "y_sector * coarse_width + x_sector",
                "used_record_ids": used_records,
                "record_sector_counts": {
                    str(k): record_sector_counts[k] for k in used_records
                },
                "rows_rle": coarse_rows_rle,
            },
            "fine_record_table": {
                "decoded_base": FINE_TABLE_BASE,
                "runtime_base": "7F:800F",
                "record_bytes": FINE_RECORD_BYTES,
                "record_count": record_count,
                "record_shape": [4, 4],
                "cell_type": "u16_le_packed_surface_word",
                "records": fine_records,
            },
        },
        "resources": {
            "tail_ids": parsed["resource_ids"],
            "resource_list_offset": cursor,
            "terminator_offset": parsed["resource_terminator_offset"],
            "a000_total": a_cursor,
            "c000_total": c_cursor,
            "entries": resources,
            "confirmed_c000_snapshot": KNOWN_DRAGSTER_C000,
            "checkpoint_finish": {
                "resource_id": checkpoint_id,
                "c000_range": checkpoint_range,
                "behavior_code": 0x14,
                "fine_record_ids": sorted(checkpoint_records),
                "coarse_sector_placement_count": len(checkpoint_sector_placements),
                "coarse_sector_placements": checkpoint_sector_placements,
            },
        },
        "validation": {
            "sector_lookup": "81:8A4A..8B94: (y>>6)*04F1 + (x>>6) indexes u16 at 7F:000F; value*32 indexes 7F:800F",
            "fine_selection": "81:8B65..8B8A: coordinate bits 4..5 select one of 16 u16 cells inside the 32-byte record",
            "surface_resource_lookup": "81:8C11..8CFD: packed word selects C000 slot and paired A000 32-byte block",
            "materialization": "resource descriptors append paired A000/C000 spans in tail-list order",
            "visual_corpus": "reference/imported/reverse-engineering/dessyreqt/Maps/01 Crawler/01 Dragster.png",
            "historical_landmarks": "analysis/generated/dessyreqt-course-landmarks.json (probe only)",
        },
        "stop_boundary": {
            "sufficient_for_dragster": [
                "world extent and camera masks",
                "64x64 coarse sector to 32-byte fine-record placement",
                "16x16 fine cell to packed surface word",
                "normal packed word to C000 slot, A000 block, and owning tail resource",
                "checkpoint-finish resource cells located in world sectors",
                "deterministic ROM-derived region query",
            ],
            "deliberately_open": [
                "packed control-bit semantics beyond the resource-selection path",
                "gameplay activation and liveness",
                "graphics extraction or replacement art",
                "editor-complete names for every packed field",
            ],
            "generalize_next": "Check the same two-level boundaries, dimension transform, and packed-word ownership invariant on a small cross-course sample before any 45-course census.",
        },
    }
    if query_rect is not None:
        result["query"] = query_world_rect(result, query_rect)
    return result


def render_md(result: dict) -> str:
    c = result["course"]
    w = result["world_contract"]
    s = result["spatial_tables"]
    res = result["resources"]
    lines = [
        "# Dragster presentation spatial/resource contract",
        "",
        "Generated by tools/build_course_presentation_contract.py. This is a Widescreen-facing contract, not an editor-complete course format.",
        "",
        "## World and camera extent",
        "",
        f"- Header dimensions {c['header_dims'][0]} x {c['header_dims'][1]} expand to a runtime coarse grid of {w['coarse_grid'][0]} x {w['coarse_grid'][1]} 64-unit sectors.",
        f"- Dragster world extent is {w['world_extent'][0]} x {w['world_extent'][1]} world units; X range is 0..{w['world_x_range'][1]:04X}, Y range is 0..{w['world_y_range'][1]:04X}.",
        f"- Camera configuration uses matching masks 0D49={w['camera_wrap_or_clamp_masks']['x_0D49']:04X} and 0D47={w['camera_wrap_or_clamp_masks']['y_0D47']:04X}.",
        f"- Spawn is {tuple(c['spawn_world'])}; the historical finish-X probe {c['historical_finish_x_probe']} falls inside this extent.",
        "",
        "## Two-level spatial lookup",
        "",
        f"1. 7F:000F / decoded 0x{s['coarse_sector_index']['decoded_base']:04X} is a {s['coarse_sector_index']['entry_count']}-entry u16 coarse-sector table, indexed as (y>>6) * width + (x>>6).",
        f"2. Each u16 value selects one of {s['fine_record_table']['record_count']} records at 7F:800F / decoded 0x{s['fine_record_table']['decoded_base']:04X} by multiplying the value by 32.",
        "3. Each 32-byte record is a 4x4 grid of u16 packed surface words, resolving the 64x64 sector to 16x16 world cells.",
        "4. For normal packed words, 81:8C11..8C2C derives a C000 slot; that slot identifies both the C000 behavior/orientation byte and the paired 32-byte A000 surface block.",
        "",
        "The earlier 33 x 1024 plane-major hypothesis is rejected. The 0x8000 boundary is a two-level indirection split.",
        "",
        "## Materialized resource ownership",
        "",
        "| ID | size | A000 range | C000 range |",
        "|---:|---:|---|---|",
    ]
    for item in res["entries"]:
        lines.append(
            f"| {item['resource_id_hex']} | 0x{item['size']:04X} | "
            f"{item['a000_range'][0]}..{item['a000_range'][1]} | "
            f"{item['c000_range'][0]}..{item['c000_range'][1]} |"
        )
    cp = res["checkpoint_finish"]
    lines += [
        "",
        f"Resource 0x24 owns C000 slots {cp['c000_range'][0]}..{cp['c000_range'][1]}; all nine are confirmed checkpoint/finish behavior code 0x14. Those slots occur in fine records {cp['fine_record_ids']} and in {cp['coarse_sector_placement_count']} coarse-sector placements.",
        "",
        "## Query contract",
        "",
        "Example: python3 tools/build_course_presentation_contract.py --query-rect 1088 768 1408 896",
        "",
        "The JSON result returns every touched 16x16 cell with coarse sector, fine-record ID, packed surface word, C000 slot, paired A000 range, and owning tail resource.",
        "",
        "## Stop boundary",
        "",
    ]
    lines += [f"- sufficient on Dragster: {x}" for x in result["stop_boundary"]["sufficient_for_dragster"]]
    lines += [f"- deliberately open: {x}" for x in result["stop_boundary"]["deliberately_open"]]
    lines += ["", result["stop_boundary"]["generalize_next"], ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path, default=JSON_OUT)
    ap.add_argument("--md-out", type=Path, default=MD_OUT)
    ap.add_argument("--query-rect", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    args = ap.parse_args()
    result = build(tuple(args.query_rect) if args.query_rect else None)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_md(result), encoding="utf-8")
    summary = {
        "course": result["course"],
        "world_contract": result["world_contract"],
        "used_record_ids": result["spatial_tables"]["coarse_sector_index"]["used_record_ids"],
        "resources": result["resources"]["tail_ids"],
        "checkpoint_sector_placement_count": result["resources"]["checkpoint_finish"]["coarse_sector_placement_count"],
        "query": result.get("query"),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
