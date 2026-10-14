#!/usr/bin/env python3
"""Game-frame versus host-frame census from the source frame counter 7E:00C6.

``80:FAC9`` waits for the next vblank on ``$4212`` and ``80:FADF`` then
decrements direct-page ``$C6`` modulo 32 (reloading ``$1F`` when it goes
negative). Each decrement is therefore one completed pass through the game's
vblank wait: one *game* frame. Host frames without a decrement are lag frames.
Counting decrements between dense dumps on each engine for the same controller
stream measures where native and original spend different numbers of host
frames per game frame, without any instrumentation of either engine.

Sampling must be dense enough that at most 31 decrements fall between two
samples (the counter period is 32). The default 4-frame spacing is safe
because the wait admits at most one pass per host frame.

Observation only: it grants no gameplay, original-parity or release credit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import qa_frontier_original_crosscheck as xc  # noqa: E402

SCHEMA = "ur-lag-frame-census/1"
COUNTER = 0x00C6
MENU = 0x009F
PERIOD = 32


def passes(pages: list[bytes]) -> list[int]:
    """Counter decrements between consecutive samples (mod the 32 period)."""
    return [(a[COUNTER] - b[COUNTER]) % PERIOD for a, b in zip(pages, pages[1:])]


def census(frames: list[int], engines: dict[str, list[bytes]]) -> dict:
    if len(frames) < 2 or any(b - a < 1 or b - a > PERIOD - 1 for a, b in zip(frames, frames[1:])):
        raise ValueError("samples must be increasing and closer than the counter period")
    counted = {name: passes(pages) for name, pages in engines.items()}
    for name, steps in counted.items():
        for (a, b), n in zip(zip(frames, frames[1:]), steps):
            if n > b - a:
                raise ValueError(f"{name}: {n} passes in {b - a} host frames is impossible")
    names = sorted(engines)
    windows = []
    for i, (a, b) in enumerate(zip(frames, frames[1:])):
        row = {name: counted[name][i] for name in names}
        if len(set(row.values())) > 1:
            windows.append({"host_frames": [a, b],
                            "menu": {name: engines[name][i + 1][MENU] for name in names},
                            "game_frames": row})
    host = frames[-1] - frames[0]
    return {"schema": SCHEMA, "host_frames": host,
            "first_sample": frames[0], "last_sample": frames[-1],
            "game_frames": {name: sum(counted[name]) for name in names},
            "lag_frames": {name: host - sum(counted[name]) for name in names},
            "differing_windows": windows,
            "release_gate_credit": 0, "original_native_parity_claimed": False}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=ROOT / "tests/input/two-player-first-race.input")
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, action="append", required=True,
                    help="reference libretro core; repeat for several")
    ap.add_argument("--native-exe", type=Path)
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--frames", default="2-1126/4")
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("refuse to overwrite a prior census")
    frames = xc.parse_frames(args.frames)
    control = args.input.read_text(encoding="utf-8")
    engines, identity = {}, {}
    for core in args.core:
        ref = xc.Original(args.snesref, core, args.rom)
        name = core.stem
        dumps = ref.run(control, frames, args.work / name)
        engines[name] = [dumps[f].read_bytes() for f in frames]
        identity[name] = ref.identity
    if args.native_exe:
        dumps = xc.native_run(args.native_exe, args.rom.resolve(), control, frames,
                              args.work / "native")
        engines["native"] = [dumps[f].read_bytes() for f in frames]
        identity["native"] = {"executable_sha256": xc.sha256(args.native_exe)}
    result = census(frames, engines)
    result["identity"] = identity
    result["input_sha256"] = xc.sha256(args.input)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("game_frames", "lag_frames")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
