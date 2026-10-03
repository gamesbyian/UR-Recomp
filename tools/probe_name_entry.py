#!/usr/bin/env python3
"""Drive the stock name editor and confirm the forbidden-name rule at runtime.

Decision served: closes the ``name_entry_cursor_mapping`` capability (binding
cursor movement to the visible grid) and runtime-confirms the statically
recovered forbidden-name rule (``analysis/generated/forbidden-name-table.json``)
that the modern COOL NAME! acknowledgement will reuse.

Grid (PLAYER_NAME_EDITOR via OPTIONS -> RENAME PLAYER -> MIKE): 13 columns at
x = 24 + 16*col, rows at y = 24 + 24*row. Row 0 is A-M, row 1 is N-Z, row 2 is
the delete arrow then 0-9, row 3 is punctuation then OK at column 12. The
cursor starts on T (row 1, column 6). A enters the highlighted cell.

For each name the tool generates a script from the shared rename route,
types the name, moves to OK, confirms, and decodes the editor message, the
cursor OBJ and the SRAM name record (offset 0x000C for rider 0).

``plan_moves`` is pure and unit-tested; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import extract_forbidden_name_table as fnt
import extract_menu_visual_language as mvl

ROOT = Path(__file__).resolve().parents[1]
EXPLORE = ROOT / "tests/input/ui-rename-editor-explore.script"
START = (1, 6)  # T
OK_CELL = (3, 12)
NAMES = ["SONIC", "XSEGAX", "BASSIST", "ZED"]
NAME_RECORD_RIDER0 = 0x000C


def cell_for(ch: str) -> tuple[int, int]:
    if "A" <= ch <= "M":
        return 0, ord(ch) - ord("A")
    if "N" <= ch <= "Z":
        return 1, ord(ch) - ord("N")
    raise ValueError(f"only letters are planned: {ch!r}")


def plan_moves(name: str) -> list[str]:
    """Script lines: move to each letter, press A, then move to OK and press A."""
    lines, (r, c) = [], START
    for target in [cell_for(ch) for ch in name] + [OK_CELL]:
        tr, tc = target
        lines += [f"press {'down' if tr > r else 'up'} 1", "wait 12"] * abs(tr - r)
        lines += [f"press {'right' if tc > c else 'left'} 1", "wait 12"] * abs(tc - c)
        lines += ["press a 2", "wait 20"]
        r, c = tr, tc
    return lines


def route_prefix() -> list[str]:
    src = EXPLORE.read_text().splitlines()
    start = src.index("# LEFT") + 1
    return src[start:src.index("dump ui-rename-editor-left-before")]


def observe(run: Path) -> dict:
    d = mvl.Dump(run, "name-result")
    info = mvl.catalog_screen(d)
    small = [r["text"] for r in info["small_font_runs"]]
    sram = (run / "name-result.sram.bin").read_bytes()
    return {
        "editor_text": small,
        "screen_titles": [r["text"] for r in info["big_font_rows"]][:6],
        "rejected_message": any("NOT COOL ENOUGH" in t for t in small),
        "still_in_editor": any(r["text"].startswith("ABCDEFGHIJKLM") for r in info["big_font_rows"]),
        "sram_name_rider0": sram[NAME_RECORD_RIDER0:NAME_RECORD_RIDER0 + 8].split(b"\xff")[0].decode("latin1").rstrip("_"),
    }


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snesref", type=Path, default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument("--core", type=Path, default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=fnt.ROM)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/name-entry-probe.json")
    args = ap.parse_args()
    words = fnt.words_from_rom(args.rom.read_bytes())
    results, checks = {}, {}
    with tempfile.TemporaryDirectory() as td:
        for name in NAMES:
            run = Path(td) / name
            run.mkdir()
            script = run / "s.script"
            script.write_text("\n".join(route_prefix() + plan_moves(name) + ["wait 90", "dump name-result", "quit"]) + "\n")
            env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
                       SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(run))
            with open(run / "snesref.log", "w") as log:
                subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=run,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            obs = observe(run)
            predicted = fnt.is_forbidden(name, words)
            obs["static_rule_predicts_forbidden"] = predicted
            results[name] = obs
            if predicted:
                checks[f"{name.lower()}_rejected_in_editor"] = obs["rejected_message"] and obs["still_in_editor"] \
                    and obs["sram_name_rider0"] == "mike"
            else:
                checks[f"{name.lower()}_accepted_and_saved"] = not obs["rejected_message"] \
                    and obs["sram_name_rider0"] == name.lower()
    report = {
        "schema_version": 1,
        "question": "Does the stock editor reject exactly the names the recovered rule predicts?",
        "harness": "snesref + pinned snes9x-libretro, clean boot, OPTIONS -> RENAME PLAYER -> MIKE",
        "grid": {"columns": 13, "x": "24 + 16*col", "y": "24 + 24*row",
                 "rows": ["A-M", "N-Z", "delete arrow, 0-9 (from column 1)", "punctuation, OK at column 12"],
                 "start_cell": "T (row 1, column 6)", "enter": "A enters the highlighted cell",
                 "rejection": "inline 'NOT COOL ENOUGH' below the name; the editor stays open and SRAM is unchanged",
                 "saved_record": "accepted names are written lowercase to the rider's 16-byte SRAM name record, terminated by FF (older bytes beyond the terminator are left in place)"},
        "results": results,
        "checks": checks,
        "all_checks_pass": all(checks.values()) and bool(checks),
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    for n, o in results.items():
        print(n, o["rejected_message"], o["sram_name_rider0"], o["static_rule_predicts_forbidden"])
    print(json.dumps(checks, indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
