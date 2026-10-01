#!/usr/bin/env python3
"""Probe the two post-prototype WRAM insertion brackets using trusted code operands.

This is intentionally narrow. It scans only instructions reached after trusted
entry seeding and reports absolute 16-bit operands inside the two bracket ranges.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import json

from compare_europe_usa_snes2asm_homologs import ROOT, trace, seed_entries, cpu_to_offset
from compare_semantic_anchors import build_output

ROMS = {
    "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
    "pal-prototype-1994-11-29": ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
    "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
}

OUT_JSON = ROOT / "analysis/generated/wram-insertion-bracket-probe.json"
OUT_MD = ROOT / "analysis/generated/wram-insertion-bracket-probe.md"

MIN_SEED_SIMILARITY = 0.60

BRACKETS = {
    "first_plus4": (0x026A, 0x030D),
    "second_plus2": (0x04FB, 0x0541),
}

FOCUSED_NEIGHBORHOODS = {
    "first_inserted_space": (0x030A, 0x0310),
    "second_inserted_space": (0x053C, 0x0546),
    "autojoy_hardware_registers": (0x4218, 0x421F),
}


def trusted_seed_map(corpus: dict) -> dict[str, list[str]]:
    """Use every accepted semantic anchor as a reachability seed."""
    seeds = {name: [] for name in ROMS}
    for anchor in corpus["anchors"]:
        seeds["usa-retail"].append(anchor["usa_cpu_address"])
        for build in ("pal-prototype-1994-11-29", "europe-retail"):
            matches = anchor["matches"].get(build, [])
            if not matches:
                continue
            top = matches[0]
            if top["byte_similarity"] >= MIN_SEED_SIMILARITY:
                seeds[build].append(top["cpu_address"])
    return {name: sorted(set(values)) for name, values in seeds.items()}



def trusted_europe_projection_targets(corpus: dict) -> set[str]:
    """Collect Europe operand targets already explained by accepted projections."""
    out: set[str] = set()
    for anchor in corpus["anchors"]:
        matches = anchor["matches"].get("europe-retail", [])
        if not matches:
            continue
        top = matches[0]
        if top["byte_similarity"] < MIN_SEED_SIMILARITY:
            continue
        for projection in top["semantic_word_projection"].values():
            out.add(projection["dominant_candidate"])
    return out


def scan_operands(blob: bytes, disassembler, lo: int, hi: int) -> list[dict]:
    out = []
    # snes2asm marks opcode bytes and operand bytes. For 3-byte absolute ops,
    # take the two operand bytes following a reached opcode and interpret LE16.
    for off in range(0, len(blob) - 2):
        role = disassembler.code_map[off]
        if not (role & disassembler.OP_CODE):
            continue
        if not (disassembler.code_map[off + 1] & disassembler.OP_PARAM):
            continue
        if not (disassembler.code_map[off + 2] & disassembler.OP_PARAM):
            continue
        value = blob[off + 1] | (blob[off + 2] << 8)
        if lo <= value <= hi:
            out.append({
                "file_offset": off,
                "opcode": f"{blob[off]:02X}",
                "operand": f"{value:04X}",
                "operand_bytes": blob[off + 1:off + 3].hex(" "),
            })
    return out


def build() -> dict:
    corpus = build_output()
    seeds = trusted_seed_map(corpus)
    explained_europe = trusted_europe_projection_targets(corpus)
    builds = {}
    for name, path in ROMS.items():
        blob = path.read_bytes()
        d = trace(blob)
        seed_entries(d, [cpu_to_offset(x) for x in seeds[name]])
        per = {}
        for bracket, (lo, hi) in {**BRACKETS, **FOCUSED_NEIGHBORHOODS}.items():
            hits = scan_operands(blob, d, lo, hi)
            counts = Counter(h["operand"] for h in hits)
            per[bracket] = {
                "range": [f"{lo:04X}", f"{hi:04X}"],
                "reference_count": len(hits),
                "operand_counts": dict(sorted(counts.items())),
                "hits": hits,
            }
        builds[name] = per

    exclusive = {}
    for neighborhood in FOCUSED_NEIGHBORHOODS:
        usa = set(builds["usa-retail"][neighborhood]["operand_counts"])
        proto = set(builds["pal-prototype-1994-11-29"][neighborhood]["operand_counts"])
        europe = set(builds["europe-retail"][neighborhood]["operand_counts"])
        numeric_only = europe - usa - proto
        exclusive[neighborhood] = {
            "europe_only_numeric_operands": sorted(numeric_only),
            "explained_by_trusted_projection": sorted(numeric_only & explained_europe),
            "unexplained_europe_operands": sorted(numeric_only - explained_europe),
            "shared_all_three": sorted(europe & usa & proto),
            "europe_operands": sorted(europe),
        }

    return {
        "schema_version": 2,
        "method": {
            "reachability": "all accepted semantic-anchor top matches seeded into vendored snes2asm",
            "minimum_seed_similarity": MIN_SEED_SIMILARITY,
            "scope": "absolute-looking 16-bit operands inside the two inferred WRAM insertion brackets",
            "caveat": "operand presence is structural evidence, not semantic identity by itself",
        },
        "seed_counts": {name: len(values) for name, values in seeds.items()},
        "builds": builds,
        "focused_exclusivity": exclusive,
    }


def render(report: dict) -> str:
    lines = [
        "# WRAM insertion-bracket operand probe",
        "",
        "Narrow trusted-code scan for absolute 16-bit operands inside the two post-prototype WRAM insertion brackets.",
        "",
    ]
    for bracket, bounds in {**BRACKETS, **FOCUSED_NEIGHBORHOODS}.items():
        lines += [f"## {bracket} {bounds[0]:04X}..{bounds[1]:04X}", ""]
        for build, data in report["builds"].items():
            x = data[bracket]
            ops = ", ".join(f"`{k}`×{v}" for k, v in x["operand_counts"].items()) or "none"
            lines.append(f"- **{build}:** {x['reference_count']} references; {ops}")
        if bracket in report["focused_exclusivity"]:
            ex = report["focused_exclusivity"][bracket]
            numeric_only = ", ".join(f"`{x}`" for x in ex["europe_only_numeric_operands"]) or "none"
            explained = ", ".join(f"`{x}`" for x in ex["explained_by_trusted_projection"]) or "none"
            unexplained = ", ".join(f"`{x}`" for x in ex["unexplained_europe_operands"]) or "none"
            lines.append(f"- Europe-only numeric operands in trusted code: {numeric_only}")
            lines.append(f"- Explained by trusted relocation projection: {explained}")
            lines.append(f"- **Unexplained Europe operands:** {unexplained}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build()
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(report), encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8"))
    print("BRACKET_JSON=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
