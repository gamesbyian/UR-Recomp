#!/usr/bin/env python3
"""Decode and verify the stock Track Records SRAM table.

Decision served: modern PB deltas and a unified records surface need the stock
per-track records (value, holder, rank) so they can embed or import the
original tables rather than inventing a parallel store.

Recovered layout (battery SRAM, 8 KiB image offsets):
- ``0x0422 + 2*i``: 150 little-endian words, ``i = 50*rank + 5*tour_row + track``;
  rank 0/1/2 are the GOLD/SILVER/BRONZE rows of the Track Records screen (1st,
  2nd and 3rd best), tour_row follows the medal matrix (Crawler 0 ... Hunter 8,
  group 9 unidentified), track is the position within the tour (stunt is 2).
- values: race = finish time and circuit = best lap, both in 1/100 s (default
  60000 = 10:00.00, shown as NO TIME); stunt = score (default 0).
- ``0x054E``: 16-bit sum of the 150 words.
- ``0x0550 + i``: holder rider index (default 16 = ``someone``).

Verification runs (snesref, clean boot):
1. ``tests/input/ui-race-result-route.script`` from a clean save: Dragster
   finish fills rank 0 of Crawler/Dragster with the finish time held by MIKE.
2. the same route again on the resulting save: an equal time fills rank 1.
3. the Dessyreqt movie through Zoom Zoo and Bowl: circuit stores best lap
   (rank 0, track 1) and stunt stores the score (rank 0, track 2).

``decode`` / ``checksum`` are pure and unit-tested; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import build_legacy_cast_presets as cast

ROOT = Path(__file__).resolve().parents[1]
RECORDS, COUNT, CHECKSUM, HOLDERS = 0x0422, 150, 0x054E, 0x0550
RANKS, GROUPS, TRACKS = 3, 10, 5
STUNT_TRACK = 2
NO_TIME, NO_SCORE, NOBODY = 60000, 0, 16
RESULT_ROUTE = ROOT / "tests/input/ui-race-result-route.script"
SMV = ROOT / "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
P1_RESULT_WORD = 0x0618  # last-race P1 result (time/score); 0x061A holds the opponent's


def index(rank: int, tour_row: int, track: int) -> int:
    return 50 * rank + TRACKS * tour_row + track


def word(sram: bytes, offset: int) -> int:
    return sram[offset] | sram[offset + 1] << 8


def checksum(sram: bytes) -> int:
    return sum(word(sram, RECORDS + 2 * i) for i in range(COUNT)) & 0xFFFF


def decode(sram: bytes, names: list[str] | None = None) -> list[dict]:
    out = []
    for rank in range(RANKS):
        for tour in range(GROUPS):
            for track in range(TRACKS):
                i = index(rank, tour, track)
                value = word(sram, RECORDS + 2 * i)
                holder = sram[HOLDERS + i]
                kind = "stunt_score" if track == STUNT_TRACK else "time_cs"
                empty = value == (NO_SCORE if kind == "stunt_score" else NO_TIME)
                out.append({"rank": rank, "tour_row": tour, "track": track, "kind": kind, "value": value,
                            "empty": empty, "holder": holder,
                            "holder_name": names[holder].upper() if names and holder < len(names) else None})
    return out


def run(args, workdir: Path, script: Path, sram_in: Path, input_file: Path | None = None) -> None:
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
               SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(workdir), SNESREF_SRAM_IN=str(sram_in))
    if input_file:
        env["SNESREF_INPUT_FILE"] = str(input_file)
    with open(workdir / "snesref.log", "w") as log:
        subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=workdir,
                       stdout=log, stderr=subprocess.STDOUT, check=True)


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument("--core", type=Path, default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=cast.ROM)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/track-records-sram.json")
    args = ap.parse_args()
    names = cast.default_names(args.rom.read_bytes(), 21)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # Clean formatted save: boot once with an all-0x60 image (how the anchored movie SRAM formats) and dump.
        fmt = td / "fmt"; fmt.mkdir()
        (fmt / "blank.srm").write_bytes(b"\x60" * 0x2000)
        (fmt / "s.script").write_text("until 009F == D7 3600\nwait 10\ndump clean\nquit\n")
        run(args, fmt, fmt / "s.script", fmt / "blank.srm")
        clean = (fmt / "clean.sram.bin").read_bytes()
        first = td / "first"; first.mkdir()
        run(args, first, RESULT_ROUTE, fmt / "clean.sram.bin")
        after1 = (first / "ui-race-result-after-back.sram.bin").read_bytes()
        second = td / "second"; second.mkdir()
        run(args, second, RESULT_ROUTE, first / "ui-race-result-after-back.sram.bin")
        after2 = (second / "ui-race-result-after-back.sram.bin").read_bytes()
        tas = td / "tas"; tas.mkdir()
        subprocess.run([sys.executable, str(ROOT / "tools/extract_smv_input.py"), str(SMV),
                        "--input-out", str(tas / "movie.input"), "--sram-out", str(tas / "anchored.srm"),
                        "--sram-size", "8192", "--json-out", str(tas / "movie.json")], check=True, stdout=subprocess.DEVNULL)
        (tas / "s.script").write_text("wait 12250\ndump tas\nquit\n")
        run(args, tas, tas / "s.script", tas / "anchored.srm", tas / "movie.input")
        tas_sram = (tas / "tas.sram.bin").read_bytes()
    d0 = index(0, 0, 0)
    t1 = word(after1, P1_RESULT_WORD)
    checks = {
        "clean_defaults": all(r["empty"] and r["holder"] == NOBODY for r in decode(clean)),
        "checksum_formula_holds_clean": checksum(clean) == word(clean, CHECKSUM),
        "first_finish_fills_rank0_dragster": word(after1, RECORDS + 2 * d0) == t1 and after1[HOLDERS + d0] == 0,
        "checksum_formula_holds_after_records": checksum(after1) == word(after1, CHECKSUM) and checksum(after2) == word(after2, CHECKSUM),
        "equal_second_finish_fills_rank1": word(after2, RECORDS + 2 * index(1, 0, 0)) == word(after2, P1_RESULT_WORD)
                                            and after2[HOLDERS + index(1, 0, 0)] == 0,
        "circuit_stores_best_lap_not_total": word(tas_sram, RECORDS + 2 * index(0, 0, 1)) not in (NO_TIME,)
                                             and word(tas_sram, RECORDS + 2 * index(0, 0, 1)) < 6000,
        "stunt_stores_score": word(tas_sram, RECORDS + 2 * index(0, 0, 2)) > 0,
        "checksum_formula_holds_tas": checksum(tas_sram) == word(tas_sram, CHECKSUM),
    }
    filled = lambda s: [r for r in decode(s, names) if not r["empty"]]
    report = {
        "schema_version": 1,
        "purpose": "Stock Track Records SRAM layout for modern PB deltas and records-surface embedding.",
        "layout": {"records": "0x0422 + 2*(50*rank + 5*tour_row + track), 150 LE words",
                   "checksum": "0x054E = 16-bit sum of the 150 record words",
                   "holders": "0x0550 + (50*rank + 5*tour_row + track), rider index (16 = someone)",
                   "ranks": "0/1/2 = GOLD/SILVER/BRONZE rows on Track Records = 1st/2nd/3rd best",
                   "tour_row": "medal-matrix order (Crawler 0, Jumper 1, Shuffler 2 ... Hunter 8); group 9 unidentified",
                   "values": "race: finish time, circuit: best lap (1/100 s, 60000 = NO TIME); stunt: score (0 = none)",
                   "last_race_slots": "0x0618 / 0x061A hold the last race's P1 / opponent result value"},
        "observed": {"first_run": filled(after1), "second_run": filled(after2), "tas_after_bowl": filled(tas_sram)},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(checks, indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
