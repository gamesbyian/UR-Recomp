#!/usr/bin/env python3
"""Recover PAL per-racer course-contact register addresses without USA assumptions.

Anchors the first bank-82 frame-dispatch transfer to the independently
aligned, opcode-identical snes2asm course/player marshal prefix. Decode
operands *from the selected ROM*, then look for coherent P2 and bank-81
round-trip transfers. Ambiguous or absent matches remain unproven.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_europe_usa_snes2asm_homologs import cpu_to_offset

ROOT = Path(__file__).resolve().parents[1]
USA = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
BETA = ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc"
PROTOTYPE = ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"
EUROPE = ROOT / "reference/roms/retail/Unirally_Europe.sfc"
PROTO_ALIGN = ROOT / "analysis/generated/usa-pal-prototype-snes2asm-homologs.json"
EUROPE_ALIGN = ROOT / "analysis/generated/europe-usa-snes2asm-homologs.json"

# A single independently homolog-aligned executable region provides the
# bank-82 P1 entry location. No PAL WRAM operand addresses are hardcoded.
P1_ENTRY_CPU = "82:89BB"
P2_ENTRY_CPU = "82:8EC3"
MARSHAL_USA = {
    "p1_enter": "81:8D48", "p1_exit": "81:8DF3",
    "p2_enter": "81:8EA2", "p2_exit": "81:8F47",
}


def u16(data: bytes, i: int) -> int:
    return data[i] | (data[i + 1] << 8)


def read_transfer(rom: bytes, offset: int) -> dict | None:
    """Accept only a contiguous absolute LDY/absolute STY instruction pair."""
    if not 0 <= offset <= len(rom) - 6:
        return None
    if rom[offset] != 0xAC or rom[offset + 3] != 0x8C:
        return None
    return {
        "source": u16(rom, offset + 1),
        "destination": u16(rom, offset + 4),
        "bytes": rom[offset:offset + 6].hex(),
    }


def locate_transfer(rom: bytes, usa_site: str, shift: int,
                    source: int, destination: int,
                    radius: int = 256) -> dict:
    """Require unique exact inferred operands near the corresponding region."""
    base = cpu_to_offset(usa_site) + shift
    lo, hi = max(0, base - radius), min(len(rom) - 6, base + radius)
    hits = []
    for off in range(lo, hi + 1):
        candidate = read_transfer(rom, off)
        if (candidate is not None
                and candidate["source"] == source
                and candidate["destination"] == destination):
            hits.append(off)
    return {
        "usa_site": usa_site,
        "searched_near_shift": shift,
        "matches": [f"{off:06X}" for off in hits],
        "unambiguous": len(hits) == 1,
    }


def independent_prefix_shift(path: Path, build: str) -> int:
    if build == "usa-retail" or build == "legacy-beta":
        return 0
    alignment = json.loads(path.read_text(encoding="utf-8"))
    region = next(
        item for item in alignment["regions"]
        if item["name"] == "Race_UpdateRacersFrame:state_marshal_prefix"
    )
    if region["aligned_opcode_byte_disagreements"] != 0:
        raise ValueError("aligned race-frame prefix has opcode disagreements")
    if region["aligned_role_disagreements"] != 0:
        raise ValueError("aligned race-frame prefix has role disagreements")
    return (
        int(region["prototype_shift"])
        if build == "pal-prototype-1994-11-29"
        else int(region["europe_shift"])
    )


def inspect_build(rom: bytes, build: str, shift: int) -> dict:
    anchor = cpu_to_offset(P1_ENTRY_CPU) + shift
    transfer = read_transfer(rom, anchor)
    if transfer is None:
        return {
            "build": build, "aligned_shift": shift,
            "status": "unresolved_opcode_pair_at_aligned_entry",
            "candidate": None,
        }
    # This proves the first aligned entry's operand contents, not the
    # interpretation of the surrounding player update in every mode.
    p1, scratch = transfer["source"], transfer["destination"]
    p2 = p1 + 2
    p2_lookup = locate_transfer(rom, P2_ENTRY_CPU, shift, p2, scratch)
    entry = {
        "aligned_p1_cpu": P1_ENTRY_CPU,
        "aligned_p1_file_offset": f"{anchor:06X}",
        **transfer,
    }
    round_trips = {}
    for name, site in MARSHAL_USA.items():
        if name.endswith("enter"):
            source = p1 if name.startswith("p1") else p2
            destination = scratch
        else:
            source = scratch
            destination = p1 if name.startswith("p1") else p2
        round_trips[name] = locate_transfer(
            rom, site, shift, source, destination
        )
    fully_correlated = (
        p2_lookup["unambiguous"]
        and all(item["unambiguous"] for item in round_trips.values())
    )
    return {
        "build": build,
        "aligned_shift": shift,
        "status": (
            "unique_structural_transfer_correspondence"
            if fully_correlated else "partial_or_ambiguous_correspondence"
        ),
        "candidate": {
            "p1_backing": p1, "p2_backing_candidate": p2,
            "shared_current_player": scratch,
        },
        "p1_entry": entry,
        "p2_entry": p2_lookup,
        "bank81_round_trips": round_trips,
        "guardrail": (
            "Opcode agreement and source/destination coherence do not "
            "establish per-frame execution in PAL runtime. A guest trace "
            "must confirm identity, update order and event behavior."
        ),
    }


def build_report() -> dict:
    items = []
    for name, rom_path, align in (
        ("usa-retail", USA, PROTO_ALIGN),
        ("legacy-beta", BETA, PROTO_ALIGN),
        ("pal-prototype-1994-11-29", PROTOTYPE, PROTO_ALIGN),
        ("europe-retail", EUROPE, EUROPE_ALIGN),
    ):
        shift = independent_prefix_shift(align, name)
        items.append(inspect_build(rom_path.read_bytes(), name, shift))
    return {
        "schema_version": 1,
        "scope": "ROM-aligned course collision register transfer operands",
        "builds": items,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = build_report()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
