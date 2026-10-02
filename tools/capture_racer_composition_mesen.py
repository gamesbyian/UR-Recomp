#!/usr/bin/env python3
"""Capture one synchronized racer-composition invocation in MesenCE.

The ordinary frame-boundary dumps are excellent presentation oracles, but the
persistent presentation IDs can move relative to the already-built DMA staging
list within the same host frame. This tool closes that phase gap by stopping
the reference emulator twice inside one 83:F0BB invocation:

* 83:F129, immediately after 83:F2BB has built the untouched row masks; and
* 83:F292, after the sparse staging descriptor list is complete.

It then checks the repository-owned static composer against both boundaries.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from controller_input import load_controller_runs, masks_at
from extract_racer_presentation_family import (
    compose_racer_staging,
    extract_frame,
    lorom_offset,
    packed_word_source,
)

DEFAULT_MESEN_REPO = ROOT / "third_party" / "src" / "mesen-for-ai"
MASK_BUTTONS = (
    ("b", 0x001), ("y", 0x002), ("select", 0x004), ("start", 0x008),
    ("up", 0x010), ("down", 0x020), ("left", 0x040), ("right", 0x080),
    ("a", 0x100), ("x", 0x200), ("l", 0x400), ("r", 0x800),
)


def load_mesen_class(repo: Path):
    client = ROOT / "tools" / "mesen_client.py"
    spec = importlib.util.spec_from_file_location("ur_mesen_client", client)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {client}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Mesen


def buttons_for_mask(mask: int) -> dict[str, bool]:
    return {name: True for name, bit in MASK_BUTTONS if mask & bit}


def read_wram(mesen, address: int, length: int) -> bytes:
    out = bytearray()
    pos = address
    remaining = length
    while remaining:
        size = min(remaining, 0x1000)
        result = mesen.tool(
            "cpu.read_memory",
            memoryType="snesWorkRam",
            address=pos,
            length=size,
        )
        out.extend(result["bytes"])
        pos += size
        remaining -= size
    return bytes(out)


def u16(data: bytes, off: int) -> int:
    return data[off] | (data[off + 1] << 8)


def pc_display(result: dict) -> str:
    hit = result.get("breakpoint_hit") or {}
    return str(hit.get("pcDisplay", "")).upper()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--input-file", type=Path, required=True)
    ap.add_argument("--advance-frames", type=int, default=1218)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    ap.add_argument(
        "--mesen-for-ai-repo",
        type=Path,
        default=Path(os.environ.get("MESEN_FOR_AI_REPO", str(DEFAULT_MESEN_REPO))),
    )
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    runs = load_controller_runs(args.input_file)
    Mesen = load_mesen_class(args.mesen_for_ai_repo.resolve())

    with Mesen(repo=str(args.mesen_for_ai_repo.resolve())) as mesen:
        mesen.load_rom(str(args.rom.resolve()), timeout=180)

        previous = (None, None)
        for frame in range(args.advance_frames):
            current = masks_at(runs, frame)
            for port, mask in enumerate(current):
                if mask != previous[port]:
                    mesen.tool(
                        "input.set",
                        port=port,
                        subport=0,
                        buttons=buttons_for_mask(mask),
                    )
            previous = current
            mesen.tool("run.step_frames", frames=1, reset=(frame == 0))

        # Hold the same controller state for the interrupted renderer frame.
        current = masks_at(runs, args.advance_frames)
        for port, mask in enumerate(current):
            if mask != previous[port]:
                mesen.tool(
                    "input.set",
                    port=port,
                    subport=0,
                    buttons=buttons_for_mask(mask),
                )

        pre_bp = mesen.tool(
            "breakpoint.create",
            memoryType="snesPrgRom",
            address=lorom_offset(0x83, 0xF129),
            length=1,
            access="exec",
            cpuType="snes",
        )
        post_bp = mesen.tool(
            "breakpoint.create",
            memoryType="snesPrgRom",
            address=lorom_offset(0x83, 0xF292),
            length=1,
            access="exec",
            cpuType="snes",
        )

        pre_step = mesen.tool("run.step_frames", frames=2, reset=False)
        if "F129" not in pc_display(pre_step):
            raise SystemExit(
                f"expected first racer composition breakpoint at F129, got {pre_step.get('breakpoint_hit')}"
            )
        pre = read_wram(mesen, 0, 0x1800)
        mesen.tool("breakpoint.delete", handle=pre_bp["handle"])

        post_step = mesen.tool("run.step_frames", frames=1, reset=False)
        if "F292" not in pc_display(post_step):
            raise SystemExit(
                f"expected second racer composition breakpoint at F292, got {post_step.get('breakpoint_hit')}"
            )
        post = read_wram(mesen, 0, 0x1800)
        mesen.tool("breakpoint.delete", handle=post_bp["handle"])

    ids = {
        "p1_primary": u16(pre, 0x0FE9),
        "p2_primary": u16(pre, 0x0FEB),
        "p1_companion": u16(pre, 0x0D3F),
        "p2_companion": u16(pre, 0x0D41),
    }
    selectors = {"p1": u16(pre, 0x0C83), "p2": u16(pre, 0x0C85)}
    companion_gate_words = {
        "p1": u16(pre, 0x0D1B),
        "p2": u16(pre, 0x0D1D),
    }
    companion_enabled = {
        "p1": companion_gate_words["p1"] != 0,
        "p2": companion_gate_words["p2"] != 0,
    }
    frames = {name: extract_frame(rom, fid) for name, fid in ids.items()}
    composed = compose_racer_staging(
        frames["p1_primary"],
        frames["p2_primary"],
        frames["p1_companion"],
        frames["p2_companion"],
        p1_selector=selectors["p1"],
        p2_selector=selectors["p2"],
        p1_companion_enabled=companion_enabled["p1"],
        p2_companion_enabled=companion_enabled["p2"],
    )

    actual_primary = [f"0x{u16(pre, 0x00 + 2*i):04X}" for i in range(5)]
    actual_companion = [f"0x{u16(pre, 0x0A + 2*i):04X}" for i in range(5)]
    mask_checks = {
        "primary_exact": actual_primary == composed["primary_row_masks"],
        "companion_raw_exact": actual_companion == composed["companion_row_masks_raw"],
        "actual_primary": actual_primary,
        "expected_primary": composed["primary_row_masks"],
        "actual_companion_raw": actual_companion,
        "expected_companion_raw": composed["companion_row_masks_raw"],
        "expected_companion_effective": composed["companion_row_masks"],
    }

    descriptors = []
    for i in range(82):
        q = i * 2
        bank = post[0x15A1 + q]
        if bank == 0xFF:
            break
        descriptors.append({
            "slot": i,
            "source_bank": bank,
            "source_addr": u16(post, 0x1645 + q),
            "vram_word": u16(post, 0x16E9 + q),
        })
    by_dest: dict[int, list[dict]] = {}
    for row in descriptors:
        by_dest.setdefault(row["vram_word"], []).append(row)

    occupied = []
    exact = 0
    destinations = 0
    for cell in composed["cells"]:
        if cell["word_hex"] is None:
            continue
        candidates = by_dest.get(cell["staged_vram_word"], [])
        destinations += int(bool(candidates))
        matches = [
            row for row in candidates
            if row["source_bank"] == cell["source_bank"]
            and row["source_addr"] == cell["source_addr"]
        ]
        exact += int(bool(matches))
        occupied.append({
            "row": cell["row"],
            "column": cell["column"],
            "player": cell["player"],
            "choice": cell["choice"],
            "expected_source": cell["source_snes"],
            "vram_word": f"0x{cell['staged_vram_word']:04X}",
            "source_exact": bool(matches),
            "matching_slots": [x["slot"] for x in matches],
            "actual_sources": [
                f"{x['source_bank']:02X}:{x['source_addr']:04X}" for x in candidates
            ],
        })

    report = {
        "schema_version": 1,
        "purpose": "Reference-emulator synchronized proof of the four-record racer cache composer.",
        "breakpoints": {
            "pre": {"cpu": "83:F129", "rom_offset": lorom_offset(0x83, 0xF129), "hit": pre_step.get("breakpoint_hit")},
            "post": {"cpu": "83:F292", "rom_offset": lorom_offset(0x83, 0xF292), "hit": post_step.get("breakpoint_hit")},
        },
        "ids": {k: f"0x{v:04X}" for k, v in ids.items()},
        "selectors": selectors,
        "companion_gate_words": {k: f"0x{v:04X}" for k, v in companion_gate_words.items()},
        "companion_enabled": companion_enabled,
        "mask_checks": mask_checks,
        "staging": {
            "descriptor_count": len(descriptors),
            "occupied_cells": len(occupied),
            "occupied_destinations_present": destinations,
            "occupied_sources_exact": exact,
            "all_occupied_destinations_present": destinations == len(occupied),
            "all_occupied_sources_exact": exact == len(occupied),
            "cells": occupied,
        },
    }

    lines = [
        "# Synchronized racer composition proof",
        "",
        f"IDs: {report['ids']}",
        f"Selectors: {selectors}",
        f"Primary masks exact: {mask_checks['primary_exact']}",
        f"Companion masks exact before F12B/F140 gates: {mask_checks['companion_raw_exact']}",
        f"Companion gates: {report['companion_gate_words']} -> {companion_enabled}",
        (
            "Occupied staging sources exact: "
            f"{exact}/{len(occupied)}; destinations present {destinations}/{len(occupied)}"
        ),
        "",
    ]
    for row in occupied:
        if not row["source_exact"]:
            lines.append(
                f"- mismatch row {row['row']} col {row['column']} {row['player']} "
                f"{row['choice']}: expected {row['expected_source']} at {row['vram_word']}; "
                f"actual {row['actual_sources']}"
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
