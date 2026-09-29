#!/usr/bin/env python3
"""Reconstruct selected Uniracers state from a snesref low-WRAM JSONL trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

WATCH = {
    0x009F, 0x0313, 0x00CE,
    0x0411, 0x0412, 0x0415, 0x0416,
    0x04B7, 0x04B8, 0x04BB, 0x04BC,
    0x0545, 0x04C7, 0x04C8,
}


def u16(state: dict[int, int], addr: int) -> int:
    return state.get(addr, 0) | (state.get(addr + 1, 0) << 8)


def s16(state: dict[int, int], addr: int) -> int:
    v = u16(state, addr)
    return v - 0x10000 if v & 0x8000 else v


def snapshot(frame: int, state: dict[int, int]) -> dict:
    return {
        "frame": frame,
        "menu": state.get(0x009F, 0),
        "inRace": state.get(0x0313, 0),
        "track": state.get(0x00CE, 0),
        "x": u16(state, 0x0411),
        "y": u16(state, 0x0415),
        "vx": s16(state, 0x04B7),
        "vy": s16(state, 0x04BB),
        "air": state.get(0x0545, 0),
        "pitch": u16(state, 0x04C7) & 0x3F,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", type=Path)
    ap.add_argument("--checkpoint", action="append", type=int, default=[])
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--tsv-out", type=Path)
    args = ap.parse_args()

    cps = sorted(set(args.checkpoint))
    cp_set = set(cps)
    max_cp = max(cps, default=-1)
    state: dict[int, int] = {}
    snapshots: list[dict] = []
    transitions = {"menu": [], "inRace": []}

    current_frame = None

    def emit_checkpoint(f: int) -> None:
        if f in cp_set and not any(x["frame"] == f for x in snapshots):
            snapshots.append(snapshot(f, state))

    for raw in args.trace.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        rec = json.loads(raw)
        f = int(rec["f"])
        if current_frame is None:
            current_frame = f
        if f != current_frame:
            emit_checkpoint(current_frame)
            # Any requested checkpoint between changed frames sees the same
            # stable WRAM state.
            for cp in cps:
                if current_frame < cp < f:
                    emit_checkpoint(cp)
            current_frame = f

        addr = int(rec["adr"], 16)
        old = int(rec["old"], 16)
        val = int(rec["val"], 16)
        if addr in WATCH:
            state[addr] = val
        if addr == 0x009F and old != val:
            transitions["menu"].append({"frame": f, "old": old, "val": val})
        elif addr == 0x0313 and old != val:
            transitions["inRace"].append({"frame": f, "old": old, "val": val})

    if current_frame is not None:
        emit_checkpoint(current_frame)
        for cp in cps:
            if current_frame < cp <= max_cp:
                emit_checkpoint(cp)

    snapshots.sort(key=lambda x: x["frame"])
    first_in_race = next(
        (x["frame"] for x in transitions["inRace"] if x["val"] == 1),
        None,
    )
    first_results = next(
        (x["frame"] for x in transitions["menu"] if x["val"] == 0x99),
        None,
    )
    report = {
        "checkpoints": snapshots,
        "transitions": transitions,
        "first_in_race_frame": first_in_race,
        "first_race_results_frame": first_results,
    }

    lines = []
    for s in snapshots:
        lines.append(
            f'{s["frame"]}\tmenu=0x{s["menu"]:02X}\tinRace=0x{s["inRace"]:02X}'
            f'\ttrack={s["track"]}\tx={s["x"]}\ty={s["y"]}'
            f'\tvx={s["vx"]}\tvy={s["vy"]}\tair={s["air"]}\tpitch={s["pitch"]}'
        )
    print("\n".join(lines))
    print(f"first_in_race_frame={first_in_race}")
    print(f"first_race_results_frame={first_results}")

    if args.tsv_out:
        args.tsv_out.parent.mkdir(parents=True, exist_ok=True)
        args.tsv_out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
