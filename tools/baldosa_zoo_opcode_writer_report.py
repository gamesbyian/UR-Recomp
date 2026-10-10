#!/usr/bin/env python3
"""Cross-check reference SNES CPU opcode-delta logs against immutable Zoo dumps.

The opcode PC is a candidate instruction/synchronous-side-effect scope, not
automatic proof that an observed address was stored by that CPU instruction.
No adjustment of guest frame phase, gameplay rules or QA event acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

WRITER = re.compile(
    r"ZOOPCWRITE f=(\d+) v=(\d+) pc=([0-9A-Fa-f]{6}) "
    r"addr=([0-9A-Fa-f]{4}) old=([0-9A-Fa-f]{2}) new=([0-9A-Fa-f]{2})"
)


def parse(log: str) -> list[dict]:
    rows = []
    for match in WRITER.finditer(log):
        f, v, pc, addr, old, new = match.groups()
        if old == new:
            raise ValueError(f"opcode write trace contains unchanged byte at {addr}")
        rows.append({
            "original_icpu_frame": int(f),
            "ppu_v_counter": int(v),
            "guest_pc": f"{pc[:2]}:{pc[2:].upper()}",
            "wram_address": f"7E:{addr.upper()}",
            "old": old.upper(), "new": new.upper(),
        })
    return rows


def analyze(log: str, original: Path, *, scene_entry_frame: int) -> dict:
    if scene_entry_frame < 1:
        raise ValueError("independently measured original scene-entry frame required")
    writes = parse(log)
    if not writes:
        raise ValueError("reference opcode writer trace returned no writes")
    before = (original / "boundary-05156.wram.bin").read_bytes()
    after = (original / "boundary-05157.wram.bin").read_bytes()
    if len(before) != 0x20000 or len(after) != 0x20000:
        raise ValueError("source boundary WRAM dumps must be complete 128 KiB")
    delta = {i: [before[i], after[i]] for i in range(len(before))
             if before[i] != after[i]}
    # Include nearby CPU frame counter offsets because Snes9x records this
    # at CPU dispatch and the host dumped state at frame boundaries.
    near = {scene_entry_frame + f for f in (5154, 5155, 5156, 5157, 5158)}
    scoped = [w for w in writes if w["original_icpu_frame"] in near]
    relevant = [w for w in scoped
                if int(w["wram_address"][3:], 16) in delta]
    addresses = sorted({
        int(w["wram_address"][3:], 16) for w in relevant})
    if not relevant:
        raise ValueError("no traced opcode scope wrote a byte changed at +5157")
    by_pc = Counter(w["guest_pc"] for w in relevant)
    return {
        "schema": "UR-QA01-ZOO-ORIGINAL-MENU-WRITER-PC/1",
        "source": "in-place traced original Snes9x opcode dispatch; pristine 2014 inputs and ROM; QA-only temporary emulator instrument",
        "source_original_scene_entry_frame": scene_entry_frame,
        "frame_window": sorted(near),
        "unaltered_source_original_boundary_frame_deltas": {
            "relative_frames": [5156, 5157],
            "wram_differing_bytes": len(delta),
            "addresses": [f"7E:{a:04X}" for a in sorted(delta)],
        },
        "matched_changed_address_count": len(addresses),
        "matched_changed_addresses": [f"7E:{a:04X}" for a in addresses],
        "scoped_opcode_events": relevant,
        "candidate_pc_counts": dict(sorted(by_pc.items())),
        "unattributed_changed_address_count": len(delta)-len(addresses),
        "interpretation_guardrail": (
            "Opcode-level pre/post memory differences identify a candidate "
            "executed instruction or synchronous side-effect scope, not a "
            "proven individual STA/MVN or host/emulator root cause; stage "
            "classification is not an accepted event. CPU trace frame numbers "
            "may require a separate host boundary adjudication."
        ),
        "complete_event_qa_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--scene-entry-frame", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    d = analyze(args.log.read_text(encoding="utf-8"),
                args.original, scene_entry_frame=args.scene_entry_frame)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: d[k] for k in (
        "unaltered_source_original_boundary_frame_deltas",
        "matched_changed_address_count", "candidate_pc_counts",
        "unattributed_changed_address_count", "complete_event_qa_credit")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
