#!/usr/bin/env python3
"""Rank uncovered direct-call targets reached from the accepted structural census.

This is a prioritizer, not a coverage claim. It asks a narrow question:
which direct JSR/JSL destinations outside the census are called most often from
already-bounded code, remain easy to align across preserved builds, and sit on
shipping-relevant caller paths?
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path

from compare_europe_usa_snes2asm_homologs import (
    cpu_to_offset, offset_to_cpu, seed_entries, trace
)

ROOT = Path(__file__).resolve().parents[1]
ROMS = {
    "usa-retail": ROOT / "reference/roms/retail/Uniracers_USA.sfc",
    "pal-prototype-1994-11-29": ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc",
    "europe-retail": ROOT / "reference/roms/retail/Unirally_Europe.sfc",
    "legacy-beta": ROOT / "reference/roms/prototypes/Uniracers_Beta_legacy.sfc",
}
CENSUS = ROOT / "analysis/generated/comparative-structural-census.json"
OUTJ = ROOT / "analysis/generated/comparative-frontier-ranking.json"
OUTM = ROOT / "analysis/generated/comparative-frontier-ranking.md"

RELEVANCE = {
    "collision-resolution": 5, "contact-geometry": 5, "course-surface-sampler": 5,
    "racer-update": 5, "course-materialization": 5, "race-frame-orchestrator": 5,
    "racer-oam": 4, "camera-control": 4, "input-normalization": 4,
    "checkpoint-finish": 3, "race-timer": 3, "player-state-marshal": 4,
    "stunt-finalizer": 3, "stunt-message-pipeline": 2, "object-collision": 4,
}

# Preserved Nitrodon listings already explain a few high-fan-in targets as
# support plumbing. Keep them visible, but stop generic utility fan-in from
# crowding out unexplained gameplay/course/rendering structure.
DEPRIORITIZED = {
    "81:B68B": (30, "generic signed hardware-multiply helper"),
    "82:8000": (55, "APU command-ring enqueue service"),
    "82:8035": (35, "APU command-ring/port handshake service"),
    "83:F940": (25, "PPU/register reset and forced-blank setup"),
}

def in_census(off: int, intervals: list[tuple[int,int]]) -> bool:
    return any(a <= off <= b for a,b in intervals)

def direct_target(blob: bytes, off: int) -> tuple[str,int] | None:
    op = blob[off]
    bank = (off // 0x8000) | 0x80
    if op == 0x20 and off + 2 < len(blob):  # JSR abs
        addr = blob[off+1] | (blob[off+2] << 8)
        if addr >= 0x8000:
            return ("JSR", cpu_to_offset(f"{bank:02X}:{addr:04X}"))
    if op == 0x22 and off + 3 < len(blob):  # JSL long
        addr = blob[off+1] | (blob[off+2] << 8)
        b = blob[off+3]
        if addr >= 0x8000:
            return ("JSL", cpu_to_offset(f"{b:02X}:{addr:04X}"))
    return None

def forwarding_census_target(blob: bytes, off: int, intervals: list[tuple[int,int]]) -> str | None:
    """Return the census destination when off is only JSR/JSL + RTL forwarding."""
    direct = direct_target(blob, off)
    if not direct:
        return None
    kind, target = direct
    next_off = off + (3 if kind == "JSR" else 4)
    if next_off >= len(blob) or blob[next_off] != 0x6B or not in_census(target, intervals):
        return None
    return offset_to_cpu(target)

def best_similarity(src: bytes, dst: bytes, start: int, size: int = 48, radius: int = 96) -> tuple[int,float]:
    block = src[start:start+size]
    if len(block) < 8:
        return (0, 0.0)
    best = (0, -1.0)
    for shift in range(-radius, radius+1):
        a = start + shift
        b = a + len(block)
        if a < 0 or b > len(dst):
            continue
        score = sum(x == y for x,y in zip(block, dst[a:b])) / len(block)
        if score > best[1]:
            best = (shift, score)
    return best

def build(root: Path = ROOT) -> dict:
    census = json.loads((root / CENSUS.relative_to(ROOT)).read_text())
    blobs = {k:(root / p.relative_to(ROOT)).read_bytes() for k,p in ROMS.items()}
    usa = blobs["usa-retail"]
    intervals = [(cpu_to_offset(r["usa_start"]), cpu_to_offset(r["usa_end"])) for r in census["regions"]]
    code = [r for r in census["regions"] if r["kind"] == "code"]

    d = trace(usa)
    seed_entries(d, sorted({cpu_to_offset(r["usa_start"]) for r in code}))

    callers = defaultdict(list)
    for r in code:
        start, end = cpu_to_offset(r["usa_start"]), cpu_to_offset(r["usa_end"])
        for off in range(start, end + 1):
            if not (d.code_map[off] & d.OP_CODE):
                continue
            t = direct_target(usa, off)
            if not t:
                continue
            kind, target = t
            if target >= len(usa) or in_census(target, intervals):
                continue
            callers[target].append({
                "callsite": offset_to_cpu(off), "kind": kind,
                "source": r["source"], "region": r["name"],
                "relevance": RELEVANCE.get(r["source"], 1),
            })

    rows = []
    for target, refs in callers.items():
        build_align = {}
        align_scores = []
        for name, blob in blobs.items():
            if name == "usa-retail":
                continue
            shift, sim = best_similarity(usa, blob, target)
            build_align[name] = {"shift": shift, "similarity": round(sim, 6)}
            align_scores.append(sim)
        distinct_sources = len({x["source"] for x in refs})
        distinct_regions = len({(x["source"], x["region"]) for x in refs})
        max_rel = max(x["relevance"] for x in refs)
        mean_align = sum(align_scores) / len(align_scores) if align_scores else 0
        target_cpu = offset_to_cpu(target)
        raw_score = (
            5 * min(len(refs), 5) +
            6 * min(distinct_sources, 3) +
            3 * min(distinct_regions, 4) +
            4 * max_rel +
            round(20 * mean_align)
        )
        penalty, reason = DEPRIORITIZED.get(target_cpu, (0, None))
        forwarded = forwarding_census_target(usa, target, intervals)
        if forwarded:
            penalty += 50
            wrapper_reason = f"forwarding wrapper into accepted census at {forwarded}"
            reason = f"{reason}; {wrapper_reason}" if reason else wrapper_reason
        score = raw_score - penalty
        rows.append({
            "usa_target": target_cpu,
            "score": score,
            "raw_score": raw_score,
            "deprioritization_penalty": penalty,
            "deprioritization_reason": reason,
            "forwards_into_census": forwarded,
            "incoming_calls": len(refs),
            "distinct_sources": distinct_sources,
            "distinct_regions": distinct_regions,
            "max_shipping_relevance": max_rel,
            "mean_cross_build_similarity": round(mean_align, 6),
            "cross_build_alignment": build_align,
            "callers": sorted(refs, key=lambda x:(x["source"], x["callsite"])),
        })
    rows.sort(key=lambda x:(-x["score"], -x["incoming_calls"], x["usa_target"]))
    return {
        "schema_version": 1,
        "purpose": "Prioritize uncovered direct-call frontiers from accepted structural-island code.",
        "caveat": "Static direct-call frontier only. Scores guide the next discriminator; they are not semantic certainty or runtime frequency.",
        "candidate_count": len(rows),
        "candidates": rows,
    }

def render(data: dict, limit: int = 25) -> str:
    lines = [
        "# Comparative structural frontier ranking", "",
        "This ranks direct JSR/JSL targets outside the accepted census that are reached from already-bounded code. It favors repeated incoming connectivity, shipping-relevant caller paths, and easy four-ROM alignment. It does not claim runtime frequency or semantic identity.", "",
        "| Rank | USA target | Score | Calls | Sources | Relevance | Cross-build similarity | Note |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for i,row in enumerate(data["candidates"][:limit], 1):
        note = row.get("deprioritization_reason") or ""
        lines.append(f"| {i} | `{row['usa_target']}` | {row['score']} | {row['incoming_calls']} | {row['distinct_sources']} | {row['max_shipping_relevance']} | {row['mean_cross_build_similarity']:.3f} | {note} |")
    lines += ["", "Use the top candidates as cheap discriminators for the next independent structural island. Before promoting one, inspect its callers and confirm an instruction-aligned function/data boundary.", ""]
    return "\n".join(lines)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    data = build(args.root)
    outj = args.root / OUTJ.relative_to(ROOT)
    outm = args.root / OUTM.relative_to(ROOT)
    outj.write_text(json.dumps(data, indent=2) + "\n")
    outm.write_text(render(data))
    print(render(data))

if __name__ == "__main__":
    main()
