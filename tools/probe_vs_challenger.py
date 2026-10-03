#!/usr/bin/env python3
"""Verify the post-race VS flow: result, champions, challenger pick, track choice.

Decision served: VS_CHALLENGER (0x3F) and VS_CHALLENGE_TRACK (0x5A) were Tier 1
UI-atlas states known only from the 2014 bot. The frozen first-race VS route
reaches TOUR_SELECT/TRACK_SELECT instead; these states only appear after a VS
race has a winner.

Method: run ``tests/input/vs-challenger-route.input`` with
``tests/input/vs-challenger-route-observe.script`` through a snesref built with
``tools/patches/snesrecomp-dual-controller-input.patch`` (the pinned snesref
reads only P1). Decode each checkpoint's menu value and on-screen text.

``evaluate`` is pure and unit-tested; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import extract_menu_visual_language as mvl
import probe_tier_opponents as tier

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "tests/input/vs-challenger-route.input"
SCRIPT = ROOT / "tests/input/vs-challenger-route-observe.script"
CHECKPOINTS = ["vsc-result", "vsc-champions", "vsc-pick-challenger", "vsc-pick-after-p1", "vsc-track-choice", "vsc-next"]
DRAW_INPUT = ROOT / "tests/input/vs-first-race.input"
DRAW_SCRIPT = ROOT / "tests/input/vs-draw-rematch-observe.script"
DRAW_CHECKPOINTS = ["vsd-result", "vsd-rematch", "vsd-after"]
BRANCH_EXPECT = {1: (0x16, "NOW PLAYING"), 2: (0x91, "PICK TRACK"), 3: (0x6D, "PICK TOUR"), 4: (0xD7, "1P")}
BRANCH_SCRIPT = "wait 4580\ndump vsb-pre\nwait 300\ndump vsb-post\nquit\n"
TRACK_CHOICES = ["NEXT TRACK", "SAME TRACK", "SELECT TRACK", "SELECT TOUR", "QUIT"]


def evaluate_draw(obs: dict[str, dict]) -> dict:
    r, rm, after = (obs[c] for c in DRAW_CHECKPOINTS)
    return {
        "draw_result_both_no_time": r["menu"] == 0xF9 and r["texts"].count("NO TIME") >= 2,
        "draw_shows_rematch_banner_0xB7": rm["menu"] == 0xB7 and rm["texts"] == ["REMATCH"],
        "rematch_returns_to_now_playing": after["menu"] == 0x16 and "NOW PLAYING" in after["texts"],
    }


def branch_input(base_lines: list[str], downs: int) -> str:
    """The challenger route with the final NEXT TRACK confirm replaced by P2 Down x downs + A."""
    keep = [l for l in base_lines if l and not l.startswith("#") and not l.startswith("4620:")]
    ev = [f"{4600 + 30 * i}:2:000:020" for i in range(downs)] + [f"{4600 + 30 * downs + 20}:2:000:100"]
    return "\n".join(keep + ev) + "\n"


def evaluate_branches(branches: dict[int, dict]) -> dict:
    checks = {}
    for downs, obs in branches.items():
        menu, label = BRANCH_EXPECT[downs]
        name = TRACK_CHOICES[downs].lower().replace(" ", "_")
        checks[f"track_choice_{name}_reaches_0x{menu:02X}"] = obs["menu"] == menu and label in obs["texts"]
    return checks


def evaluate(obs: dict[str, dict]) -> dict:
    r, ch, pc, p1, tc, nx = (obs[c] for c in CHECKPOINTS)
    texts = {k: v["texts"] for k, v in obs.items()}

    def after(texts_list, label):
        return texts_list[texts_list.index(label) + 1] if label in texts_list else None

    return {
        "result_is_vs_race_result_0xF9": r["menu"] == 0xF9 and "COMPLETE" in r["texts"],
        "p1_finished_p2_no_time": after(texts["vsc-result"], "MIKE") not in (None, "NO TIME")
                                   and after(texts["vsc-result"], "ANDREW") == "NO TIME",
        "champions_table_0xD3": ch["menu"] == 0xD3 and "VS CHAMPIONS" in ch["texts"],
        "pick_challenger_0x3F": pc["menu"] == 0x3F and "PICK CHALLENGER" in pc["texts"],
        "p1_inert_on_pick_challenger": p1["menu"] == 0x3F and p1["column"] == pc["column"],
        "p2_pick_opens_track_choice_0x5A": tc["menu"] == 0x5A and tc["texts"][:5] == TRACK_CHOICES,
        "next_track_reaches_now_playing": nx["menu"] == 0x16 and "NOW PLAYING" in nx["texts"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, required=True,
                    help="snesref built with tools/patches/snesrecomp-dual-controller-input.patch")
    ap.add_argument("--core", type=Path, default=ROOT / ".tools/src/snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/vs-challenger-probe.json")
    args = ap.parse_args()
    def run(input_file: Path, script: Path, names: list[str]) -> dict[str, dict]:
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
                       SNESREF_INPUT_FILE=str(input_file), SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(work))
            with open(work / "snesref.log", "w") as log:
                subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=work,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            if "p2=" not in (work / "snesref.log").read_text():
                raise SystemExit("snesref did not report P2 input; build it with the dual-controller patch")
            out = {}
            for c in names:
                d = mvl.Dump(work, c)
                out[c] = {"menu": d.wram[0x9F], "column": d.wram[0x0C63], "row": d.wram[0x000E],
                          "p1_rider": d.wram[0x17D], "p2_rider": d.wram[0x17F], "texts": tier.screen_texts(d)}
            return out

    obs = run(INPUT, SCRIPT, CHECKPOINTS)
    draw = run(DRAW_INPUT, DRAW_SCRIPT, DRAW_CHECKPOINTS)
    branches = {}
    with tempfile.TemporaryDirectory() as bd:
        base = INPUT.read_text().splitlines()
        for downs in BRANCH_EXPECT:
            inp, scr = Path(bd) / f"b{downs}.input", Path(bd) / f"b{downs}.script"
            inp.write_text(branch_input(base, downs))
            scr.write_text(BRANCH_SCRIPT)
            branches[downs] = run(inp, scr, ["vsb-post"])["vsb-post"]
    checks = {**evaluate(obs), **evaluate_draw(draw), **evaluate_branches(branches)}
    obs.update(draw)
    obs.update({f"branch-{TRACK_CHOICES[k].lower().replace(' ', '-')}": v for k, v in branches.items()})
    report = {
        "schema_version": 1,
        "question": "What follows a decided VS race, and who controls it?",
        "harness": "snesref (dual-controller patch) + pinned snes9x-libretro, clean boot, frozen two-pad input",
        "fixtures": [str(x.relative_to(ROOT)) for x in (INPUT, SCRIPT, DRAW_INPUT, DRAW_SCRIPT)],
        "flow": "VS race result 0xF9 -> VS CHAMPIONS 0xD3 -> PICK CHALLENGER 0x3F (loser's pad) -> track choice 0x5A -> NOW PLAYING; a drawn race (both NO TIME) instead shows a REMATCH banner 0xB7 that advances to NOW PLAYING on a button",
        "checkpoints": {k: {**v, "menu": f"0x{v['menu']:02X}", "column": f"0x{v['column']:02X}"} for k, v in obs.items()},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    for k, v in obs.items():
        print(k, hex(v["menu"]), v["texts"][:6])
    print(json.dumps(checks, indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
