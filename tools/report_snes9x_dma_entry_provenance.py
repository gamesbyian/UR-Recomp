#!/usr/bin/env python3
"""Attribute original DMA entry descriptors without inventing PPU final state.

URDMAPROV is an opt-in Snes9x 1.43 source-level witness. Entries contain
channel A-bus origin and B-bus destination register only; $2115/16/17,
$2102/03 and $2121 latches are *not* in this schema. Never claim their values.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROW = re.compile(
    r"URDMAPROV frame=(\d+) v=(\d+) cycles=(-?\d+) pc=([0-9A-Fa-f]{6}) "
    r"channel=(\d+) bank=([0-9A-Fa-f]{2}) src=([0-9A-Fa-f]{4}) "
    r"bbus=([0-9A-Fa-f]{2}) count=([0-9A-Fa-f]{4}) "
    r"mode=(\d+) direction=(\d+) fixed=(\d+) decrement=(\d+)$"
)
PORTS = {4: "OAMDATA", 0x18: "VMDATAL", 0x19: "VMDATAH", 0x22: "CGDATA"}

def parse(lines: list[str], *, from_frame: int | None = None,
          to_frame: int | None = None) -> dict:
    if from_frame is not None and to_frame is not None and from_frame > to_frame:
        raise ValueError("invalid frame window")
    rows, malformed = [], []
    for line_number, line in enumerate(lines, 1):
        if "URDMAPROV" not in line:
            continue
        m = ROW.search(line.strip())
        if not m:
            malformed.append(line_number)
            continue
        frame, v, cycles = map(int, m.group(1, 2, 3))
        if from_frame is not None and frame < from_frame or to_frame is not None and frame > to_frame:
            continue
        pc = int(m.group(4), 16)
        channel = int(m.group(5))
        bank, addr, bbus, count = (int(m.group(i), 16) for i in range(6, 10))
        mode, direction, fixed, decrement = (int(m.group(i)) for i in range(10, 14))
        if channel > 7 or bbus not in PORTS or mode > 7 or any(x not in (0, 1) for x in (direction, fixed, decrement)):
            malformed.append(line_number)
            continue
        rows.append({
            "source_line": line_number, "frame": frame, "v": v, "cycles": cycles,
            "pc": f"{pc:06X}", "channel": channel,
            "a_bus_source": f"{bank:02X}:{addr:04X}",
            "a_bus_region": "wram" if bank in (0x7E, 0x7F) else
                            "rom_candidate" if (addr >= 0x8000 and (bank <= 0x6F or 0x80 <= bank <= 0xEF)) else "other",
            "b_bus_register": f"21{bbus:02X}", "b_bus_name": PORTS[bbus],
            "transfer_count": count or 65536, "raw_count": count,
            "transfer_mode": mode, "direction": direction,
            "fixed": bool(fixed), "decrement": bool(decrement),
            "transfer_completed": False, "ppu_port_address_known": False,
            "h_dma": False
        })
    order_errors = [
        [a["source_line"], b["source_line"]]
        for a, b in zip(rows, rows[1:])
        if (b["frame"], b["v"], b["cycles"]) < (a["frame"], a["v"], a["cycles"])
    ]
    return {
        "schema_version": 1, "source": "opt-in archived Snes9x 1.43 S9xDoDMA entry",
        "entries": rows, "count": len(rows),
        "malformed_lines": malformed, "order_errors": order_errors,
        "claim_limits": [
            "DMA entry only; no confirmation of DMA completion or transferred byte contents",
            "No HDMA instrumentation or claim of HDMA absence",
            "PPU destination port address latch state unobserved; no VMADD/OAMADD/CGADD inference",
            "No proof of sprite visibility, priority, final VRAM/OAM, or original/native event parity",
            "PC is emulator entry context, not independently proven exact trigger instruction"
        ], "complete_ppu_provenance": False,
    }

def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("log", type=Path)
    a.add_argument("--from-frame", type=int)
    a.add_argument("--to-frame", type=int)
    a.add_argument("--json-out", type=Path)
    x = a.parse_args()
    try:
        result = parse(x.log.read_text(encoding="utf-8", errors="replace").splitlines(),
                       from_frame=x.from_frame, to_frame=x.to_frame)
    except (OSError, ValueError) as exc:
        a.error(str(exc))
    body = json.dumps(result, indent=2) + "\n"
    if x.json_out:
        x.json_out.parent.mkdir(parents=True, exist_ok=True)
        x.json_out.write_text(body, encoding="utf-8")
    print(body, end="")
    return 2 if result["malformed_lines"] or result["order_errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
