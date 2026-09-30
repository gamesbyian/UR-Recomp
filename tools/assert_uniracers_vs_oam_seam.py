#!/usr/bin/env python3
"""Assert the locally reproduced Uniracers VS active-display OAM seam.

Patched Snes9x snesref dumps one PPU-write TSV per named checkpoint:
    frame vcounter hcounter addr value source

In active VS gameplay Uniracers performs HDMA writes to $2104 at scanlines
0 and 112. The canonical observed values are $A5 at V=0 and $5A at V=112.
This utility makes that historical compatibility seam a deterministic test.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def parse_ppuw(path: Path) -> list[dict]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.lower().startswith("frame"):
            continue
        parts = line.split()
        if len(parts) != 6:
            raise ValueError(f"{path}: malformed PPU write row: {raw!r}")
        frame, v, h, addr, value, source = parts
        rows.append({
            "frame": int(frame, 0),
            "v": int(v, 0),
            "h": int(h, 0),
            "addr": int(addr, 16),
            "value": int(value, 16),
            "source": source.lower(),
        })
    return rows


def assert_vs_oam_seam(paths: list[Path]) -> list[dict]:
    if not paths:
        raise ValueError("at least one PPU-write TSV is required")
    results = []
    for path in paths:
        rows = parse_ppuw(path)
        active = [
            r for r in rows
            if r["addr"] == 0x2104 and r["source"] == "hdma" and r["v"] < 225
        ]
        by_v = {}
        for row in active:
            by_v.setdefault(row["v"], set()).add(row["value"])
        ok0 = 0xA5 in by_v.get(0, set())
        ok112 = 0x5A in by_v.get(112, set())
        if not (ok0 and ok112):
            raise AssertionError(
                f"{path}: expected HDMA $2104 writes V=0->$A5 and "
                f"V=112->$5A; observed "
                f"{ {v: sorted(vals) for v, vals in sorted(by_v.items())} }"
            )
        results.append({
            "path": str(path),
            "active_oam_writes": len(active),
            "v0_values": sorted(by_v.get(0, set())),
            "v112_values": sorted(by_v.get(112, set())),
        })
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ppuw", nargs="+", type=Path)
    args = ap.parse_args()
    for row in assert_vs_oam_seam(args.ppuw):
        print(
            f"{row['path']}: PASS active_oam_writes={row['active_oam_writes']} "
            f"v0={row['v0_values']} v112={row['v112_values']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
