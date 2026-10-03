#!/usr/bin/env python3
"""Verify the 1P race/circuit/stunt result screens from the historical 2014 movie.

Decision served: the UI atlas listed RESULT_CIRCUIT (0xBC) and RESULT_STUNT
(0x18, summing 0x2F) as historical bot labels only. The Dessyreqt movie still
plays in sync on the pinned modern core through its first Crawler tracks
(Dragster race, Zoom Zoo circuit, Bowl stunt), so it can drive all three result
families without a bespoke driving policy.

Method: extract the movie input and anchored SRAM, replay through snesref with
the per-frame low-WRAM trace, find the stable ``7E:009F`` runs after each race,
then dump one frame inside each result run and decode its titles/labels.

``result_runs`` is pure and unit-tested; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import extract_menu_visual_language as mvl
import probe_attract_cycle as trace
import probe_tier_opponents as tier

ROOT = Path(__file__).resolve().parents[1]
SMV = ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
HORIZON = 12100
RESULT_MENUS = {0x99: "RESULT_RACE", 0xBC: "RESULT_CIRCUIT", 0x2F: "RESULT_STUNT summing", 0x18: "RESULT_STUNT"}
EXPECT = {0x99: ["DRAGSTER", "COMPLETE"], 0xBC: ["LAPS ON ZOOM ZOO", "BEST LAP"], 0x2F: ["BOWL"], 0x18: ["BOWL", "QUALIFY"]}
MIN_RUN = 8


def result_runs(states: dict[int, dict]) -> list[dict]:
    """Stable (>= MIN_RUN frames) runs of a result menu value, with the next stable menu after them."""
    runs, cur = [], None
    for f in sorted(states):
        key = states[f]["menu"]
        if cur and cur["menu"] == key:
            cur["end"] = f
            continue
        if cur and cur["end"] - cur["start"] + 1 >= MIN_RUN:
            runs.append(cur)
        cur = {"menu": key, "start": f, "end": f, "in_race": states[f]["in_race"]}
    if cur and cur["end"] - cur["start"] + 1 >= MIN_RUN:
        runs.append(cur)
    out = []
    for i, r in enumerate(runs):
        if r["menu"] in RESULT_MENUS:
            nxt = next((n for n in runs[i + 1:] if n["menu"] not in (0x84,) and n["menu"] not in RESULT_MENUS), None)
            out.append({**r, "state": RESULT_MENUS[r["menu"]], "next_menu": None if nxt is None else nxt["menu"]})
    return out


def snesref(args, workdir: Path, script: Path, trace_file: Path | None = None) -> None:
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
               SNESREF_SRAM_IN=str(workdir / "anchored.srm"), SNESREF_INPUT_FILE=str(workdir / "movie.input"),
               SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(workdir))
    if trace_file:
        env["SNESREF_TRACE_FILE"] = str(trace_file)
    with open(workdir / f"{script.stem}.log", "w") as log:
        subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=workdir,
                       stdout=log, stderr=subprocess.STDOUT, check=True)


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument("--core", type=Path, default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/result-screens-probe.json")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        subprocess.run([sys.executable, str(ROOT / "tools/extract_smv_input.py"), str(SMV),
                        "--input-out", str(work / "movie.input"), "--sram-out", str(work / "anchored.srm"),
                        "--sram-size", "8192", "--json-out", str(work / "movie.json")],
                       check=True, stdout=subprocess.DEVNULL)
        (work / "scan.script").write_text(f"wait {HORIZON}\nquit\n")
        snesref(args, work, work / "scan.script", work / "trace.jsonl")
        runs = result_runs(trace.frame_states((work / "trace.jsonl").read_text().splitlines()))
        lines, frame = [], 0
        for r in runs:
            target = (r["start"] + r["end"]) // 2
            lines += [f"wait {target - frame}", f"dump res-{r['menu']:02x}-{target:05d}"]
            frame = target
        (work / "dump.script").write_text("\n".join(lines + ["quit"]) + "\n")
        snesref(args, work, work / "dump.script")
        for r in runs:
            target = (r["start"] + r["end"]) // 2
            d = mvl.Dump(work, f"res-{r['menu']:02x}-{target:05d}")
            r["dump_frame"] = target
            r["dump_menu"] = f"0x{d.wram[0x9F]:02X}"
            r["texts"] = tier.screen_texts(d)
    checks = {}
    for menu, words in EXPECT.items():
        hit = [r for r in runs if r["menu"] == menu]
        checks[f"menu_{menu:02x}_observed"] = bool(hit)
        checks[f"menu_{menu:02x}_labels"] = bool(hit) and all(
            any(w in t for t in hit[0]["texts"]) for w in words)
    checks["circuit_and_stunt_results_advance_to_track_select"] = all(
        r["next_menu"] == 0xF6 for r in runs if r["menu"] in (0xBC, 0x18))
    for r in runs:
        r["menu"] = f"0x{r['menu']:02X}"
        r["next_menu"] = None if r["next_menu"] is None else f"0x{r['next_menu']:02X}"
    report = {
        "schema_version": 1,
        "question": "Do the historical result-screen menu values hold on the canonical ROM?",
        "harness": "snesref + pinned snes9x-libretro; Dessyreqt 2014 movie input from its anchored SRAM (in sync through the first Crawler tracks)",
        "fixture": "tests/input/result-screens-probe.script (documentation stub; the tool generates its dump schedule from the trace)",
        "note": "7E:0313 reads 0x3C/0x3D on circuit/stunt result screens, so it is not a pure in-race boolean there; 0x84 also appears for ~33 frames in the post-race fade",
        "result_runs": runs,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    for r in runs:
        print(r["menu"], r["state"], r["start"], r["end"], r["next_menu"], r["texts"][:4])
    print(json.dumps(checks, indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
