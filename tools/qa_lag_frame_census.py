#!/usr/bin/env python3
"""Game-frame versus host-frame census from the source frame counter 7E:00C6.

``80:FAC9`` waits for the next vblank on ``$4212`` and ``80:FADF`` then
decrements direct-page ``$C6`` modulo 32 (reloading ``$1F`` when it goes
negative). Each decrement is therefore one completed pass through the game's
vblank wait: one *game* frame. Where the game passes this wait every frame
(menus, screen loads) a host frame without a decrement is a lag frame; during
races and demos the wait is not used, so those frames are not lag.
Counting decrements between dense dumps on each engine for the same controller
stream measures where native and original spend different numbers of host
frames per game frame, without any instrumentation of either engine.

Other code can also write ``$C6`` (the direct-page restore does). A window in
which any engine shows more decrements than host frames is excluded for every
engine and listed, so the totals compare equal host-frame spans.

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
    names = sorted(engines)
    windows, excluded, host = [], [], 0
    totals = {name: 0 for name in names}
    for i, (a, b) in enumerate(zip(frames, frames[1:])):
        row = {name: counted[name][i] for name in names}
        menus = {name: engines[name][i + 1][MENU] for name in names}
        # More passes than host frames cannot be vblank waits: something else
        # (e.g. the direct-page restore) rewrote $C6. Exclude the window for
        # EVERY engine so the remaining totals stay comparable.
        if any(n > b - a for n in row.values()):
            excluded.append({"host_frames": [a, b], "menu": menus, "raw_steps": row})
            continue
        host += b - a
        for name in names:
            totals[name] += row[name]
        if len(set(row.values())) > 1:
            windows.append({"host_frames": [a, b], "menu": menus, "game_frames": row})
    if not host:
        raise ValueError("no window where every engine's counter is a vblank-wait count")
    return {"schema": SCHEMA, "host_frames": host,
            "first_sample": frames[0], "last_sample": frames[-1],
            "game_frames": totals,
            "frames_without_vblank_wait_pass": {name: host - totals[name] for name in names},
            "differing_windows": windows,
            "excluded_counter_rewrites": excluded,
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
    print(json.dumps({k: result[k] for k in ("game_frames", "frames_without_vblank_wait_pass")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
