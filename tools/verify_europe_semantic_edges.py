#!/usr/bin/env python3
"""Corroborate weak Europe semantic anchors with independent call/dispatch edges."""
from __future__ import annotations

from pathlib import Path
import json

from tools.compare_semantic_anchors import ROMS, cpu_to_lorom_file, file_to_lorom_cpu, ngram_votes, similarity

OUT_JSON = Path("analysis/generated/europe-hud-finish-discriminators.json")
OUT_MD = Path("analysis/generated/europe-hud-finish-discriminators.md")

HUD_TARGETS = {
    "usa-retail": "81:C5B3",
    "pal-prototype-1994-11-29": "81:C590",
    "europe-retail": "81:C59C",
}


def cpu_parts(cpu: str) -> tuple[int, int]:
    bank_s, addr_s = cpu.split(":")
    return int(bank_s, 16), int(addr_s, 16)


def find_call_refs(blob: bytes, cpu: str) -> dict:
    bank, addr = cpu_parts(cpu)
    jsr = bytes((0x20, addr & 0xFF, addr >> 8))
    jsl = bytes((0x22, addr & 0xFF, addr >> 8, bank))
    out = {}
    for kind, token in (("jsr", jsr), ("jsl", jsl)):
        positions = []
        pos = blob.find(token)
        while pos >= 0:
            positions.append(pos)
            pos = blob.find(token, pos + 1)
        out[kind] = [{"file_offset": p, "cpu": file_to_lorom_cpu(p)} for p in positions]
    return out


def best_dispatch_match(source: bytes, target: bytes) -> dict:
    usa_start = cpu_to_lorom_file("81:82E6")
    size = 0x80
    src = source[usa_start:usa_start + size]
    votes = ngram_votes(src, target, k=6, stride=3, max_hits=32)
    votes.setdefault(usa_start, 0)
    candidates = []
    max_votes = max(votes.values()) if votes else 1
    for start, count in votes.most_common(64):
        if start + size > len(target):
            continue
        sim = similarity(src, target[start:start + size])
        vf = count / max_votes if max_votes else 0.0
        score = 0.85 * sim + 0.15 * vf
        candidates.append((score, sim, count, start))
    candidates.sort(reverse=True)
    score, sim, count, start = candidates[0]
    # USA dispatch table begins at +0x3A; object code 0x14 selects +0x14 within it.
    table = start + 0x3A
    entry = table + 0x14
    handler = int.from_bytes(target[entry:entry + 2], 'little')
    bank = int(file_to_lorom_cpu(start).split(':')[0], 16)
    return {
        "candidate_start": file_to_lorom_cpu(start),
        "file_offset": start,
        "similarity": round(sim, 6),
        "score": round(score, 6),
        "ngram_votes": count,
        "table_cpu": f"{bank:02X}:{(int(file_to_lorom_cpu(start).split(':')[1],16)+0x3A)&0xFFFF:04X}",
        "object_14_entry_cpu": f"{bank:02X}:{(int(file_to_lorom_cpu(start).split(':')[1],16)+0x4E)&0xFFFF:04X}",
        "object_14_handler": f"{bank:02X}:{handler:04X}",
    }


def build_report() -> dict:
    blobs = {name: path.read_bytes() for name, path in ROMS.items()}
    hud = {}
    for build, target in HUD_TARGETS.items():
        hud[build] = {
            "target": target,
            "refs": find_call_refs(blobs[build], target),
        }
    dispatch = {
        build: best_dispatch_match(blobs["usa-retail"], blobs[build])
        for build in ("pal-prototype-1994-11-29", "europe-retail")
    }
    dispatch['usa-retail'] = best_dispatch_match(blobs['usa-retail'], blobs['usa-retail'])
    return {
        "schema_version": 1,
        "hud_queue": hud,
        "object_dispatch": dispatch,
    }


def render_md(r: dict) -> str:
    lines=[
        "# Europe HUD / checkpoint structural discriminators",
        "",
        "Two independent edges are used here: direct call references to the proposed HUD queue target, and the object-code dispatch-table entry that selects the checkpoint/finish handler.",
        "",
        "## HUD queue call references",
        "",
        "| Build | Candidate | JSR refs | JSL refs |",
        "|---|---|---:|---:|",
    ]
    for build in ("usa-retail","pal-prototype-1994-11-29","europe-retail"):
        h=r["hud_queue"][build]
        lines.append(f"| {build} | `{h['target']}` | {len(h['refs']['jsr'])} | {len(h['refs']['jsl'])} |")
    lines += [
        "",
        "## Object-code 0x14 dispatch",
        "",
        "| Build | Matched dispatcher | Similarity | Dispatch table | 0x14 handler |",
        "|---|---|---:|---|---|",
    ]
    for build in ("usa-retail","pal-prototype-1994-11-29","europe-retail"):
        d=r["object_dispatch"][build]
        lines.append(f"| {build} | `{d['candidate_start']}` | {d['similarity']:.3f} | `{d['table_cpu']}` | `{d['object_14_handler']}` |")
    lines += [
        "",
        "If Europe object code 0x14 dispatches directly to `81:8042`, that independently corroborates the proposed Europe `Race_HandleCheckpointFinish` correspondence. Coherent call-reference counts and caller locations similarly strengthen the HUD queue candidate beyond byte similarity alone.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    r=build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(r, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    OUT_MD.write_text(render_md(r), encoding="utf-8")
    print(OUT_MD.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
