#!/usr/bin/env python3
"""Inspect racer packed-word low two bits and their renderer use.

This tool is deliberately evidence-first:
- census low2 values across all comparable monotonic racer-frame records;
- retain word/high/low correlations without assigning names;
- emit a bounded snes2asm listing around the proven packed-word consumer so
  every use of the current word workspace ($2A) can be inspected mechanically.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from compare_europe_usa_snes2asm_homologs import cpu_to_offset, seed_entries, trace
from extract_racer_presentation_family import (
    FRAME_ENTRY_SIZE,
    FRAME_SOURCE_BANK_BASE,
    FRAME_TABLE_ADDR,
    FRAME_TABLE_BANK,
    OCCUPANCY_BITS,
    frame_pointer,
    lorom_offset,
)

LIST_START = "83:F190"
LIST_END = "83:F290"


def comparable_records(rom: bytes):
    max_id = ((0x10000 - FRAME_TABLE_ADDR) // FRAME_ENTRY_SIZE) - 2
    for frame_id in range(max_id + 1):
        try:
            ptr = frame_pointer(rom, frame_id)
            nxt = frame_pointer(rom, frame_id + 1)
        except (ValueError, IndexError):
            continue
        if ptr.source_bank != nxt.source_bank:
            continue
        if ptr.source_addr < 0x8000 or nxt.source_addr < 0x8000:
            continue
        length = nxt.source_addr - ptr.source_addr
        if length < 4 or length > 68 or (length - 4) % 2:
            continue
        off = lorom_offset(ptr.source_bank, ptr.source_addr)
        raw = rom[off:off + length]
        if len(raw) != length:
            continue
        header = raw[:4]
        occupied = [
            (scan_index, byte_index, bit_index)
            for scan_index, (byte_index, bit_index) in enumerate(OCCUPANCY_BITS)
            if header[byte_index] & (1 << bit_index)
        ]
        words = [int.from_bytes(raw[i:i + 2], "little") for i in range(4, len(raw), 2)]
        if len(occupied) != len(words):
            continue
        yield frame_id, header, occupied, words


def census(rom: bytes) -> dict:
    low2 = Counter()
    low2_by_low6 = defaultdict(Counter)
    low2_by_scan = defaultdict(Counter)
    low2_by_high = defaultdict(Counter)
    frame_presence = Counter()
    examples = defaultdict(list)
    total_words = 0
    frame_count = 0

    for frame_id, header, occupied, words in comparable_records(rom):
        frame_count += 1
        seen = set()
        for (scan_index, _, _), word in zip(occupied, words):
            total_words += 1
            hi = word >> 8
            lo = word & 0xFF
            v = lo & 0x03
            low6 = (lo & 0xFC) >> 2
            low2[v] += 1
            low2_by_low6[low6][v] += 1
            low2_by_scan[scan_index][v] += 1
            low2_by_high[hi][v] += 1
            seen.add(v)
            if len(examples[v]) < 20:
                examples[v].append({
                    "frame_id": f"0x{frame_id:04X}",
                    "scan_index": scan_index,
                    "word_hex": f"0x{word:04X}",
                    "high_byte": hi,
                    "low6": low6,
                    "header_hex": header.hex(),
                })
        for v in seen:
            frame_presence[v] += 1

    def compact(mapping):
        return {
            str(k): {str(v): c for v, c in sorted(counts.items())}
            for k, counts in sorted(mapping.items())
        }

    mixed_low6 = {
        str(k): {str(v): c for v, c in sorted(counts.items())}
        for k, counts in sorted(low2_by_low6.items())
        if len(counts) > 1
    }
    mixed_high = {
        str(k): {str(v): c for v, c in sorted(counts.items())}
        for k, counts in sorted(low2_by_high.items())
        if len(counts) > 1
    }

    return {
        "comparable_frames": frame_count,
        "total_packed_words": total_words,
        "low2_counts": {str(k): low2[k] for k in range(4)},
        "frames_containing_low2": {str(k): frame_presence[k] for k in range(4)},
        "examples": {str(k): examples[k] for k in range(4)},
        "low2_by_scan_index": compact(low2_by_scan),
        "low2_by_low6": compact(low2_by_low6),
        "low2_by_high_byte": compact(low2_by_high),
        "mixed_low6_groups": mixed_low6,
        "mixed_high_byte_groups": mixed_high,
        "low2_is_not_function_of_low6": bool(mixed_low6),
        "low2_is_not_function_of_high_byte": bool(mixed_high),
    }


def listing(rom: bytes) -> dict:
    d = trace(rom)
    seed_entries(d, [cpu_to_offset("83:F0BB"), cpu_to_offset("83:F2BB")])
    start = cpu_to_offset(LIST_START)
    end = cpu_to_offset(LIST_END) + 1
    d.decode(start, end)
    rows = []
    for off, ins in d.code.item_range(start, end):
        rows.append({
            "cpu": f"83:{0x8000 + (off % 0x8000):04X}",
            "text": ins.text(),
        })
    word_workspace = []
    for i, row in enumerate(rows):
        text = row["text"].upper()
        if "$2A" in text or " #$0003" in text or " #$0001" in text or " #$0002" in text:
            word_workspace.append({
                "match": row,
                "context": rows[max(0, i - 5): min(len(rows), i + 7)],
            })
    return {
        "start": LIST_START,
        "end": LIST_END,
        "instruction_count": len(rows),
        "rows": rows,
        "word_workspace_xrefs": word_workspace,
    }


def render_md(report: dict) -> str:
    c = report["census"]
    lines = [
        "# Racer packed-word low-two-bit audit",
        "",
        f"Comparable frame records: **{c['comparable_frames']}**.",
        f"Packed words inspected: **{c['total_packed_words']}**.",
        "",
        "## Distribution",
        "",
    ]
    for k in range(4):
        lines.append(
            f"- low2={k}: {c['low2_counts'][str(k)]} words in "
            f"{c['frames_containing_low2'][str(k)]} frames"
        )
    lines += [
        "",
        f"Low2 is not a pure function of bits7..2: **{c['low2_is_not_function_of_low6']}**.",
        f"Low2 is not a pure function of the high byte: **{c['low2_is_not_function_of_high_byte']}**.",
        "",
        "## Bounded renderer listing",
        "",
    ]
    for row in report["listing"]["rows"]:
        lines.append(f"    {row['cpu']}  {row['text']}")
    lines += [
        "",
        "## Workspace xrefs",
        "",
    ]
    for hit in report["listing"]["word_workspace_xrefs"]:
        lines.append(f"### {hit['match']['cpu']} {hit['match']['text']}")
        lines.append("")
        for row in hit["context"]:
            lines.append(f"    {row['cpu']}  {row['text']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    report = {
        "schema_version": 1,
        "purpose": "Determine what can be proven about packed-word bits1..0 without speculative naming.",
        "census": census(rom),
        "listing": listing(rom),
    }
    js = json.dumps(report, indent=2, sort_keys=True) + "\n"
    md = render_md(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(js, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
