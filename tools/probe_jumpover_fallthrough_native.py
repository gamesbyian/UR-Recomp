#!/usr/bin/env python3
"""Fresh-process Jumpover fall-through fixture: snesref reference vs native recomp.

Policy (docs/JUMPOVER-FALLTHROUGH-REGRESSION.md, "Anchor route decision"): the
recovered SMVs' mid-update Snes9x 1.51 freezes are not admitted as native
anchors. Instead every case boots a fresh process from the recovered real
"All Silvers - No Hunter" SRAM, reaches the Jumpover race through the stock
menus, holds Right, seeds one game-written persistent variable (P1's boost
meter, ``7E:11CF``, normally written by landed-stunt rewards) once at a frame
boundary, and splices the recovered right-route SMV's own controller stream.

The same scene-keyed script drives both cores; per-frame P1 state is dumped
over the event window and compared exactly. Each route's matrix (``ROUTES``)
holds a fall-through case, an adjacent seed lead that rides normally, and the
PHYS-01 direction-matched control (shoulder released on the last acting
movie sample before the lip, ``CONTROL_SAMPLE``).
The right route also keeps the ordinary lead on its other side.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from probe_jumpover_fallthrough import controller_samples  # noqa: E402

GLITCHES = ROOT / "reference/imported/reverse-engineering/dessyreqt/Glitches"
MOVIES = {
    "right": GLITCHES / "Jumpover - Jump through halfpipe.smv",
    "left": GLITCHES / "Jumpover - Jump through halfpipe - left.smv",
}
DEFAULT_SRAM = ROOT / "reference/imported/reverse-engineering/dessyreqt/SRAM/All Silvers - No Hunter.srm"
# Per-route approach from race entry: (frames after race entry, held mask).
# Right: hold Right into the halfpipe. Left: hold Right, jump the halfpipe,
# turn back with Left on the far lip, and release Left for three frames to
# place the return approach on the movie's two-frame input phase.
ROUTES = {
    "right": {
        "approach": [(0, 0x0080)],
        "splice_offset": 362,
        "boost": 72,
        "shoulder": 0x0800,
        "cases": [("seed-35", 35, False), ("seed-36", 36, False), ("seed-37", 37, False),
                  ("seed-36-shoulder-41", 36, True)],
    },
    "left": {
        "approach": [(0, 0x0080), (372, 0x0081), (392, 0x0080), (436, 0x0040),
                     (457, 0x0000), (460, 0x0040)],
        "splice_offset": 478,
        "boost": 120,
        "shoulder": 0x0400,
        "cases": [("seed-21", 21, False), ("seed-22", 22, False),
                  ("seed-21-shoulder-41", 21, True)],
    },
}
# PHYS-01's control releases the shoulder on sample 42, the last acting input
# before the lip. Input acts every second frame; from a fresh boot the acting
# samples are odd (the 1.51 anchor's were even), so the equivalent sample is 41.
CONTROL_SAMPLE = 41
BOOST_ADDR = 0x11CF
EXTENSION_FRAMES = 60
WINDOW = (36, 110)          # dumped movie frames (state after frame f)
FALL_Y = 1000               # Y beyond any ordinary halfpipe floor contact
JUMPOVER_TRACK_ID = 19      # course:20 (stream index - 1)

# Boot -> 1P -> rider -> Bounder (tour option 3) -> Jumpover (slot 4).
MENU_SCRIPT = """\
until 009F == D7 3600
wait 60
press a 2
until 009F == 3C 1200
wait 60
press a 2
until 009F == 6D 1200
wait 60
press down 2
wait 20
press right 2
wait 20
until 009B == 03 120
press a 2
until 009F == F6 1200
wait 60
press down 2
wait 12
press down 2
wait 12
press down 2
wait 12
press down 2
wait 20
until 009B == 04 120
press a 2
until 009F == 16 1200
wait 60
press a 2
until 0313 == 01 1800
dump race-entered
"""

FIELDS = {  # name: (WRAM offset, signed, mask)
    "x": (0x0411, False, None),
    "y": (0x0415, False, None),
    "x_speed": (0x04B7, True, None),
    "y_speed": (0x04BB, True, None),
    "pitch": (0x04C7, False, 0x3F),
    "air_time": (0x0545, False, 0xFF),
    "contact_word": (0x0E95, False, None),
    "boost": (0x11CF, False, None),
}


def snes9x_to_mask(word: int) -> int:
    """Snes9x 1.51 joypad word (B=0x8000 ... R=0x0010) -> 12-bit script mask (B=1 ... R=0x800)."""
    return sum(1 << i for i in range(12) if word & (0x8000 >> i))


def movie_masks(route: str, control_sample: int | None = None) -> list[int]:
    masks = [snes9x_to_mask(w) for w in controller_samples(MOVIES[route].read_bytes())]
    masks += [masks[-1]] * EXTENSION_FRAMES
    if control_sample is not None:
        masks[control_sample] &= ~ROUTES[route]["shoulder"]
    return masks


def input_events(masks: list[int], race_frame: int, splice: int, approach) -> list[tuple[int, int, int]]:
    """Run-length events: the approach (offsets from race entry), then the movie from `splice`."""
    if splice <= race_frame:
        raise ValueError("splice must follow race entry")
    if isinstance(approach, int):
        approach = [(0, approach)]
    points = [(race_frame + off, mask) for off, mask in approach if race_frame + off < splice]
    if not points or points[0][0] != race_frame:
        raise ValueError("approach must start at race entry")
    events = [(a, b - a, m) for (a, m), (b, _) in zip(points, points[1:] + [(splice, None)])]
    run = None
    for i, mask in enumerate(masks):
        frame = splice + i
        if run and run[2] == mask:
            run[1] += 1
        else:
            if run:
                events.append(tuple(run))
            run = [frame, 1, mask]
    events.append(tuple(run))
    return events


def fixture_script(race_frame: int, splice: int, lead: int, boost: int) -> str:
    """Menu route, one frame-boundary boost seed `lead` frames before the splice, per-frame dumps."""
    seed = splice - 1 - lead
    if seed <= race_frame:
        raise ValueError("boost seed must follow race entry")
    lines = [MENU_SCRIPT.rstrip("\n"), f"wait {seed - race_frame}",
             f"poke {BOOST_ADDR:04X} {boost & 0xFF:02x}{boost >> 8:02x}"]
    cur = seed + 2  # a poke holds one frame plus the trailing idle frame
    for f in range(WINDOW[0], WINDOW[1] + 1):
        target = splice + f
        if target > cur:
            lines.append(f"wait {target - cur}")
            cur = target
        lines.append(f"dump m{f:03d}")
    lines.append("quit")
    return "\n".join(lines) + "\n"


def read_p1(wram: bytes) -> dict:
    out = {}
    for name, (addr, signed, mask) in FIELDS.items():
        value = struct.unpack_from("<h" if signed else "<H", wram, addr)[0]
        out[name] = value & mask if mask is not None else value
    return out


def classify(series: dict[int, dict]) -> dict:
    """Outcome and contact frames from an event-window series (keys = movie frames)."""
    if not series:
        raise ValueError("empty series")
    frames = sorted(series)
    contacts = [f for f in frames if series[f]["air_time"] == 0]
    ranges = []
    for f in contacts:
        if ranges and ranges[-1][1] == f - 1:
            ranges[-1][1] = f
        else:
            ranges.append([f, f])
    max_y = max(series[f]["y"] for f in frames)
    return {
        "outcome": "fall_through" if max_y > FALL_Y else "ordinary",
        "max_y": max_y,
        "contact_ranges": ranges,
        "final": series[frames[-1]],
        "series_sha256": hashlib.sha256(json.dumps([series[f] for f in frames], sort_keys=True).encode()).hexdigest(),
    }


def first_divergence(ref: dict[int, dict], nat: dict[int, dict]):
    for f in sorted(set(ref) | set(nat)):
        if ref.get(f) != nat.get(f):
            return {"frame": f, "fields": sorted(k for k in FIELDS if (ref.get(f) or {}).get(k) != (nat.get(f) or {}).get(k))}
    return None


WRAM_SIZE = 0x20000


class EvidenceError(RuntimeError):
    pass


def load_series(directory: Path) -> dict[int, dict]:
    """Every window frame must be a full WRAM image of an active Jumpover race.

    A missing or short dump fails the run instead of being skipped, so two
    engines can never agree by both omitting the same frame.
    """
    out = {}
    for f in range(WINDOW[0], WINDOW[1] + 1):
        path = directory / f"m{f:03d}.wram.bin"
        if not path.exists():
            raise EvidenceError(f"missing dump {path}")
        wram = path.read_bytes()
        if len(wram) != WRAM_SIZE:
            raise EvidenceError(f"{path}: {len(wram)} bytes, expected a {WRAM_SIZE}-byte WRAM image")
        if wram[0x00CE] != JUMPOVER_TRACK_ID or wram[0x0313] != 0x01:
            raise EvidenceError(f"{path}: not an active Jumpover race "
                                f"(7E:00CE={wram[0x00CE]}, 7E:0313={wram[0x0313]})")
        out[f] = read_p1(wram)
    return out


def race_entry_frame(log: str) -> int | None:
    m = re.search(r"script f=(\d+) dump race-entered", log)
    return int(m.group(1)) if m else None


def run_reference(work: Path, args, script: Path, events) -> str:
    inp = work / "ref.input"
    # A zero mask is a gap: no event, no buttons (native rejects mask-0 events).
    inp.write_text("".join(f"{a}:{b}:{c:x}\n" for a, b, c in events if c))
    out = work / "ref"
    out.mkdir(exist_ok=True)
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_WRAM_FILL="0", SNESREF_SRAM_IN=str(args.sram),
               SNESREF_SCRIPT=str(script), SNESREF_INPUT_FILE=str(inp), SNESREF_DUMP_DIR=str(out))
    # snesref writes snesref_audio.wav / snesref_trace.jsonl into its cwd.
    proc = subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env,
                          capture_output=True, text=True, timeout=600, cwd=work)
    return proc.stdout + proc.stderr


def run_native(work: Path, args, script: Path, events, shift: int) -> str:
    inp = work / "native.input"
    inp.write_text("".join(f"{a + shift}:{b}:{c:x}:0\n" for a, b, c in events if c))
    saves = args.native.parent / "saves"
    backup = saves.with_name("saves.jumpover-probe-backup")
    if backup.exists():
        raise RuntimeError(f"stale probe backup exists: {backup}")
    if saves.exists():
        saves.rename(backup)
    try:
        saves.mkdir()
        shutil.copyfile(args.sram, saves / "save.srm")
        out = work / "native"
        out.mkdir(exist_ok=True)
        env = dict(os.environ, SDL_AUDIODRIVER="dummy", UR_EXECUTION_MODE="authentic",
                   SNESRECOMP_DUMP_DIR=str(out), SNESRECOMP_INPUT_FILE=str(inp),
                   UR_RECOMP_USER_DATA_ROOT=str(work / "user-data"))
        proc = subprocess.run(["xvfb-run", "-a", str(args.native), str(args.rom), "--script", str(script)],
                              env=env, capture_output=True, text=True, timeout=900, cwd=work)
        return proc.stdout + proc.stderr
    finally:
        shutil.rmtree(saves, ignore_errors=True)
        if backup.exists():
            backup.rename(saves)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, required=True, help="snes9x libretro core")
    ap.add_argument("--native", type=Path, required=True, help="native recomp executable")
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--sram", type=Path, default=DEFAULT_SRAM)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--routes", default="right,left")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)
    for name in ("snesref", "core", "native", "rom", "sram", "work_dir"):
        setattr(args, name, getattr(args, name).resolve())

    ref_race = None
    shift = None
    routes = {}
    ok = True
    for route in args.routes.split(","):
        cfg = ROUTES[route]
        results = []
        for name, lead, control in cfg["cases"]:
            masks = movie_masks(route, CONTROL_SAMPLE if control else None)
            work = args.work_dir / f"{route}-{name}"
            shutil.rmtree(work, ignore_errors=True)
            work.mkdir(parents=True)
            script = work / "fixture.script"

            def prepare(race):
                splice = race + cfg["splice_offset"]
                script.write_text(fixture_script(race, splice, lead, cfg["boost"]))
                return input_events(masks, race, splice, cfg["approach"])

            # The reference race-entry frame fixes the absolute input timeline.
            events = prepare(ref_race or 1088)
            ref_log = run_reference(work, args, script, events)
            rf = race_entry_frame(ref_log)
            if rf is None:
                raise SystemExit(f"reference did not reach the race:\n{ref_log[-2000:]}")
            if rf != (ref_race or 1088):
                events = prepare(rf)
                ref_log = run_reference(work, args, script, events)
            ref_race = rf
            nat_log = run_native(work, args, script, events, shift or 0)
            nf = race_entry_frame(nat_log)
            if nf is None:
                raise SystemExit(f"native did not reach the race:\n{nat_log[-2000:]}")
            if nf - rf != (shift or 0):
                # Native boots through the menus on a different frame; the
                # script adapts through `until`, the absolute input is shifted.
                shift = nf - rf
                nat_log = run_native(work, args, script, events, shift)
                if race_entry_frame(nat_log) - rf != shift:
                    raise SystemExit("native race entry is not deterministic")
            ref_series, nat_series = load_series(work / "ref"), load_series(work / "native")
            case = {
                "case": name,
                "seed_lead": lead,
                "shoulder_released_on_sample": CONTROL_SAMPLE if control else None,
                "reference": classify(ref_series),
                "native": classify(nat_series),
                "first_divergence": first_divergence(ref_series, nat_series),
            }
            results.append(case)
            ok &= case["first_divergence"] is None and case["reference"] == case["native"]
            print(json.dumps({"route": route, "case": name, "reference": case["reference"]["outcome"],
                              "native": case["native"]["outcome"],
                              "first_divergence": case["first_divergence"]}), flush=True)
        outcomes = [c["reference"]["outcome"] for c in results]
        if "fall_through" not in outcomes or "ordinary" not in outcomes:
            print(f"{route}: matrix needs a fall-through case and an ordinary control", file=sys.stderr)
            ok = False
        routes[route] = {
            "movie_sha256": hashlib.sha256(MOVIES[route].read_bytes()).hexdigest(),
            "approach_from_race_entry": [{"frame_offset": off, "mask": f"0x{mask:03x}"} for off, mask in cfg["approach"]],
            "splice_offset_frames": cfg["splice_offset"],
            "boost_seed_value": cfg["boost"],
            "cases": results,
        }

    evidence = {
        "schema_version": 2,
        "kind": "jumpover-fallthrough-native-fixture",
        "qualification": ("controlled-state parity, not an input-only stock run: each case "
                          "writes P1's boost meter (7E:11CF) once at a frame boundary; "
                          "everything else comes from a fresh boot with the recovered SRAM"),
        "course": {"id": "course:20", "name": "Jumpover", "track_id": JUMPOVER_TRACK_ID},
        "sram_sha256": hashlib.sha256(args.sram.read_bytes()).hexdigest(),
        "reference": "snesref + snes9x libretro core (fresh boot, SNESREF_WRAM_FILL=0)",
        "native": "UR_EXECUTION_MODE=authentic, same scene-keyed script",
        "reference_race_entry_frame": ref_race,
        "native_race_entry_offset_frames": shift,
        "boost_seed": {"wram": "7E:11CF",
                       "note": "one frame-boundary write `seed_lead` frames before the splice; stands in for an earlier landed-stunt reward"},
        "window_movie_frames": list(WINDOW),
        "fall_y": FALL_Y,
        "routes": routes,
    }
    if args.json_out:
        args.json_out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
