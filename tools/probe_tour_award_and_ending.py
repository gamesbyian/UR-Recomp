#!/usr/bin/env python3
"""Reach the tour medal award, the per-tour gold sequence, ENDING and the splash cheat.

Decision served: ENDING was the last Tier 1 UI gap, and the policy feature
``ending-sequence-and-shortcut`` rested on an unverified public chord. This probe
drives the stock paths decoded in R-2026-10-04-UI-22:

- ``80:F549`` (UNIRACERS title splash, 110 frames) compares the held pad with the
  5-entry table ``80:F602`` (Up, Left, Up, R, A). On a full match it backs the
  tier tables up to ``0x10E3``, sets every rider's tier ``0x10D3`` to 3 (all tours,
  Hunter included) and sets ``0x10D0`` = 1; the next pass through the splash
  restores the tiers and clears the flag.
- ``83:8805`` awards the tour when its five ``0x1075`` flags are set. Bronze and
  silver go to ``83:AEF6``; reaching gold (or completing an already-gold tour)
  dispatches per tour through ``83:88FD`` (eight short vignettes, then TOUR_SELECT). Hunter's entry ``83:AB9A`` is the
  ending: newspaper pages chosen by ``0x10D0`` (normal: two pages; cheat: one
  CHEAT! page), then WHODUNNIT credits with ``$9F`` = 0x5B, then the title.

Diagnostic pokes (labelled in the report): the award runs replay the Dessyreqt movie
up to its first Dragster win and seed the other four tour flags (and, for gold, the
medal cell) in battery SRAM mid-race, because no committed input wins five tracks.
Runs for other tours also pin the track index ``$CE`` = 5*row + 4 and ``$D0`` = row
over the result window and set the stored track bytes ``0x074A``/``0x067E``, which is
how the Dragster win is booked as the last track of that tour. The cheat runs use input only.

Needs snesref built with tools/patches/snesrecomp-dual-controller-input.patch and
then tools/patches/snesrecomp-sram-poke.patch (adds the ``spoke`` script command).
``evaluate`` is pure and unit-tested; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMV = ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
CHEAT = ("up", "left", "up", "r", "a")
CHEAT_AT = 300          # frame inside the 110-frame title splash
WIN_CUT = 2950          # movie input is dropped after its first Dragster win
SEED_AT = 2000          # mid-race, after rider select wiped the flags
TIERS, TIER_BACKUP, CHEAT_FLAG = 0x10D3, 0x10E3, 0x10D0
CRAWLER_CELL = 0x069C   # rider 0 (MIKE); tour row r is +16*r
FLAGS = 0x1075
ENDING_MENU = 0x5B

TOURS = ("crawler", "jumper", "shuffler", "bounder", "walker", "runner", "hopper", "sprinter", "hunter")
TOUR_SELECT_MENU = 0x6D
SCENE_FRAME = WIN_CUT + 252     # first dump after the result is dismissed


def scenario(row: int, medal_seed: int, cheat_flag: bool = False) -> dict:
    return {"row": row, "medal_seed": medal_seed, "cell": CRAWLER_CELL + 16 * row, "cheat_flag": cheat_flag}


AWARD_SCENARIOS = {
    "bronze": scenario(0, 0),
    **{f"gold_{name}": scenario(row, 2) for row, name in enumerate(TOURS[:8])},
    "ending": scenario(8, 2),
    "ending_cheat": scenario(8, 2, cheat_flag=True),
}


def award_script(cfg: dict) -> str:
    row = cfg["row"]
    track = 5 * row + 4
    # Row 0: the movie's real Dragster win sets track 0, so seed tracks 1-4.
    # Other rows: seed tracks 0-3 and book the win as track 4 of that tour.
    lines = [f"wait {SEED_AT}",
             f"spoke {FLAGS + 5 * row + (1 if row == 0 else 0):04X} 01010101",
             f"spoke {cfg['cell']:04X} {cfg['medal_seed']:02X}"]
    if row:
        lines += [f"spoke 074A {track:02X}", f"spoke 067E {track:02X}"]
    if cfg["cheat_flag"]:
        lines.append(f"spoke {CHEAT_FLAG:04X} 01")
    lines.append(f"wait {WIN_CUT - 200 - SEED_AT}")
    # $CE = track, $CF = 0, $D0 = tour row over the result window.
    lines.append(f"pokefor CE {track:02X}00{row:02X} 200" if row else "wait 200")
    lines += [f"dump w-{WIN_CUT:05d}", "wait 150", "press a 2"]
    frame = WIN_CUT + 152
    while frame < WIN_CUT + 3000:
        lines += [f"dump w-{frame:05d}", "wait 100"]
        frame += 100
    return "\n".join(lines + ["quit"]) + "\n"


def cheat_script(sequence: bool) -> str:
    lines = [f"wait {CHEAT_AT}"]
    for b in CHEAT if sequence else ():
        lines += [f"press {b} 3", "wait 3"]
    lines += ["until 009F == D7 3000", "wait 20", "dump menu", "quit"]
    return "\n".join(lines) + "\n"


def sample(work: Path, tag: str) -> dict:
    s = (work / f"{tag}.sram.bin").read_bytes()
    w = (work / f"{tag}.wram.bin").read_bytes()
    fb = work / f"{tag}.fb.bmp"
    return {"menu": w[0x9F], "tiers": list(s[TIERS:TIERS + 16]), "tier_backup": list(s[TIER_BACKUP:TIER_BACKUP + 16]),
            "cheat_flag": s[CHEAT_FLAG], "medals": [s[CRAWLER_CELL + 16 * r] for r in range(9)],
            "tour_flags": [list(s[FLAGS + 5 * r:FLAGS + 5 * r + 5]) for r in range(9)],
            "fb_sha1": hashlib.sha1(fb.read_bytes()).hexdigest()[:12] if fb.exists() else None}


def evaluate(obs: dict) -> dict:
    c, n, back = obs["cheat"], obs["cheat_control"], obs["cheat_reboot"]
    checks = {
        "cheat_sets_every_tier_to_3": c["tiers"] == [3] * 16 and c["cheat_flag"] == 1,
        "cheat_backs_up_previous_tiers": c["tier_backup"] == n["tiers"],
        "no_sequence_no_unlock": n["tiers"] != [3] * 16 and n["cheat_flag"] == 0,
        "next_boot_restores_tiers": back["tiers"] == n["tiers"] and back["cheat_flag"] == 0,
    }
    for name, cfg in AWARD_SCENARIOS.items():
        timeline = obs[name]
        last = timeline[max(timeline)]
        row = cfg["row"]
        checks[f"{name}_medal_incremented"] = last["medals"][row] == cfg["medal_seed"] + 1
        checks[f"{name}_tour_flags_cleared"] = last["tour_flags"][row] == [0] * 5
        menus = [timeline[f]["menu"] for f in sorted(timeline)]
        if row == 8:
            checks[f"{name}_reaches_ending_menu"] = ENDING_MENU in menus
        else:
            checks[f"{name}_no_ending"] = ENDING_MENU not in menus
        if name.startswith("gold_"):
            checks[f"{name}_returns_to_tour_select"] = TOUR_SELECT_MENU in menus
    scene = lambda name: obs[name][SCENE_FRAME]["fb_sha1"]
    golds = [scene(f"gold_{n}") for n in TOURS[:8]]
    checks["gold_scenes_differ_per_tour"] = len(set(golds)) == len(golds)
    checks["cheat_flag_changes_ending_page"] = scene("ending") != scene("ending_cheat")
    return checks


def run(args, work: Path, script: str, sram_in: Path | None = None, input_file: Path | None = None) -> None:
    work.mkdir(parents=True, exist_ok=True)
    (work / "s.script").write_text(script)
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
               SNESREF_SCRIPT=str(work / "s.script"), SNESREF_DUMP_DIR=str(work))
    if sram_in:
        env["SNESREF_SRAM_IN"] = str(sram_in)
    if input_file:
        env["SNESREF_INPUT_FILE"] = str(input_file)
    with open(work / "snesref.log", "w") as log:
        subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=work,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    if "spoke" in script and "unknown" in (work / "snesref.log").read_text().lower():
        raise SystemExit("snesref rejected 'spoke'; build it with tools/patches/snesrecomp-sram-poke.patch")


def cut_input(src: Path, dst: Path, end: int) -> None:
    out = []
    for line in src.read_text().splitlines():
        if not line or line.startswith("#"):
            out.append(line)
            continue
        parts = line.split(":")
        start, dur = int(parts[0]), int(parts[1])
        if start >= end:
            continue
        parts[1] = str(min(dur, end - start))
        out.append(":".join(parts))
    dst.write_text("\n".join(out) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, required=True,
                    help="snesref with the dual-controller and sram-poke patches")
    ap.add_argument("--core", type=Path, default=ROOT / ".tools/src/snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/tour-award-ending-probe.json")
    args = ap.parse_args()
    obs = {}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fmt = td / "fmt"
        fmt.mkdir()
        (fmt / "blank.srm").write_bytes(b"\x60" * 0x2000)
        run(args, fmt, "until 009F == D7 3600\nwait 10\ndump clean\nquit\n", fmt / "blank.srm")
        clean = fmt / "clean.sram.bin"
        run(args, td / "cheat", cheat_script(True), clean)
        obs["cheat"] = sample(td / "cheat", "menu")
        run(args, td / "control", cheat_script(False), clean)
        obs["cheat_control"] = sample(td / "control", "menu")
        run(args, td / "reboot", cheat_script(False), td / "cheat/menu.sram.bin")
        obs["cheat_reboot"] = sample(td / "reboot", "menu")

        subprocess.run([sys.executable, str(ROOT / "tools/extract_smv_input.py"), str(SMV),
                        "--input-out", str(td / "movie.input"), "--sram-out", str(td / "anchored.srm"),
                        "--sram-size", "8192", "--json-out", str(td / "movie.json")], check=True, stdout=subprocess.DEVNULL)
        cut_input(td / "movie.input", td / "movie-cut.input", WIN_CUT)
        for name, cfg in AWARD_SCENARIOS.items():
            work = td / name
            run(args, work, award_script(cfg), td / "anchored.srm", td / "movie-cut.input")
            obs[name] = {int(p.name[2:7]): sample(work, p.name[:-9]) for p in work.glob("w-*.sram.bin")}
    checks = evaluate(obs)
    summary = {name: [{"frame": f, "menu": hex(v["menu"]), "cheat_flag": v["cheat_flag"],
                       "medal": v["medals"][AWARD_SCENARIOS[name]["row"]]}
                      for f, v in sorted(obs[name].items())
                      if f == min(obs[name]) or v["menu"] != obs[name][max(k for k in obs[name] if k < f)]["menu"]]
               for name in AWARD_SCENARIOS}
    report = {
        "schema_version": 1,
        "question": "What do tour completion, gold, Hunter gold and the splash cheat do in stock?",
        "harness": "snesref (dual-controller + sram-poke patches) + pinned snes9x-libretro",
        "diagnostic_pokes": "award runs seed tour flags/medal in SRAM mid-race; Hunter runs pin $CE=44/$D0=8 and the stored track bytes (see docstring)",
        "cheat": {"sequence": list(CHEAT), "window": "UNIRACERS title splash (80:F549, 110 frames)",
                  "effect": "every rider tier 3 for this power-on; tiers restored and 0x10D0 cleared on the next pass through the splash",
                  "observed": {k: obs[k] for k in ("cheat", "cheat_control", "cheat_reboot")}},
        "gold_scenes": "reaching gold dispatches 83:88FD by tour row: Crawler 83:C49C, Jumper 83:BB80, Shuffler 83:B1EB, Bounder 83:B7D2, Walker 83:B506, Runner 83:C715, Hopper 83:C11E, Sprinter 83:BED0 (short side-on vignette with a tour-specific prop, then TOUR_SELECT), Hunter 83:AB9A (ending)",
        "ending": {"trigger": "Hunter medal reaching gold (83:88FD entry 8 -> 83:AB9A)",
                   "pages": {"normal": "DAILY NEWS 'AMAZING' then NATIONAL GOSSIP 'SPEEDKING'", "cheat": "DAILY NEWS 'CHEAT!'"},
                   "credits": "WHODUNNIT developer portraits, $9F = 0x5B, then title 0x84",
                   "observed_menu_changes": summary},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(checks, indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
