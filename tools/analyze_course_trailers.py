#!/usr/bin/env python3
"""Analyze decoded course payload tails referenced by header LE16@11."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import statistics

from analyze_rnc_streams import ROMS, find_streams
from rnc_method1 import unpack_method1

JSON_OUT = Path("analysis/generated/course-trailer-structure.json")
MD_OUT = Path("analysis/generated/course-trailer-structure.md")


def u16le(data: bytes, off: int) -> int:
    return data[off] | (data[off + 1] << 8)


def analyze_build(path: Path) -> list[dict]:
    rom = path.read_bytes()
    rows = []
    for index, (_off, packed, _header) in enumerate(find_streams(rom), 1):
        decoded = unpack_method1(packed)
        cursor = u16le(decoded, 11)
        if cursor >= len(decoded):
            raise SystemExit(
                f"{path}: stream {index}: LE16@11 0x{cursor:04X} outside decoded size {len(decoded)}"
            )
        trailer = decoded[cursor + 1:]
        rows.append({
            "stream": index,
            "tour_slot": ((index - 1) % 5) + 1,
            "decoded_size": len(decoded),
            "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
            "cursor": cursor,
            "cursor_plus_1_aligned_16": ((cursor + 1) % 16 == 0),
            "trailer_length": len(trailer),
            "trailer_hex": trailer.hex(" "),
            "first_byte": trailer[0] if trailer else None,
            "last_byte": trailer[-1] if trailer else None,
            "distinct_bytes": len(set(trailer)),
            "zero_count": trailer.count(0),
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    lengths = Counter(r["trailer_length"] for r in rows)
    firsts = Counter(r["first_byte"] for r in rows if r["first_byte"] is not None)
    lasts = Counter(r["last_byte"] for r in rows if r["last_byte"] is not None)
    by_slot = defaultdict(list)
    for r in rows:
        by_slot[r["tour_slot"]].append(r["trailer_length"])
    return {
        "stream_count": len(rows),
        "aligned_16_count": sum(r["cursor_plus_1_aligned_16"] for r in rows),
        "trailer_length_min": min(lengths),
        "trailer_length_max": max(lengths),
        "trailer_length_counts": {str(k): v for k, v in sorted(lengths.items())},
        "first_byte_counts": {f"0x{k:02X}": v for k, v in sorted(firsts.items())},
        "last_byte_counts": {f"0x{k:02X}": v for k, v in sorted(lasts.items())},
        "slot_lengths": {str(k): v for k, v in sorted(by_slot.items())},
        "slot_length_stats": {
            str(k): {
                "min": min(v),
                "max": max(v),
                "mean": round(statistics.mean(v), 6),
                "median": statistics.median(v),
            }
            for k, v in sorted(by_slot.items())
        },
    }


def main() -> int:
    builds = {}
    for name, path in ROMS.items():
        rows = analyze_build(path)
        builds[name] = {"summary": summarize(rows), "streams": rows}

    usa = builds["usa-retail"]
    usa_hashes={r["decoded_sha256"] for r in builds["usa-retail"]["streams"]}
    all_hashes={
        r["decoded_sha256"]
        for payload in builds.values()
        for r in payload["streams"]
    }
    report = {
        "schema_version": 2,
        "field": "LE16@11",
        "unique_decoded_payloads_across_builds": len(all_hashes),
        "builds": builds,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Course Trailer Structure",
        "",
        "Mechanical analysis of bytes after the little-endian header field LE16@11. The field itself is treated as an inclusive cursor; the analyzed trailing region begins at LE16@11 + 1. No semantic record names are assumed.",
        "",
        "## Cross-build summary",
        "",
        f"- unique decoded payloads across all builds: {len(all_hashes)}",
        "",
        "| Build | Streams | Novel decoded vs USA | (cursor+1) aligned / total | Tail min | Tail max |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, payload in builds.items():
        s = payload["summary"]
        novel=sum(
            r["decoded_sha256"] not in usa_hashes
            for r in payload["streams"]
        )
        md.append(
            f"| {name} | {s['stream_count']} | {novel} | "
            f"{s['aligned_16_count']}/{s['stream_count']} | "
            f"{s['trailer_length_min']} | {s['trailer_length_max']} |"
        )

    rows = usa["streams"]
    s = usa["summary"]
    md += [
        "",
        "## USA retail detail",
        "",
        f"- streams: {s['stream_count']}",
        f"- trailer length range: {s['trailer_length_min']}–{s['trailer_length_max']} bytes",
        "- length histogram: " + ", ".join(f"{k}x{v}" for k, v in s["trailer_length_counts"].items()),
        "- first-byte histogram: " + ", ".join(f"{k}x{v}" for k, v in s["first_byte_counts"].items()),
        "- last-byte histogram: " + ", ".join(f"{k}x{v}" for k, v in s["last_byte_counts"].items()),
        "",
        "| Stream | Slot | Cursor | Decoded size | Tail bytes | First | Last | Distinct | Zeros | Trailer hex |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        first = "none" if r["first_byte"] is None else f"0x{r['first_byte']:02X}"
        last = "none" if r["last_byte"] is None else f"0x{r['last_byte']:02X}"
        md.append(
            f"| {r['stream']} | {r['tour_slot']} | 0x{r['cursor']:04X} | "
            f"{r['decoded_size']} | {r['trailer_length']} | {first} | {last} | "
            f"{r['distinct_bytes']} | {r['zero_count']} | {r['trailer_hex']} |"
        )

    md += [
        "",
        "## USA slot length ranges",
        "",
        "Slot 3 is the independently identified stunt slot. The table reports trailer length only; it does not assume trailer semantics.",
        "",
        "| Slot | Track-order role | Min | Median | Mean | Max | Values |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for slot in range(1, 6):
        vals = s["slot_lengths"][str(slot)]
        st = s["slot_length_stats"][str(slot)]
        role = "Stunt" if slot == 3 else ("Race" if slot in (1, 4) else "Circuit")
        md.append(
            f"| {slot} | {role} | {st['min']} | {st['median']} | "
            f"{st['mean']:.3f} | {st['max']} | "
            + ", ".join(str(v) for v in vals)
            + " |"
        )

    MD_OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(JSON_OUT)
    print(MD_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
