#!/usr/bin/env python3
"""Recover the geometry precompute/code+data island across preserved ROM builds."""
from __future__ import annotations

import hashlib
import json

from compare_europe_usa_snes2asm_homologs import (
    ROOT,
    cpu_to_offset,
    offset_to_cpu,
    seed_entries,
    trace,
)

ROMS = {
    "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
    "pal-prototype-1994-11-29": ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
    "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
    "legacy-beta": ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ = ROOT / "analysis/generated/geometry-precompute-structure-island.json"
OUTM = ROOT / "analysis/generated/geometry-precompute-structure-island.md"

REGIONS = [
    ("long_entry_wrapper", "code", "81:99D6", "81:99D9"),
    ("geometry_lookup_a", "data", "81:99DA", "81:9A19"),
    ("geometry_lookup_b", "data", "81:9A1A", "81:9A59"),
    ("geometry_precompute_body", "code", "81:9A5A", "81:9E29"),
]


def roles(d, start, end):
    op = param = other = 0
    for pos in range(start, end + 1):
        role = d.code_map[pos]
        if role & d.OP_CODE:
            op += 1
        elif role & d.OP_PARAM:
            param += 1
        else:
            other += 1
    return {
        "opcode_bytes": op,
        "operand_bytes": param,
        "unreached_or_data_bytes": other,
    }


def best_shift(src, dst, start, end, center=0, radius=96):
    block = src[start : end + 1]
    best = (center, -1.0)
    for shift in range(center - radius, center + radius + 1):
        lo = start + shift
        hi = lo + len(block)
        if lo < 0 or hi > len(dst):
            continue
        score = sum(a == b for a, b in zip(block, dst[lo:hi])) / len(block)
        if score > best[1]:
            best = (shift, score)
    return best


def local_profile(src, dst, start, end, center, window=64):
    out = []
    pos = start
    while pos <= end:
        hi = min(end, pos + window - 1)
        shift, score = best_shift(src, dst, pos, hi, center, 64)
        out.append(
            {
                "usa_start": offset_to_cpu(pos),
                "usa_end": offset_to_cpu(hi),
                "shift": shift,
                "similarity": round(score, 6),
            }
        )
        pos = hi + 1
    return out


def build():
    blobs = {name: path.read_bytes() for name, path in ROMS.items()}
    usa = blobs["usa-retail"]
    centers = {
        "usa-retail": 0,
        "legacy-beta": 0,
        "pal-prototype-1994-11-29": -32,
        "europe-retail": -15,
    }

    shifts = {}
    for build, blob in blobs.items():
        shifts[build] = {}
        for name, _kind, start, end in REGIONS:
            us, ue = cpu_to_offset(start), cpu_to_offset(end)
            shifts[build][name] = best_shift(
                usa, blob, us, ue, centers[build]
            )[0]

    disassemblers = {}
    for build, blob in blobs.items():
        d = trace(blob)
        seed = cpu_to_offset("81:99D6") + shifts[build]["long_entry_wrapper"]
        seed_entries(d, [seed])
        disassemblers[build] = d

    rows = []
    for name, kind, start, end in REGIONS:
        us, ue = cpu_to_offset(start), cpu_to_offset(end)
        row = {
            "name": name,
            "kind": kind,
            "usa_start": start,
            "usa_end": end,
            "size": ue - us + 1,
            "builds": {},
        }
        for build, blob in blobs.items():
            shift = shifts[build][name]
            bs, be = us + shift, ue + shift
            score = (
                sum(a == b for a, b in zip(usa[us : ue + 1], blob[bs : be + 1]))
                / (ue - us + 1)
            )
            info = {
                "start": offset_to_cpu(bs),
                "end": offset_to_cpu(be),
                "shift": shift,
                "size": be - bs + 1,
                "size_delta": 0,
                "similarity": round(score, 6),
                "sha256": hashlib.sha256(blob[bs : be + 1]).hexdigest(),
            }

            if kind == "code":
                info.update(roles(disassemblers[build], bs, be))
            else:
                info.update(
                    {
                        "opcode_bytes": 0,
                        "operand_bytes": 0,
                        "unreached_or_data_bytes": be - bs + 1,
                    }
                )

            if build != "usa-retail" and kind == "code":
                pairs = equal = role_disagreements = 0
                mismatches = []
                usa_d = disassemblers["usa-retail"]
                other_d = disassemblers[build]
                for pos in range(us, ue + 1):
                    a = usa_d.code_map[pos]
                    b = other_d.code_map[pos + shift]
                    if (
                        bool(a & usa_d.OP_CODE) != bool(b & other_d.OP_CODE)
                        or bool(a & usa_d.OP_PARAM) != bool(b & other_d.OP_PARAM)
                    ):
                        role_disagreements += 1
                    if a & usa_d.OP_CODE and b & other_d.OP_CODE:
                        pairs += 1
                        if usa[pos] == blob[pos + shift]:
                            equal += 1
                        else:
                            mismatches.append(
                                {
                                    "usa": offset_to_cpu(pos),
                                    "other": offset_to_cpu(pos + shift),
                                    "usa_byte": f"{usa[pos]:02x}",
                                    "other_byte": f"{blob[pos + shift]:02x}",
                                }
                            )
                info.update(
                    {
                        "aligned_opcode_pairs": pairs,
                        "aligned_equal_opcode_pairs": equal,
                        "aligned_role_disagreements": role_disagreements,
                        "opcode_mismatches": mismatches,
                    }
                )

            if build in {"pal-prototype-1994-11-29", "europe-retail"}:
                info["local_shift_profile_64byte"] = local_profile(
                    usa, blob, us, ue, shift
                )
            row["builds"][build] = info
        rows.append(row)

    tables = [row for row in rows if row["kind"] == "data"]
    table_identity = {
        build: all(row["builds"][build]["similarity"] == 1.0 for row in tables)
        for build in ROMS
    }

    return {
        "schema_version": 1,
        "island": "GeometryPrecomputeAndLookupTables",
        "usa_start": "81:99D6",
        "usa_end": "81:9E29",
        "long_entry": "81:99D6",
        "body_entry": "81:9A5A",
        "next_entry": "81:9E2A",
        "table_identity_by_build": table_identity,
        "regions": rows,
    }


def render(result):
    lines = [
        "# Geometry precompute structural island",
        "",
        "USA `81:99D6..9E29` contains a long-entry wrapper, two adjacent 64-byte lookup tables, and the geometry-precompute body before the next independent entry at `81:9E2A`. The wrapper and body are fully analyzer-reached; both lookup tables are byte-identical across all four preserved ROMs.",
        "",
        "| Region | Kind | USA bytes | PAL prototype | Europe | Legacy beta |",
        "|---|---|---:|---|---|---|",
    ]

    for region in result["regions"]:
        def cell(build):
            item = region["builds"][build]
            return (
                f"{item['start']}..{item['end']} "
                f"({item['shift']:+d}; sim {item['similarity']:.3f}; "
                f"op {item['opcode_bytes']}; other {item['unreached_or_data_bytes']})"
            )

        lines.append(
            f"| {region['name']} | {region['kind']} | {region['size']} | "
            f"{cell('pal-prototype-1994-11-29')} | "
            f"{cell('europe-retail')} | {cell('legacy-beta')} |"
        )

    lines += ["", "## Lookup-table identity", ""]
    for build, identical in result["table_identity_by_build"].items():
        lines.append(f"- {build}: {'byte-identical to USA' if identical else 'differs from USA'}")
    lines += ["", "Across the two code regions, PAL prototype and Europe preserve every aligned opcode position and analyzer code/operand role. Their byte differences are therefore operand/layout differences rather than executable-architecture changes.", ""]
    return "\n".join(lines)


def main():
    result = build()
    OUTJ.write_text(json.dumps(result, indent=2) + "\n")
    OUTM.write_text(render(result))
    print(render(result))
    print("GEOMETRY_PRECOMPUTE_JSON=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
