#!/usr/bin/env python3
"""Decode the shipped USA RNC1 routine with snesrecomp's authoritative v2 decoder.

This is deliberately a probe, not a home-grown disassembler. It asks the same
decoder used for recompilation whether two dynamically observed interpreter
scope-entry PCs belong to the control-flow graph rooted at the known RNC1 entry
and prints the nearby decoded instructions when they do. These scope-entry PCs
are attribution landmarks, not necessarily the instructions that performed the
WRAM stores.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOMPILER = ROOT / "snesrecomp" / "recompiler"
V2 = RECOMPILER / "v2"
sys.path.insert(0, str(RECOMPILER))
sys.path.insert(0, str(V2))

from decoder import decode_function  # type: ignore  # noqa: E402

ENTRY_BANK = 0x01
ENTRY_PC = 0xB8F1
SCOPE_ENTRIES = {
    "byte11-mutation-scope-entry": 0x01BA96,
    "payload-install-scope-entry": 0x01BB73,
}


def fmt(di) -> str:
    pc = di.key.pc
    return (
        f"${(pc >> 16) & 0xFF:02X}:{pc & 0xFFFF:04X} "
        f"[M={di.key.m} X={di.key.x}] "
        f"{di.insn.mnem:<5} {di.insn._fmt()}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "rom",
        type=Path,
        nargs="?",
        default=Path("reference/roms/retail/Uniracers_USA.sfc"),
    )
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    roots = [(ENTRY_BANK, ENTRY_PC, 0, 0, "RNC1")]
    seen = set()
    graphs = []
    queue = list(roots)

    while queue and len(seen) < 64:
        bank, start, em, ex, path = queue.pop(0)
        key = (bank, start, em, ex)
        if key in seen:
            continue
        seen.add(key)
        try:
            graph = decode_function(
                rom,
                bank=bank,
                start=start,
                entry_m=em,
                entry_x=ex,
            )
        except Exception as exc:
            graphs.append({
                "root": key,
                "path": path,
                "error": str(exc),
                "graph": None,
            })
            continue
        graphs.append({
            "root": key,
            "path": path,
            "error": None,
            "graph": graph,
        })

        # Direct local JSR keeps M/X state. Follow those callees recursively so
        # helper routines such as GTBITS/MAKEHUFF can contain a traced scope
        # entry even when the top-level function graph treats them separately.
        for di in graph.insns.values():
            ins = di.insn
            if ins.mnem == "JSR" and ins.length == 3:
                target = ins.operand & 0xFFFF
                if target >= 0x8000:
                    queue.append((
                        bank,
                        target,
                        di.key.m,
                        di.key.x,
                        f"{path} -> {bank:02X}:{target:04X}",
                    ))

    report = {
        "entry": f"{ENTRY_BANK:02X}:{ENTRY_PC:04X}",
        "decoded_roots": [
            {
                "bank": bank,
                "pc": start,
                "m": em,
                "x": ex,
                "path": item["path"],
                "decoded_states": (
                    len(item["graph"].insns) if item["graph"] is not None else 0
                ),
                "error": item["error"],
            }
            for item in graphs
            for bank, start, em, ex in [item["root"]]
        ],
        "scope_entries": {},
    }

    for label, target in SCOPE_ENTRIES.items():
        owners = []
        for item in graphs:
            graph = item["graph"]
            if graph is None:
                continue
            rows = sorted(
                graph.insns.values(),
                key=lambda d: (d.key.pc, d.key.m, d.key.x),
            )
            matches = [d for d in rows if d.key.pc == target]
            if not matches:
                continue
            all_index = {id(d): i for i, d in enumerate(rows)}
            for di in matches:
                idx = all_index[id(di)]
                context = rows[max(0, idx - 8):idx + 9]
                bank, start, em, ex = item["root"]
                owners.append(
                    {
                        "root": f"{bank:02X}:{start:04X}",
                        "root_m": em,
                        "root_x": ex,
                        "call_path": item["path"],
                        "m": di.key.m,
                        "x": di.key.x,
                        "instruction": fmt(di),
                        "context": [fmt(x) for x in context],
                    }
                )
        report["scope_entries"][label] = {
            "reachable_from_rnc_call_tree": bool(owners),
            "owners": owners,
        }

    print(json.dumps(report, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
