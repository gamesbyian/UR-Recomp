#!/usr/bin/env python3
"""Read-only bounded CPU-direct PPU port provenance from existing PPUPCTRACE logs.

Inspired by malmazuke's register-order provenance; does not invent DMA,
HDMA, final VRAM state, or OAM pixel winners. Every row is an *observed*
S9xSetPPU CPU-direct write, with frame/beam/cycle and original CPU PC.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.analyze_preparation_ppu_pc_trace import TRACE_RE, SCROLL_RE
except ModuleNotFoundError:
    from analyze_preparation_ppu_pc_trace import TRACE_RE, SCROLL_RE

PORTS = {0x2116: "VMADDL", 0x2117: "VMADDH", 0x2118: "VMDATAL", 0x2119: "VMDATAH"}


def collect(lines: list[str], *, from_frame: int | None = None,
            to_frame: int | None = None) -> dict:
    if from_frame is not None and to_frame is not None and from_frame > to_frame:
        raise ValueError("from-frame must not exceed to-frame")
    events = []
    skipped = 0
    for lineno, line in enumerate(lines, 1):
        if "PPUPCTRACE" not in line:
            continue
        match = TRACE_RE.search(line)
        if not match:
            skipped += 1
            continue
        row = match.groupdict()
        frame = int(row["frame"])
        if (from_frame is not None and frame < from_frame) or (
                to_frame is not None and frame > to_frame):
            continue
        addr = int(row["addr"], 16)
        if addr not in PORTS:
            skipped += 1
            continue
        events.append({
            "frame": frame, "scanline": int(row["v"]), "cpu_cycles": int(row["cycles"]),
            "pc": row["pc"].upper(), "port": f"{addr:04X}", "port_name": PORTS[addr],
            "value": int(row["val"], 16), "source_line": lineno,
        })
    # Preserve log order; backward frame/beam/cycle events indicate different
    # epochs or a malformed trace, not a safe total execution order.
    ordering_errors = []
    for a, b in zip(events, events[1:]):
        if (b["frame"], b["scanline"], b["cpu_cycles"]) < (
                a["frame"], a["scanline"], a["cpu_cycles"]):
            ordering_errors.append([a["source_line"], b["source_line"]])
    # Only an immediately adjacent, temporally ordered 2116/17/18/19
    # sequence is a defensible witnessed word pair. A gap, rollover or
    # intervening register write must remain unpaired.
    quads = []
    for i in range(len(events) - 3):
        q = events[i:i + 4]
        if [x["port"] for x in q] != ["2116", "2117", "2118", "2119"]:
            continue
        if any(b["source_line"] != a["source_line"] + 1 for a, b in zip(q, q[1:])):
            continue
        if len({x["frame"] for x in q}) != 1:
            continue
        if any((b["scanline"], b["cpu_cycles"]) < (a["scanline"], a["cpu_cycles"]) for a, b in zip(q, q[1:])):
            continue
        quads.append({
            "frame": q[0]["frame"],
            "source_lines": [x["source_line"] for x in q],
            "source_pcs": [x["pc"] for x in q],
            "vmadd_word": q[0]["value"] | q[1]["value"] << 8,
            "data_low": q[2]["value"], "data_high": q[3]["value"],
            "classification": "observed_cpu_direct_port_write_quad",
            "final_vram_destination_proven": False,
        })
    frames = sorted({e["frame"] for e in events})
    return {
        "schema_version": 1, "scope": "CPU-direct $2116-$2119 Snes9x log only",
        "claim_limits": [
            "No DMA/HDMA observations in this log",
            "No VMAIN ($2115) initial state or complete VMADD increment semantics",
            "No final BG/OBJ priority, pixel visibility or OAM ownership conclusions",
            "No complete VRAM state reconstruction or USA gameplay acceptance",
        ],
        "trace_rows": len(events), "unparseable_or_unsupported_rows": skipped,
        "event_frames": frames, "ordering_violations": ordering_errors,
        "cpu_port_events": events, "contiguous_word_quads": quads,
        "contiguous_word_quad_count": len(quads),
        "complete_provenance": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace", type=Path)
    ap.add_argument("--from-frame", type=int)
    ap.add_argument("--to-frame", type=int)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--require-quad", action="store_true")
    args = ap.parse_args(argv)
    try:
        report = collect(args.trace.read_text(encoding="utf-8", errors="replace").splitlines(),
                         from_frame=args.from_frame, to_frame=args.to_frame)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    text = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    if report["ordering_violations"] or report["unparseable_or_unsupported_rows"]:
        return 2
    return 0 if report["contiguous_word_quad_count"] or not args.require_quad else 2


if __name__ == "__main__":
    raise SystemExit(main())
