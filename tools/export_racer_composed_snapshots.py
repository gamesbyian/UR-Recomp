#!/usr/bin/env python3
"""Export composed racer-object PNGs from retained runtime snapshots.

This is the human-facing bridge from SNES presentation state to lossless art:
given the canonical ROM, retained WRAM snapshots, and the staging-analysis
report, emit stored-orientation and display-orientation 64x64 transparent PNGs
plus a provenance-rich manifest. Bulk images are intended for workflow
artifacts or local generation, not routine Git storage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from extract_racer_presentation_family import (
    compose_racer_staging,
    encode_png_rgba,
    extract_frame,
    rasterize_composed_player_rgba,
    sha256,
)


def u16(data: bytes, off: int) -> int:
    return data[off] | (data[off + 1] << 8)


def frame_provenance(frame: dict) -> dict:
    return {
        "frame_id": frame["frame_id_hex"],
        "record_header": frame["record_header_hex"],
        "source_snes": frame["source_snes"],
        "source_rom_offset": frame["source_rom_offset"],
        "record_sha256": frame["record_sha256"],
        "packed_word_count": frame["packed_word_count"],
    }


def export_snapshots(
    rom: bytes,
    dump_dir: Path,
    staging_report: dict,
    output_dir: Path,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    by_tag = {x["checkpoint"]: x for x in staging_report["runtime_staging_checks"]}
    images = []

    for wram_path in sorted(dump_dir.glob("two-player-*.wram.bin")):
        tag = wram_path.name[:-9]
        if tag not in by_tag:
            continue
        wram = wram_path.read_bytes()
        cp = by_tag[tag]

        ids = {
            "p1_primary": u16(wram, 0x0FE9),
            "p2_primary": u16(wram, 0x0FEB),
            "p1_companion": u16(wram, 0x0D3F),
            "p2_companion": u16(wram, 0x0D41),
        }
        frames = {name: extract_frame(rom, fid) for name, fid in ids.items()}
        selectors = {"p1": u16(wram, 0x0C83), "p2": u16(wram, 0x0C85)}
        companion_gate_words = {"p1": u16(wram, 0x0D1B), "p2": u16(wram, 0x0D1D)}
        companion_enabled = {
            "p1": companion_gate_words["p1"] != 0,
            "p2": companion_gate_words["p2"] != 0,
        }
        composition = compose_racer_staging(
            frames["p1_primary"],
            frames["p2_primary"],
            frames["p1_companion"],
            frames["p2_companion"],
            p1_selector=selectors["p1"],
            p2_selector=selectors["p2"],
            p1_companion_enabled=companion_enabled["p1"],
            p2_companion_enabled=companion_enabled["p2"],
        )
        replay = cp.get("composition_replay") or {}

        for player, slot_num, color_off in (
            ("p1", 98, 0x017D),
            ("p2", 99, 0x017F),
        ):
            palette_asset = 0x06 + wram[color_off]
            slot = next(
                (x for x in cp["racer_object_slots"] if x["slot"] == slot_num),
                None,
            )
            if slot is None:
                raise ValueError(f"{tag}: missing retained OAM slot {slot_num}")
            hflip = bool(slot["hflip"])
            vflip = bool(slot["vflip"])

            stored = rasterize_composed_player_rgba(
                rom, composition, player, palette_asset
            )
            display = rasterize_composed_player_rgba(
                rom,
                composition,
                player,
                palette_asset,
                hflip=hflip,
                vflip=vflip,
            )
            stored_png = encode_png_rgba(64, 64, stored)
            display_png = encode_png_rgba(64, 64, display)
            stem = f"{tag}-{player}"
            stored_name = f"{stem}-stored.png"
            display_name = f"{stem}-display.png"
            (output_dir / stored_name).write_bytes(stored_png)
            (output_dir / display_name).write_bytes(display_png)

            all_exact = replay.get("all_occupied_sources_exact") is True
            images.append({
                "checkpoint": tag,
                "player": player,
                "representation": (
                    "synchronized-composed-object"
                    if all_exact
                    else "snapshot-derived-composed-object-candidate"
                ),
                "source_frame_ids": {
                    k: f"0x{v:04X}" for k, v in ids.items()
                },
                "source_records": {
                    k: frame_provenance(v) for k, v in frames.items()
                },
                "selectors": selectors,
                "companion_gate_words": {
                    k: f"0x{v:04X}" for k, v in companion_gate_words.items()
                },
                "companion_enabled": companion_enabled,
                "palette_asset_id": f"0x{palette_asset:02X}",
                "palette_formula": "0x06 + player color selector",
                "player_color_selector_address": (
                    "$017D" if player == "p1" else "$017F"
                ),
                "oam_slot": slot_num,
                "oam_hflip": hflip,
                "oam_vflip": vflip,
                "dimensions": [64, 64],
                "origin": [0, 0],
                "occupancy_tile_offset": [1, 0],
                "stored_png": stored_name,
                "stored_png_sha256": sha256(stored_png),
                "display_png": display_name,
                "display_png_sha256": sha256(display_png),
                "staging_replay": {
                    "mode": replay.get("comparison_mode"),
                    "source_exact_cells": replay.get("source_exact_cells"),
                    "occupied_cells": replay.get("occupied_cells"),
                    "destinations_present": replay.get("destinations_present"),
                    "all_occupied_sources_exact": replay.get(
                        "all_occupied_sources_exact"
                    ),
                },
                "uncertainty": (
                    None
                    if all_exact
                    else (
                        "retained frame-boundary IDs/selectors are not "
                        "source-exact for every occupied descriptor from the "
                        "already-built staging list; use synchronized evidence "
                        "for golden final-object validation"
                    )
                ),
            })

    return {
        "schema_version": 2,
        "family": "ordinary-2p-composed-racer-objects",
        "rom_sha256": sha256(rom),
        "dimensions": [64, 64],
        "canonical_orientation": "stored object-local orientation",
        "display_orientation": "canonical raster followed by retained OAM H/V flip",
        "bulk_storage_policy": (
            "PNGs are generated artifacts; retain compact hashes/manifests in Git "
            "and avoid committing the full image corpus"
        ),
        "images": images,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--staging-report", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    report = json.loads(args.staging_report.read_text(encoding="utf-8"))
    manifest = export_snapshots(rom, args.dump_dir, report, args.output_dir)
    manifest_path = args.manifest or (args.output_dir / "manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if not manifest["images"]:
        raise SystemExit("no composed racer images emitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
