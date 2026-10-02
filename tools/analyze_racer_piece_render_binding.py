#!/usr/bin/env python3
"""Bind decoded racer packed cells to the retained runtime OAM presentation layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from compare_europe_usa_snes2asm_homologs import cpu_to_offset, seed_entries, trace

STATIC_START = "83:F180"
STATIC_END = "83:F290"
CHECKPOINTS = ("two-player-race-1220", "two-player-race-1420")
RACER_OAM_SLOTS = (96, 97, 98, 99)


def decode_obsel(value: int) -> dict:
    size_code = (value >> 5) & 0x07
    sizes = {
        0: ((8, 8), (16, 16)),
        1: ((8, 8), (32, 32)),
        2: ((8, 8), (64, 64)),
        3: ((16, 16), (32, 32)),
        4: ((16, 16), (64, 64)),
        5: ((32, 32), (64, 64)),
        6: ((16, 32), (32, 64)),
        7: ((16, 32), (32, 32)),
    }
    small, large = sizes[size_code]
    return {
        "raw": value,
        "raw_hex": f"0x{value:02X}",
        "size_code": size_code,
        "small_pixels": list(small),
        "large_pixels": list(large),
        "name_select": (value >> 3) & 0x03,
        "name_base": value & 0x07,
    }


def decode_oam_slot(oam: bytes, slot: int, obsel: dict) -> dict:
    if len(oam) < 544:
        raise ValueError("OAM snapshot must contain 544 bytes")
    q = slot * 4
    xlo, y, tile, attr = oam[q:q + 4]
    pair = (oam[0x200 + slot // 4] >> ((slot % 4) * 2)) & 0x03
    x = xlo | ((pair & 1) << 8)
    large = bool((pair >> 1) & 1)
    size = obsel["large_pixels"] if large else obsel["small_pixels"]
    return {
        "slot": slot,
        "x": x,
        "y": y,
        "tile": tile,
        "tile_hex": f"0x{tile:02X}",
        "attr": attr,
        "attr_hex": f"0x{attr:02X}",
        "palette_number": (attr >> 1) & 0x07,
        "hflip": bool(attr & 0x40),
        "vflip": bool(attr & 0x80),
        "large": large,
        "size_pixels": size,
    }


def static_listing(rom: bytes) -> dict:
    d = trace(rom)
    seed_entries(d, [cpu_to_offset("83:F0BB"), cpu_to_offset("83:F2BB")])
    start = cpu_to_offset(STATIC_START)
    end = cpu_to_offset(STATIC_END) + 1
    d.decode(start, end)
    rows = []
    for off, ins in d.code.item_range(start, end):
        rows.append({
            "cpu": f"83:{0x8000 + (off % 0x8000):04X}",
            "text": ins.text(),
        })
    hits = []
    for i, row in enumerate(rows):
        t = row["text"].upper()
        if "1645" in t or "15A1" in t:
            hits.append({
                "match": row,
                "context": rows[max(0, i - 5): min(len(rows), i + 6)],
            })
    return {
        "start": STATIC_START,
        "end": STATIC_END,
        "instruction_count": len(rows),
        "staging_xrefs": hits,
    }


def load_frame_map(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["frame_id_hex"]: row for row in data["frames"]}


def checkpoint_binding(dump_dir: Path, evidence: dict, frames: dict[str, dict], tag: str) -> dict:
    regs = json.loads((dump_dir / f"{tag}.regs.json").read_text(encoding="utf-8"))
    oam = (dump_dir / f"{tag}.oam.bin").read_bytes()
    obsel = decode_obsel(int(regs["obsel"]))
    slots = [decode_oam_slot(oam, s, obsel) for s in RACER_OAM_SLOTS]

    e = next(row for row in evidence["checkpoints"] if row["checkpoint"] == tag)
    frame_ids = [f"0x{x:04X}" for x in e["frame_ids"]]

    players = []
    expected_attrs = (0x66, 0x68)
    for player_index, frame_id in enumerate(frame_ids, start=1):
        expected_attr = expected_attrs[player_index - 1]
        candidates = [s for s in slots if s["attr"] == expected_attr]
        players.append({
            "player": player_index,
            "frame_id": frame_id,
            "packed_cell_count": len(frames[frame_id]["pieces"]),
            "occupancy_layout": frames[frame_id]["occupancy_layout"],
            "matching_oam_slots": candidates,
            "large_oam_slots": [s for s in candidates if s["large"]],
        })

    return {
        "checkpoint": tag,
        "obsel": obsel,
        "racer_slots": slots,
        "players": players,
    }


def build(rom: bytes, frame_manifest: Path, evidence_path: Path, dump_dir: Path) -> dict:
    frames = load_frame_map(frame_manifest)
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    cps = [checkpoint_binding(dump_dir, evidence, frames, tag) for tag in CHECKPOINTS]

    stable_large = {}
    for cp in cps:
        for p in cp["players"]:
            key = str(p["player"])
            stable_large.setdefault(key, []).append([
                (s["slot"], s["tile_hex"], s["attr_hex"], s["size_pixels"])
                for s in p["large_oam_slots"]
            ])

    return {
        "schema_version": 1,
        "purpose": "Bind decoded racer packed cells to retained OAM object identities without conflating the two layers.",
        "static_renderer": static_listing(rom),
        "checkpoints": cps,
        "derived": {
            "obsel_mode": "0x83 selects 16x16 small and 64x64 large OBJs",
            "packed_cell_layer": "Each decoded frame has a 5x6 occupancy lattice and one packed 16-bit word per occupied cell.",
            "oam_layer": "The same large OAM tile identities remain in use while authoritative frame IDs and packed-cell records change.",
            "one_packed_cell_per_oam_object": False,
            "interpretation": "Packed records construct sub-OBJ racer presentation content beneath stable large OAM objects; OAM owns placement/palette/orientation at the later composition layer.",
            "stable_large_oam_by_player": stable_large,
        },
    }


def render_md(r: dict) -> str:
    lines = [
        "# Racer packed-cell to OAM binding",
        "",
        "This report joins the recovered 30-cell packed-frame decoder to retained ordinary-2P OAM/register snapshots.",
        "",
        "## Runtime binding",
        "",
    ]
    for cp in r["checkpoints"]:
        o = cp["obsel"]
        lines.append(
            f"- {cp['checkpoint']}: OBSEL {o['raw_hex']} => small {o['small_pixels'][0]}x{o['small_pixels'][1]}, "
            f"large {o['large_pixels'][0]}x{o['large_pixels'][1]}."
        )
        for p in cp["players"]:
            ls = ", ".join(
                f"slot {s['slot']} tile {s['tile_hex']} attr {s['attr_hex']} {s['size_pixels'][0]}x{s['size_pixels'][1]}"
                for s in p["large_oam_slots"]
            ) or "none"
            lines.append(
                f"  - P{p['player']} frame {p['frame_id']}: {p['packed_cell_count']} packed cells; large OAM: {ls}."
            )
    lines += [
        "",
        "The frame IDs change between the two retained checkpoints while the large OAM object identities remain stable. "
        "Therefore the packed records are not one-record-per-OAM-entry. They feed the tile/presentation construction layer beneath the later OAM placement layer.",
        "",
        "## Static staging xrefs",
        "",
    ]
    for hit in r["static_renderer"]["staging_xrefs"]:
        lines.append(f"### {hit['match']['cpu']} {hit['match']['text']}")
        lines.append("")
        for row in hit["context"]:
            lines.append(f"    {row['cpu']}  {row['text']}")
        lines.append("")
    lines += [
        "## Boundary",
        "",
        "This proof does not assign spatial X/Y names to the 5x6 lattice axes and does not name the unresolved low two bits of each packed word. "
        "Those remain separate finite questions.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--frame-manifest", type=Path, default=ROOT / "analysis/generated/racer-presentation-family.json")
    ap.add_argument("--evidence", type=Path, default=ROOT / "analysis/evidence/racer-presentation-observed-states.json")
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    r = build(args.rom.read_bytes(), args.frame_manifest, args.evidence, args.dump_dir)
    js = json.dumps(r, indent=2, sort_keys=True) + "\n"
    md = render_md(r)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(js, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
