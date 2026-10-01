#!/usr/bin/env python3
"""Verify regional racer-state semantics by bidirectional copy relationships.

Rather than promoting a relocated RAM address because it appears at the same
relative byte offset, this tool requires the regional Race_UpdateRacersFrame
candidate to preserve the semantic dataflow relation:

    persistent player slot -> current-player working slot -> persistent slot

for X velocity, Y velocity, and boost.
"""
from __future__ import annotations

from pathlib import Path
import json

try:
    from tools.compare_semantic_anchors import ROMS, cpu_to_lorom_file, file_to_lorom_cpu
except ModuleNotFoundError:
    from compare_semantic_anchors import ROMS, cpu_to_lorom_file, file_to_lorom_cpu

OUT_JSON = Path("analysis/generated/regional-racer-state-relations.json")
OUT_MD = Path("analysis/generated/regional-racer-state-relations.md")

BUILDS = {
    "usa-retail": {
        "routine": "82:89B9",
        "relations": {
            "Player1_XSpeed": ("04B7", "0F9F"),
            "Player1_YSpeed": ("04BB", "0FA1"),
            "Player1_BoostMeter": ("11CF", "11CD"),
        },
    },
    "pal-prototype-1994-11-29": {
        "routine": "82:89B6",
        "relations": {
            "Player1_XSpeed": ("04B7", "0FA3"),
            "Player1_YSpeed": ("04BB", "0FA5"),
            "Player1_BoostMeter": ("11D3", "11D1"),
        },
    },
    "europe-retail": {
        "routine": "82:89CC",
        "relations": {
            "Player1_XSpeed": ("04BB", "0FA9"),
            "Player1_YSpeed": ("04BF", "0FAB"),
            "Player1_BoostMeter": ("11D9", "11D7"),
        },
    },
}


def word_bytes(word_hex: str) -> bytes:
    value = int(word_hex, 16)
    return bytes((value & 0xFF, value >> 8))


def find_seq(region: bytes, pattern: bytes, base: int) -> list[dict]:
    out=[]
    pos=region.find(pattern)
    while pos >= 0:
        absolute=base+pos
        out.append({"file_offset": absolute, "cpu": file_to_lorom_cpu(absolute)})
        pos=region.find(pattern, pos+1)
    return out


def relation_patterns(persistent: str, working: str) -> dict[str, bytes]:
    p=word_bytes(persistent)
    w=word_bytes(working)
    return {
        "copy_in_y": bytes((0xAC,)) + p + bytes((0x8C,)) + w,
        "copy_out_y": bytes((0xAC,)) + w + bytes((0x8C,)) + p,
        "copy_in_a": bytes((0xAD,)) + p + bytes((0x8D,)) + w,
        "copy_out_a": bytes((0xAD,)) + w + bytes((0x8D,)) + p,
    }


def inspect_build(blob: bytes, spec: dict) -> dict:
    start=cpu_to_lorom_file(spec['routine'])
    size=0x520
    region=blob[start:start+size]
    relations={}
    for name,(persistent,working) in spec['relations'].items():
        hits={k: find_seq(region,p,start) for k,p in relation_patterns(persistent,working).items()}
        copy_in=hits['copy_in_y'] + hits['copy_in_a']
        copy_out=hits['copy_out_y'] + hits['copy_out_a']
        relations[name]={
            "persistent": f"7E:{persistent}",
            "working": f"7E:{working}",
            "copy_in": copy_in,
            "copy_out": copy_out,
            "copy_in_count": len(copy_in),
            "copy_out_count": len(copy_out),
            "bidirectional": bool(copy_in and copy_out),
            "patterns": hits,
        }
    return {
        "routine": spec["routine"],
        "relations": relations,
        "all_bidirectional": all(r["bidirectional"] for r in relations.values()),
    }


def build_report() -> dict:
    blobs={name:path.read_bytes() for name,path in ROMS.items()}
    return {
        "schema_version": 1,
        "method": "exact local 65816 absolute load/store dataflow pairs inside matched Race_UpdateRacersFrame windows",
        "builds": {name: inspect_build(blobs[name], spec) for name,spec in BUILDS.items()},
    }


def render_md(r: dict) -> str:
    lines=[
        "# Regional racer-state copy relations",
        "",
        "A relation is promoted only when the matched racer-update routine contains both a persistent→working copy and a working→persistent copy for the proposed build-specific addresses.",
        "",
        "| Build | Semantic field | Persistent | Working | Copy in | Copy out | Bidirectional |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for build,b in r["builds"].items():
        for name,rel in b["relations"].items():
            lines.append(
                f"| {build} | {name} | `{rel['persistent']}` | `{rel['working']}` | "
                f"{rel['copy_in_count']} | {rel['copy_out_count']} | {'yes' if rel['bidirectional'] else 'no'} |"
            )
    lines += [
        "",
        "Exact instruction edges are stronger evidence than same-offset operand projection: they preserve the named field’s role in the marshal→simulate→writeback pipeline.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report=build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    print(OUT_MD.read_text())
    return 0 if all(x['all_bidirectional'] for x in report['builds'].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
