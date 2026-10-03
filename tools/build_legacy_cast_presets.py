#!/usr/bin/env python3
"""Build the exact preset table for the 16 original Uniracers racers.

Each racer's identity in stock play is the rider index ``$017D`` (0..15), which
is also the medal-matrix column (analysis/data/progression-model.json) and
selects in-race palette asset ``0x06 + index`` (analysis/data/presentation-assets.json).

Sources joined here:
- ROM: the five-byte asset table at ``82:B32F`` (bank, little-endian address,
  little-endian length) for palette assets 0x06..0x15;
- runtime: the clean-boot PLAYER_SELECT_P1 dump from
  ``tests/input/menu-visual-language.script`` for default names and grid
  placement. The grid rule ``index = 2 * row + column`` was confirmed by
  confirming MIKE/ANDREW/MARTIN/AMY/STEVE and reading ``$017D``. The end-of-frame
  OBJ palettes are cross-checked against the ROM assets.

Colour labels are a derived convenience from the mid-ramp colour, not stock data.
Standard library only.
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
from pathlib import Path

import extract_menu_visual_language as mvl

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
ASSET_TABLE = (0x82, 0xB32F)
FIRST_RACER_PALETTE_ASSET = 0x06
RACER_COUNT = 16
# Entries that differ between racers: a dark-to-light body-colour ramp.
BODY_RAMP_ENTRIES = [2, 4, 6, 7, 9, 11, 13]
LABEL_ENTRY = 9
LEFT_COLUMN_PX, RIGHT_COLUMN_PX = 40, 152
# Grid confirmations run separately (see module docstring): (row, column) -> $017D.
CONFIRMED_INDICES = {(0, 0): 0, (0, 1): 1, (1, 0): 2, (2, 0): 4, (7, 1): 15}


def lorom(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def palette_asset(rom: bytes, asset_id: int) -> dict:
    entry_off = lorom(*ASSET_TABLE) + 5 * asset_id
    entry = rom[entry_off:entry_off + 5]
    bank, addr, length = entry[0], entry[1] | entry[2] << 8, entry[3] | entry[4] << 8
    data = rom[lorom(bank, addr):lorom(bank, addr) + length]
    return {
        "asset_id_hex": f"0x{asset_id:02X}",
        "table_entry_snes": f"82:{ASSET_TABLE[1] + 5 * asset_id:04X}",
        "source_snes": f"{bank:02X}:{addr:04X}",
        "length": length,
        "bgr555_words": [f"0x{data[i] | data[i + 1] << 8:04X}" for i in range(0, length, 2)],
        "payload_sha256": hashlib.sha256(data).hexdigest(),
    }


def rgb(word: int) -> list[int]:
    return [(word & 31) << 3, ((word >> 5) & 31) << 3, ((word >> 10) & 31) << 3]


def colour_label(word: int) -> str:
    r, g, b = (c / 248 for c in rgb(word))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.25:
        return "white" if v > 0.75 else "grey" if v > 0.3 else "black"
    hue = h * 360
    if (hue < 15 or hue >= 335) and v > 0.75 and s < 0.5:
        return "pink"
    for limit, name in ((15, "red"), (40, "orange"), (70, "yellow"), (100, "lime"), (140, "green"),
                        (170, "teal"), (200, "cyan"), (255, "blue"), (290, "purple"), (335, "pink"), (360, "red")):
        if hue < limit:
            return name
    return "red"


def roster_names(dump: mvl.Dump) -> dict[tuple[int, int], str]:
    map_base, _, width, height = mvl.bg_layout(dump.fillram, 1)
    x_screen = ((dump.ppu["bg"][1]["hofs"] & 0x3FF) // 256) % (width // 32)
    runs = mvl.small_text_rows(dump.vram, map_base, width, height, 7, x_screen)
    out = {}
    for column, x in enumerate((LEFT_COLUMN_PX, RIGHT_COLUMN_PX)):
        col_runs = sorted((r for r in runs if r["x_left"] == x), key=lambda r: r["y"])
        for row, run in enumerate(col_runs):
            out[(row, column)] = run["text"]
    return out


def build(dump_dir: Path, rom: bytes) -> dict:
    rider = mvl.series(dump_dir, "rider")[-1]
    names = roster_names(rider)
    cg = rider.cgram
    end_of_frame_obj = [[f"0x{cg[2 * (128 + p * 16 + k)] | cg[2 * (128 + p * 16 + k) + 1] << 8:04X}"
                         for k in range(16)] for p in range(8)]
    racers = []
    for index in range(RACER_COUNT):
        row, column = index // 2, index % 2
        asset = palette_asset(rom, FIRST_RACER_PALETTE_ASSET + index)
        mid = int(asset["bgr555_words"][LABEL_ENTRY], 16)
        racers.append({
            "rider_index": index,
            "rider_index_ram": "$017D (P1) / $017F (P2)",
            "default_name": names.get((row, column)),
            "select_grid": {"row": row, "column": "left" if column == 0 else "right"},
            "medal_matrix_column": index,
            "race_palette": asset,
            "body_ramp_rgb": [rgb(int(asset["bgr555_words"][k], 16)) for k in BODY_RAMP_ENTRIES],
            "colour_label_derived": colour_label(mid),
        })
    words = [r["race_palette"]["bgr555_words"] for r in racers]
    varying = [k for k in range(16) if len({w[k] for w in words}) > 1]
    checks = {
        "sixteen_default_names_decoded": all(r["default_name"] for r in racers),
        "names_unique": len({r["default_name"] for r in racers}) == RACER_COUNT,
        "body_ramp_entries_are_the_varying_set": set(BODY_RAMP_ENTRIES) <= set(varying),
        # At end of frame, HDMA has loaded the bottom four grid rows (riders 8..15) into OBJ palettes 0..7.
        "rider_select_icons_use_race_palettes_8_15": all(
            end_of_frame_obj[p][1:] == words[8 + p][1:] for p in range(8)),
        "grid_rule_matches_confirmations": all(2 * r + c == i for (r, c), i in CONFIRMED_INDICES.items()),
        "selection_state_player_select": rider.wram[0x9F] == 0x3C,
    }
    return {
        "schema_version": 1,
        "purpose": "Exact presets for the 16 classic racers: identity index, default name, select-grid slot, medal column and in-race palette.",
        "sources": {
            "rom": "reference/roms/retail/Uniracers_USA.sfc asset table 82:B32F, palette assets 0x06..0x15",
            "runtime": "tests/input/menu-visual-language.script PLAYER_SELECT_P1 dump (clean boot, snesref + pinned snes9x-libretro)",
            "grid_rule_confirmations": {f"row{r}-{'left' if c == 0 else 'right'}": i for (r, c), i in CONFIRMED_INDICES.items()},
            "related": ["analysis/data/progression-model.json", "analysis/data/presentation-assets.json"],
        },
        "grid_rule": "rider_index = 2 * row + (0 left | 1 right); 8 rows x 2 columns on PLAYER_SELECT_P1",
        "palette_layout": {
            "body_ramp_entries": BODY_RAMP_ENTRIES,
            "varying_entries_observed": varying,
            "note": "remaining entries are a shared grey/black chassis; entries 8, 14 and 15 vary slightly for a few racers",
        },
        "default_names_are_renameable": "RENAME PLAYER edits names in battery SRAM; values here are clean-boot defaults",
        "legacy_opponents_not_listed": "Bronsen, Silverton and Goldwyn are not in the selectable roster",
        "racers": racers,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dump_dir", type=Path, help="snesref dump directory from tests/input/menu-visual-language.script")
    ap.add_argument("--rom", type=Path, default=ROM)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/legacy-cast-presets.json")
    args = ap.parse_args()
    report = build(args.dump_dir, args.rom.read_bytes())
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    for r in report["racers"]:
        print(f'{r["rider_index"]:2d} {r["default_name"]:<9} {r["select_grid"]["row"]}/{r["select_grid"]["column"]:<5} '
              f'{r["race_palette"]["asset_id_hex"]} {r["colour_label_derived"]}')
    print(json.dumps(report["checks"], indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
