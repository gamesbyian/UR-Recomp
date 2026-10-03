#!/usr/bin/env python3
"""Measure the stock attract/demo cycle from MAIN_MENU with no input.

Decision served: the baseline modern requirement to preserve original
attract/demo behaviour (and leave a hook for a local-run showcase) needs the
stock idle timeout, sequence and exit behaviour.

Method: run ``tests/input/attract-cycle.script`` (clean boot, MAIN_MENU, then
idle) through snesref with its per-frame low-WRAM change trace, reconstruct
``7E:009F`` (menu), ``7E:0313`` (in race), ``7E:00CE`` (track) and ``7E:00D0``
(tour row) for every frame, and segment the timeline into cycles. A second run,
``tests/input/attract-exit.script``, presses Start mid-demo.

``segment`` is pure and unit-tested; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CYCLE_SCRIPT = ROOT / "tests/input/attract-cycle.script"
EXIT_SCRIPT = ROOT / "tests/input/attract-exit.script"
FIELDS = {"menu": 0x009F, "in_race": 0x0313, "track": 0x00CE, "tour_row": 0x00D0}
MAIN_MENU, TITLE = 0xD7, 0x84


def frame_states(trace_lines) -> dict[int, dict]:
    """Per-frame values of FIELDS from snesref's changed-byte jsonl trace."""
    current = {k: 0 for k in FIELDS}
    by_addr = {a: k for k, a in FIELDS.items()}
    states: dict[int, dict] = {}
    last = 0
    for line in trace_lines:
        e = json.loads(line)
        f = e["f"]
        if f != last:
            for g in range(last, f):
                states[g] = dict(current)
            last = f
        key = by_addr.get(int(e["adr"], 16))
        if key:
            current[key] = int(e["val"], 16)
    states[last] = dict(current)
    return states


STABLE_FRAMES = 30  # DP $9F doubles as scratch; a real MAIN_MENU holds 0xD7 for many frames


def stable_main_menu_entries(states: dict[int, dict]) -> set[int]:
    frames = sorted(states)
    entries, run_start = set(), None
    for f in frames:
        s = states[f]
        if s["menu"] == MAIN_MENU and s["in_race"] == 0:
            if run_start is None:
                run_start = f
            if f - run_start + 1 == STABLE_FRAMES:
                entries.add(run_start)
        else:
            run_start = None
    return entries


def segment(states: dict[int, dict]) -> list[dict]:
    """Cycles: MAIN_MENU shown -> TITLE -> demo race (in_race=1) -> back to MAIN_MENU."""
    frames = sorted(states)
    entries = stable_main_menu_entries(states)
    cycles, cur = [], None
    for f in frames:
        s = states[f]
        if f in entries:
            if cur:
                cur["next_main_menu_frame"] = f
                cycles.append(cur)
            cur = {"main_menu_frame": f}
        elif cur is not None:
            if s["menu"] == TITLE and "title_frame" not in cur and s["in_race"] == 0:
                cur["title_frame"] = f
            if s["in_race"] == 1 and "race_start_frame" not in cur:
                cur.update(race_start_frame=f, track=s["track"], tour_row=s["tour_row"])
            if "race_start_frame" in cur and "race_end_frame" not in cur and (s["in_race"] != 1 or s["menu"] == TITLE):
                cur["race_end_frame"] = f
    for c in cycles:
        c["idle_before_title_frames"] = c.get("title_frame", 0) - c["main_menu_frame"]
        c["title_to_race_frames"] = c.get("race_start_frame", 0) - c.get("title_frame", 0)
        c["demo_race_frames"] = c.get("race_end_frame", 0) - c.get("race_start_frame", 0)
        c["cycle_frames"] = c["next_main_menu_frame"] - c["main_menu_frame"]
    return cycles


def run(snesref: Path, core: Path, rom: Path, script: Path, workdir: Path) -> list[str]:
    trace = workdir / "trace.jsonl"
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
               SNESREF_SCRIPT=str(script), SNESREF_TRACE_FILE=str(trace), SNESREF_DUMP_DIR=str(workdir))
    with open(workdir / "snesref.log", "w") as log:
        subprocess.run([str(snesref), str(core), str(rom)], env=env, cwd=workdir,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    return trace.read_text().splitlines()


def press_frame(log_text: str) -> int | None:
    for line in log_text.splitlines():
        if " press start " in line:
            return int(line.split("f=")[1].split()[0])
    return None


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument("--core", type=Path, default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/attract-cycle.json")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "cycle", Path(td) / "exit"
        a.mkdir(), b.mkdir()
        cycles = segment(frame_states(run(args.snesref, args.core, args.rom, CYCLE_SCRIPT, a)))
        exit_states = frame_states(run(args.snesref, args.core, args.rom, EXIT_SCRIPT, b))
        pressed = press_frame((b / "snesref.log").read_text())
    after = {k: v for k, v in exit_states.items() if pressed is not None and k >= pressed}
    title_after = next((f for f in sorted(after) if after[f]["menu"] == TITLE), None)
    menu_after = next((f for f in sorted(after) if after[f]["menu"] == MAIN_MENU and after[f]["in_race"] == 0), None)
    idle = sorted({c["idle_before_title_frames"] for c in cycles})
    checks = {
        "at_least_three_cycles": len(cycles) >= 3,
        "idle_timeout_constant": len(idle) == 1,
        "every_cycle_runs_a_demo_race": all(c["demo_race_frames"] > 0 for c in cycles),
        "demo_tracks_vary": len({(c["tour_row"], c["track"]) for c in cycles}) > 1,
        "start_exits_demo_via_title": pressed is not None and title_after is not None and menu_after is not None,
    }
    report = {
        "schema_version": 1,
        "question": "What does stock Uniracers do when MAIN_MENU is left idle?",
        "harness": "snesref + pinned snes9x-libretro, clean boot, no input; per-frame low-WRAM trace",
        "fixtures": [str(CYCLE_SCRIPT.relative_to(ROOT)), str(EXIT_SCRIPT.relative_to(ROOT))],
        "frame_rate_note": "frames are guest NTSC frames (~60.1/s)",
        "cycles": cycles,
        "start_exit": {"press_frame": pressed, "title_frame": title_after, "main_menu_frame": menu_after},
        "observations": [
            "each cycle fades MAIN_MENU to the title screen (0x84), loads a course, and plays a split-screen two-player demo race",
            "the demo course advances between cycles; HUD names in the first demo were AMY and ALICE, which do not match $017D/$017F (3/1), so the demo keeps racer identity elsewhere",
            "DP $9F is reused as scratch during the blanked course load, so short-lived values between title and race are not menu states",
        ],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    for c in cycles:
        print(c)
    print(json.dumps(checks, indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
