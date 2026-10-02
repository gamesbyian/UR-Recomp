#!/usr/bin/env python3
"""Recover the course resource descriptor/copy helper island across preserved ROM builds."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset, offset_to_cpu

ROMS = {
    "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
    "pal-prototype-1994-11-29": ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
    "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
    "legacy-beta": ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
OUTJ = ROOT / "analysis/generated/course-resource-descriptor-structure-island.json"
OUTM = ROOT / "analysis/generated/course-resource-descriptor-structure-island.md"

REGIONS = [
    ("stream_byte_reader", "82:B293", "82:B2A8"),
    ("descriptor_long_entry", "82:B2A9", "82:B2AC"),
    ("descriptor_decode", "82:B2AD", "82:B2D9"),
    ("wram_port_copy", "82:B2DA", "82:B32E"),
]

def best_shift(src: bytes, dst: bytes, start: int, end: int, radius: int = 128):
    block = src[start:end+1]
    best = (0, -1.0)
    for shift in range(-radius, radius + 1):
        lo = start + shift
        hi = lo + len(block)
        if lo < 0 or hi > len(dst):
            continue
        score = sum(a == b for a, b in zip(block, dst[lo:hi])) / len(block)
        if score > best[1]:
            best = (shift, score)
    return best

def roles(d, start: int, end: int):
    op = param = other = 0
    for pos in range(start, end + 1):
        role = d.code_map[pos]
        if role & d.OP_CODE:
            op += 1
        elif role & d.OP_PARAM:
            param += 1
        else:
            other += 1
    return {"opcode_bytes": op, "operand_bytes": param, "unreached_or_data_bytes": other}

def build(root: Path = ROOT):
    paths = {k: root / p.relative_to(ROOT) for k, p in ROMS.items()}
    blobs = {k: p.read_bytes() for k, p in paths.items()}
    usa = blobs["usa-retail"]

    align = {}
    for build, blob in blobs.items():
        align[build] = {}
        for name, start, end in REGIONS:
            us, ue = cpu_to_offset(start), cpu_to_offset(end)
            shift, sim = (0, 1.0) if build == "usa-retail" else best_shift(usa, blob, us, ue)
            align[build][name] = {"shift": shift, "similarity": round(sim, 6)}

    analyzers = {}
    for build, blob in blobs.items():
        d = trace(blob)
        # Seed public long entries and the tiny local helpers. Their bodies contain
        # the mode-setting instructions needed by the copy path; the byte-reader
        # is also called directly from the copy loop.
        seeds = [
            cpu_to_offset("82:B293") + align[build]["stream_byte_reader"]["shift"],
            cpu_to_offset("82:B2A9") + align[build]["descriptor_long_entry"]["shift"],
            cpu_to_offset("82:B2DA") + align[build]["wram_port_copy"]["shift"],
        ]
        seed_entries(d, seeds)
        analyzers[build] = d

    rows = []
    for name, start, end in REGIONS:
        us, ue = cpu_to_offset(start), cpu_to_offset(end)
        row = {"name": name, "kind": "code", "usa_start": start, "usa_end": end, "size": ue-us+1, "builds": {}}
        for build, blob in blobs.items():
            shift = align[build][name]["shift"]
            bs, be = us + shift, ue + shift
            item = {
                "start": offset_to_cpu(bs),
                "end": offset_to_cpu(be),
                "shift": shift,
                "similarity": align[build][name]["similarity"],
                "sha256": hashlib.sha256(blob[bs:be+1]).hexdigest(),
                **roles(analyzers[build], bs, be),
            }
            if build != "usa-retail":
                usa_d = analyzers["usa-retail"]
                other_d = analyzers[build]
                pairs = equal = disagreements = 0
                for pos in range(us, ue + 1):
                    a = usa_d.code_map[pos]
                    b = other_d.code_map[pos + shift]
                    if bool(a & usa_d.OP_CODE) != bool(b & other_d.OP_CODE) or bool(a & usa_d.OP_PARAM) != bool(b & other_d.OP_PARAM):
                        disagreements += 1
                    if a & usa_d.OP_CODE and b & other_d.OP_CODE:
                        pairs += 1
                        if usa[pos] == blob[pos + shift]:
                            equal += 1
                item.update({
                    "aligned_opcode_pairs": pairs,
                    "aligned_equal_opcode_pairs": equal,
                    "aligned_role_disagreements": disagreements,
                })
            row["builds"][build] = item
        rows.append(row)

    return {
        "schema_version": 1,
        "island": "CourseResourceDescriptorAndWramPortCopy",
        "usa_start": "82:B293",
        "usa_end": "82:B32E",
        "next_region": "82:B32F",
        "boundary_basis": {
            "entry": "course materialization directly JSLs 82:B2A9 and 82:B2DA",
            "internal_helpers": "82:B2A9 and 82:B2DA both converge on descriptor decoder 82:B2AD; copy loop calls stream reader 82:B293",
            "exit": "82:B31F and 82:B32E are RTL exits; 82:B32F begins the following table/data block in the preserved listing",
        },
        "relationship": {
            "caller": "course-materialization",
            "caller_sites": ["82:E18C -> 82:B2DA", "82:E1F5 -> 82:B2A9"],
            "descriptor_record_stride": 5,
            "copy_destination": "SNES WRAM data port $2180 with address registers $2181..$2183",
            "decompression_selector": "descriptor flag $4D == $80",
            "decompression_target": "81:B8F1",
            "decompression_semantics": "map/resource decompressor; selected by CMP #$80 / BEQ before the direct WRAM-port path",
        },
        "regions": rows,
    }

def render(r):
    lines = [
        "# Course resource descriptor / WRAM-port copy structural island", "",
        "USA `82:B293..B32E` is the compact helper cluster called by the recovered course loader. It parses five-byte resource descriptors through DP pointer `$4F`, exposes descriptor length/source metadata through `$4B/$4D`, and copies the selected stream through the SNES WRAM data port `$2180`.", "",
        "| Region | Size | USA | PAL prototype | Europe | Legacy beta |",
        "|---|---:|---|---|---|---|",
    ]
    for region in r["regions"]:
        def cell(build):
            b = region["builds"][build]
            return f"{b['start']}..{b['end']} ({b['shift']:+d}; sim {b['similarity']:.3f}; op {b['opcode_bytes']}; other {b['unreached_or_data_bytes']})"
        lines.append(f"| {region['name']} | {region['size']} | {cell('usa-retail')} | {cell('pal-prototype-1994-11-29')} | {cell('europe-retail')} | {cell('legacy-beta')} |")
    lines += ["", "## Structural interpretation", "",
        "- `82:B2A9` is a long-entry wrapper over the shared descriptor decoder at `82:B2AD`.",
        "- The decoder indexes a five-byte descriptor record, returns one byte in A, a word through Y, stores a word in DP `$4B`, and preserves the descriptor high-bit flag in DP `$4D`.",
        "- `82:B2DA` saves the caller's WRAM destination, reuses the same descriptor decoder, programs `$2181..$2183`, and emits `$4B` bytes through `$2180` using the stream reader at `82:B293`.",
        "- The selector is exact: `82:B2F6 CMP #$80; BEQ $B320` tests DP `$4D`, so `$4D == $80` diverts to `81:B8F1`, the preserved map/resource decompressor. Other descriptor values continue through the direct WRAM-port path.",
        "- `82:B32F` is intentionally excluded: the preserved disassembly immediately changes character into table/data-like bytes.",
        "", "This is a bounded structural result. The names describe observed dataflow and hardware effects, not a claim that every descriptor field's game-level meaning is known.", ""]
    return "\n".join(lines)

def main():
    r = build()
    OUTJ.write_text(json.dumps(r, indent=2) + "\n")
    OUTM.write_text(render(r))
    print(render(r))
    print("COURSE_RESOURCE_DESCRIPTOR_JSON=" + json.dumps(r, sort_keys=True))

if __name__ == "__main__":
    main()
