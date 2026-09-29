#!/usr/bin/env python3
"""Correlate selected ROM-side audio block payloads with SPC APU RAM snapshots.

The SPC archive remains transient. This tool consumes a canonical ROM and an SPC
ZIP/directory, extracts selected length-prefixed audio blocks, and looks for:
- an exact full-payload occurrence in each snapshot's 64 KiB APU RAM;
- the longest payload slice found after trimming a small number of leading and
  trailing bytes, useful when a ROM block includes transfer/control framing.

A match is evidence of shared loaded bytes, not by itself proof of package
reachability or song identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.analyze_spc_set import load_snapshots
    from tools.inspect_audio_block_pool import DEFAULT_POOL_CPU, lorom_file_offset, parse_block_pool
except ModuleNotFoundError:
    from analyze_spc_set import load_snapshots
    from inspect_audio_block_pool import DEFAULT_POOL_CPU, lorom_file_offset, parse_block_pool


DEFAULT_BLOCK_IDS = (0x07, 0x15, 0x29)


def extract_block_payloads(rom: bytes, block_ids=DEFAULT_BLOCK_IDS) -> list[dict]:
    block_ids = tuple(block_ids)
    pool = parse_block_pool(rom, count=max(block_ids) + 1)
    by_id = {row["id"]: row for row in pool["blocks"]}
    rows = []
    for block_id in block_ids:
        meta = by_id[block_id]
        off = int(meta["file_offset"], 16)
        total = meta["total_length"]
        record = rom[off : off + total]
        payload = record[2:]
        rows.append(
            {
                "id": block_id,
                "id_hex": f"0x{block_id:02X}",
                "file_offset": meta["file_offset"],
                "cpu_address": meta["cpu_address"],
                "total_length": total,
                "payload_length": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "payload": payload,
            }
        )
    return rows


def best_trimmed_match(
    payload: bytes,
    ram: bytes,
    *,
    max_leading_trim: int = 16,
    max_trailing_trim: int = 16,
    min_match: int = 32,
) -> dict | None:
    best = None
    for leading in range(max_leading_trim + 1):
        for trailing in range(max_trailing_trim + 1):
            end = len(payload) - trailing if trailing else len(payload)
            if end <= leading:
                continue
            candidate = payload[leading:end]
            if len(candidate) < min_match:
                continue
            pos = ram.find(candidate)
            if pos < 0:
                continue
            row = {
                "apu_offset": pos,
                "apu_offset_hex": f"0x{pos:04X}",
                "matched_length": len(candidate),
                "leading_trim": leading,
                "trailing_trim": trailing,
                "matched_sha256": hashlib.sha256(candidate).hexdigest(),
            }
            if best is None or row["matched_length"] > best["matched_length"]:
                best = row
    return best


def analyze(rom: bytes, spc_source: Path, block_ids=DEFAULT_BLOCK_IDS) -> dict:
    snapshots, source_meta = load_snapshots(spc_source)
    blocks = extract_block_payloads(rom, block_ids)
    out_blocks = []
    for block in blocks:
        payload = block.pop("payload")
        matches = []
        for snapshot in snapshots:
            exact = snapshot.ram.find(payload)
            best = best_trimmed_match(payload, snapshot.ram)
            matches.append(
                {
                    "track": snapshot.title,
                    "path": snapshot.name,
                    "exact_apu_offset": exact if exact >= 0 else None,
                    "exact_apu_offset_hex": f"0x{exact:04X}" if exact >= 0 else None,
                    "best_trimmed_match": best,
                }
            )
        out_blocks.append({**block, "matches": matches})

    return {
        "schema_version": 1,
        "canonical_rom_sha256": hashlib.sha256(rom).hexdigest(),
        "spc_source": source_meta,
        "block_ids": [f"0x{x:02X}" for x in block_ids],
        "blocks": out_blocks,
        "interpretation_guardrails": [
            "exact or trimmed byte identity shows shared loaded APU bytes only",
            "absence of a match does not prove a block is never used",
            "song/package attribution requires combining this with selector-table and reachability evidence",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("spc_source", type=Path)
    ap.add_argument("--block", action="append", type=lambda x: int(x, 0), dest="blocks")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = analyze(
        args.rom.read_bytes(),
        args.spc_source,
        tuple(args.blocks) if args.blocks else DEFAULT_BLOCK_IDS,
    )
    print(f"blocks={len(report['blocks'])}")
    for block in report["blocks"]:
        print(f"  {block['id_hex']} payload={block['payload_length']}")
        for match in block["matches"]:
            best = match["best_trimmed_match"]
            if match["exact_apu_offset_hex"] or best:
                print(
                    f"    {match['track']}: exact={match['exact_apu_offset_hex']} "
                    f"best={best}"
                )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
