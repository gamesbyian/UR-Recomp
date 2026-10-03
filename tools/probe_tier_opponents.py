#!/usr/bin/env python3
"""Probe which named opponent each medal tier faces in stock 1P tour play.

Decision served: preserving the legacy opponents (Bronsen, Silvia, Goldwyn)
independently of any modern medal redesign needs their exact identities.

Method (reference harness; synthetic SRAM only as pre-run setup):
1. take a clean-boot battery SRAM image;
2. set the Crawler/MIKE medal cell (``77:069C``) to 0, 1 and 2 and recompute the
   ``77:073C`` checksum (16-bit sum of 170 words from ``05E8``);
3. drive ``tests/input/tier-opponent-probe.script`` (1P -> MIKE -> Crawler ->
   Dragster -> NOW PLAYING -> race) and decode the TRACK_SELECT tier label, the
   NOW PLAYING opponent name, ``$017F`` and the P2 racer palette at CGRAM ``$C0``.

``summarize`` is pure; ``main`` drives snesref.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import build_legacy_cast_presets as cast
import extract_menu_visual_language as mvl

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/input/tier-opponent-probe.script"
HUNTER_SCRIPT = ROOT / "tests/input/tier-opponent-hunter-probe.script"
ALT_SCRIPT = ROOT / "tests/input/tier-opponent-alt-probe.script"
ALT_RIDER, ALT_TOUR_ROW, ALT_MEDAL = 1, 2, 1  # ANDREW on SHUFFLER holding bronze
TIER_TABLES = (0x10D3, 0x10FD)  # derived per-rider tier + mirror (83:9F49 / 83:9F81)
MEDAL_CELL = 0x069C  # Crawler row, MIKE column
CHECKSUM_START, CHECKSUM_WORDS, CHECKSUM_AT = 0x05E8, 170, 0x073C
TIER_LABELS = {"BRONZE", "SILVER", "GOLD"}


def checksum(sram: bytes) -> int:
    return sum(sram[CHECKSUM_START + 2 * i] | sram[CHECKSUM_START + 2 * i + 1] << 8
               for i in range(CHECKSUM_WORDS)) & 0xFFFF


def seeded(sram: bytes, medal: int, all_gold: bool = False, cell: int = MEDAL_CELL) -> bytes:
    """Seed MIKE's Crawler medal, or (all_gold) rows 0..7 gold plus tier 3 as 83:885D would derive."""
    out = bytearray(sram)
    if all_gold:
        for row in range(8):
            out[MEDAL_CELL + 16 * row] = 3
        for table in TIER_TABLES:
            out[table] = 3
    else:
        out[cell] = medal
    value = checksum(out)
    out[CHECKSUM_AT], out[CHECKSUM_AT + 1] = value & 0xFF, value >> 8
    return bytes(out)


def screen_texts(d: mvl.Dump) -> list[str]:
    map_base, _, width, height = mvl.bg_layout(d.fillram, 1)
    x_screen = ((d.ppu["bg"][1]["hofs"] & 0x3FF) // 256) % (width // 32)
    rows = mvl.text_rows(d.vram, map_base, width, height, 7, x_screen) + \
        mvl.small_text_rows(d.vram, map_base, width, height, 7, x_screen)
    return [r["text"] for r in sorted(rows, key=lambda r: (r["y"], r["x_left"]))]


def observe(dump_dir: Path, rom: bytes) -> dict:
    track, card, race = (mvl.Dump(dump_dir, t) for t in ("tier-track", "tier-card", "tier-race"))
    card_texts = screen_texts(card)
    vs_name = None
    if "VS" in card_texts:
        # The small font has no hyphen glyph decoder, so ANTI-UNI arrives as two runs.
        after = card_texts[card_texts.index("VS") + 1:]
        parts = []
        for t in after:
            if t.startswith("RACING"):
                break
            parts.append(t)
        vs_name = "-".join(parts)
    opponent = race.wram[0x17F]
    cg = race.cgram
    p2 = [f"0x{cg[2 * (0xC0 + k)] | cg[2 * (0xC0 + k) + 1] << 8:04X}" for k in range(16)]
    asset = cast.palette_asset(rom, cast.FIRST_RACER_PALETTE_ASSET + opponent)
    return {
        "tour_row": track.wram[0xD0],
        "tier_label": next((t for t in screen_texts(track) if t in TIER_LABELS), None),
        "card_opponent_name": vs_name,
        "card_texts": card_texts,
        "p2_rider_index": opponent,
        "in_race": race.wram[0x313],
        "p2_palette_matches_asset": p2[1:] == asset["bgr555_words"][1:],
        "p2_palette_asset": asset["asset_id_hex"],
    }


def summarize(observations: dict, names: list[str]) -> dict:
    checks = {}
    alt = observations.get("alt")
    if alt is not None:
        checks["alt_andrew_shuffler_tour_row"] = alt["tour_row"] == ALT_TOUR_ROW
        checks["alt_andrew_shuffler_opponent_index_18"] = alt["p2_rider_index"] == 17 + ALT_MEDAL and alt["in_race"] == 1
        checks["alt_andrew_shuffler_card_name"] = alt["card_opponent_name"] == names[17 + ALT_MEDAL].upper()
        checks["alt_andrew_shuffler_tier_label"] = alt["tier_label"] == "SILVER"
    hunter = observations.get("hunter")
    if hunter is not None:
        checks["hunter_tour_row_8"] = hunter["tour_row"] == 8
        checks["hunter_opponent_index_20"] = hunter["p2_rider_index"] == 20 and hunter["in_race"] == 1
        checks["hunter_card_name_matches_table"] = hunter["card_opponent_name"] == names[20].upper()
        checks["hunter_p2_palette_matches_asset"] = hunter["p2_palette_matches_asset"]
    for medal, o in ((k, v) for k, v in observations.items() if k not in ("hunter", "alt")):
        expected_index = 17 + medal
        checks[f"medal{medal}_opponent_index_{expected_index}"] = o["p2_rider_index"] == expected_index and o["in_race"] == 1
        checks[f"medal{medal}_card_name_matches_table"] = o["card_opponent_name"] == names[expected_index].upper()
        checks[f"medal{medal}_p2_palette_matches_asset"] = o["p2_palette_matches_asset"]
        checks[f"medal{medal}_tier_label"] = o["tier_label"] == ("BRONZE", "SILVER", "GOLD")[medal]
    return {"observations": {str(k): v for k, v in observations.items()},
            "rule": "main tours: opponent rider index = 17 + medal held for the selected tour and rider (0 -> BRONSEN, 1 -> SILVIA, 2 -> GOLDWYN); Hunter tour (row 8): ANTI-UNI (20)",
            "checks": checks, "all_checks_pass": all(checks.values()) and bool(observations)}


def main() -> int:
    tools = ROOT / ".tools/src"
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("clean_sram", type=Path, help="clean-boot 8 KiB SRAM image (e.g. any *.sram.bin from the menu fixture)")
    ap.add_argument("--snesref", type=Path, default=tools / "snesrecomp/build-snesref/snesref")
    ap.add_argument("--core", type=Path, default=tools / "snes9x-libretro/libretro/snes9x_libretro.so")
    ap.add_argument("--rom", type=Path, default=cast.ROM)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/tier-opponent-probe.json")
    args = ap.parse_args()
    clean = args.clean_sram.read_bytes()
    if len(clean) != 0x2000 or checksum(clean) != (clean[CHECKSUM_AT] | clean[CHECKSUM_AT + 1] << 8):
        raise SystemExit("clean SRAM must be 8 KiB with a valid 05E8..073B checksum")
    rom = args.rom.read_bytes()
    observations = {}
    with tempfile.TemporaryDirectory() as td:
        for medal in (0, 1, 2, "hunter", "alt"):
            run = Path(td) / f"case-{medal}"
            run.mkdir()
            hunter = medal == "hunter"
            if medal == "alt":
                (run / "in.srm").write_bytes(seeded(clean, ALT_MEDAL, cell=MEDAL_CELL + 16 * ALT_TOUR_ROW + ALT_RIDER))
                script = ALT_SCRIPT
            else:
                (run / "in.srm").write_bytes(seeded(clean, 0, all_gold=True) if hunter else seeded(clean, medal))
                script = HUNTER_SCRIPT if hunter else SCRIPT
            env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1", SNESREF_WRAM_FILL="0",
                       SNESREF_SRAM_IN=str(run / "in.srm"), SNESREF_SCRIPT=str(script), SNESREF_DUMP_DIR=str(run))
            with open(run / "snesref.log", "w") as log:
                subprocess.run([str(args.snesref), str(args.core), str(args.rom)], env=env, cwd=run,
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            observations[medal] = observe(run, rom)
    report = {
        "schema_version": 1,
        "question": "Which named opponent does each medal tier face?",
        "harness": "snesref + pinned snes9x-libretro; synthetic SRAM medal cell set before boot only",
        "fixtures": [str(x.relative_to(ROOT)) for x in (SCRIPT, HUNTER_SCRIPT, ALT_SCRIPT)],
        **summarize(observations, cast.default_names(rom, 21)),
    }
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report["checks"], indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
