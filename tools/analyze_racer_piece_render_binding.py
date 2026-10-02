#!/usr/bin/env python3
"""Bind decoded racer packed cells to the retained runtime OAM/VRAM presentation layer.

This is a finite semantic join, not a full animation disassembly. It combines
the mechanically recovered 30-cell packed-frame mapping, bounded static xrefs
around the $1645/$15A1 staging writes, and retained ordinary-2P OAM/register/
VRAM snapshots.
"""

from __future__ import annotations

import argparse
import hashlib
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
TILE_BYTES_4BPP = 32


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
        "name_base_byte_address": (value & 0x07) << 14,
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
        "name_high_bit": attr & 0x01,
        "palette_number": (attr >> 1) & 0x07,
        "priority": (attr >> 4) & 0x03,
        "hflip": bool(attr & 0x40),
        "vflip": bool(attr & 0x80),
        "large": large,
        "size_pixels": size,
    }


def decode_4bpp_tile(data: bytes) -> list[list[int]]:
    if len(data) != TILE_BYTES_4BPP:
        raise ValueError("SNES 4bpp tile must be exactly 32 bytes")
    out = []
    for y in range(8):
        p0, p1 = data[y * 2:y * 2 + 2]
        p2, p3 = data[16 + y * 2:16 + y * 2 + 2]
        row = []
        for x in range(8):
            bit = 7 - x
            row.append(
                ((p0 >> bit) & 1)
                | (((p1 >> bit) & 1) << 1)
                | (((p2 >> bit) & 1) << 2)
                | (((p3 >> bit) & 1) << 3)
            )
        out.append(row)
    return out


def object_tile_number(top_left: int, grid_x: int, grid_y: int) -> int:
    return (
        (((top_left & 0xF0) + (grid_y << 4)) & 0xF0)
        | (((top_left & 0x0F) + grid_x) & 0x0F)
    )


def object_tile_vram_byte_address(obsel: dict, slot: dict, tile_number: int) -> int:
    if slot["name_high_bit"]:
        raise ValueError("retained racer binding expects OBJ name-high bit 0")
    return (obsel["name_base_byte_address"] + tile_number * TILE_BYTES_4BPP) & 0xFFFF


def tile_nonzero_count(vram: bytes, addr: int) -> int:
    tile = decode_4bpp_tile(vram[addr:addr + TILE_BYTES_4BPP])
    return sum(px != 0 for row in tile for px in row)


def frame_occupancy_matrix(frame: dict) -> list[list[bool]]:
    rows = [[False] * 6 for _ in range(5)]
    for piece in frame["pieces"]:
        rows[piece["major_slot"]][piece["minor_slot"]] = True
    return rows


def object_nonzero_grid(vram: bytes, obsel: dict, slot: dict) -> list[list[bool]]:
    if slot["size_pixels"] != [64, 64]:
        raise ValueError("spatial binding currently targets retained 64x64 racer OBJ")
    out = []
    for gy in range(8):
        row = []
        for gx in range(8):
            tile = object_tile_number(slot["tile"], gx, gy)
            addr = object_tile_vram_byte_address(obsel, slot, tile)
            row.append(tile_nonzero_count(vram, addr) > 0)
        out.append(row)
    return out


def find_direct_subrect_matches(container: list[list[bool]], needle: list[list[bool]]) -> list[dict]:
    h, w = len(needle), len(needle[0])
    out = []
    for y0 in range(len(container) - h + 1):
        for x0 in range(len(container[0]) - w + 1):
            got = [row[x0:x0 + w] for row in container[y0:y0 + h]]
            if got == needle:
                out.append({"x": x0, "y": y0, "width": w, "height": h})
    return out


def bind_pieces_to_vram(frame: dict, vram: bytes, obsel: dict, slot: dict, match: dict) -> list[dict]:
    out = []
    for piece in frame["pieces"]:
        gx = match["x"] + piece["minor_slot"]
        gy = match["y"] + piece["major_slot"]
        tile_number = object_tile_number(slot["tile"], gx, gy)
        addr = object_tile_vram_byte_address(obsel, slot, tile_number)
        raw = vram[addr:addr + TILE_BYTES_4BPP]
        if len(raw) != TILE_BYTES_4BPP:
            raise ValueError("truncated VRAM tile")
        presented_gx = 7 - gx if slot["hflip"] else gx
        presented_gy = 7 - gy if slot["vflip"] else gy
        out.append({
            "word_index": piece["word_index"],
            "word_hex": piece["word_hex"],
            "major_slot": piece["major_slot"],
            "minor_slot": piece["minor_slot"],
            "object_tile_grid_x": gx,
            "object_tile_grid_y": gy,
            "presented_tile_grid_x": presented_gx,
            "presented_tile_grid_y": presented_gy,
            "presented_pixel_box_relative": [
                presented_gx * 8,
                presented_gy * 8,
                presented_gx * 8 + 7,
                presented_gy * 8 + 7,
            ],
            "object_tile_number": tile_number,
            "object_tile_hex": f"0x{tile_number:02X}",
            "vram_byte_address": addr,
            "vram_byte_address_hex": f"0x{addr:04X}",
            "nonzero_pixels": tile_nonzero_count(vram, addr),
            "tile_sha256": hashlib.sha256(raw).hexdigest(),
        })
    return out


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
    vram = (dump_dir / f"{tag}.vram.bin").read_bytes()
    obsel = decode_obsel(int(regs["obsel"]))
    slots = [decode_oam_slot(oam, s, obsel) for s in RACER_OAM_SLOTS]

    e = next(row for row in evidence["checkpoints"] if row["checkpoint"] == tag)
    frame_ids = [f"0x{x:04X}" for x in e["frame_ids"]]

    players = []
    expected_attrs = (0x66, 0x68)
    for player_index, frame_id in enumerate(frame_ids, start=1):
        expected_attr = expected_attrs[player_index - 1]
        candidates = [s for s in slots if s["attr"] == expected_attr]
        large = [s for s in candidates if s["large"]]
        frame = frames[frame_id]
        occupancy = frame_occupancy_matrix(frame)
        spatial = []
        for s in large:
            grid = object_nonzero_grid(vram, obsel, s)
            matches = find_direct_subrect_matches(grid, occupancy)
            row = {
                "slot": s["slot"],
                "tile_hex": s["tile_hex"],
                "direct_matches": matches,
                "unique_direct_match": len(matches) == 1,
            }
            if len(matches) == 1:
                row["piece_vram_bindings"] = bind_pieces_to_vram(frame, vram, obsel, s, matches[0])
            spatial.append(row)
        players.append({
            "player": player_index,
            "frame_id": frame_id,
            "packed_cell_count": len(frame["pieces"]),
            "occupancy_layout": frame["occupancy_layout"],
            "matching_oam_slots": candidates,
            "large_oam_slots": large,
            "spatial_binding": spatial,
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

    proven = []
    for cp in cps:
        for p in cp["players"]:
            for s in p["spatial_binding"]:
                if s["unique_direct_match"]:
                    bindings = s["piece_vram_bindings"]
                    proven.append({
                        "checkpoint": cp["checkpoint"],
                        "player": p["player"],
                        "frame_id": p["frame_id"],
                        "oam_slot": s["slot"],
                        "oam_tile": s["tile_hex"],
                        "packed_cell_count": p["packed_cell_count"],
                        "match": s["direct_matches"][0],
                        "bound_piece_count": len(bindings),
                        "all_bound_tiles_nonempty": all(x["nonzero_pixels"] > 0 for x in bindings),
                    })

    return {
        "schema_version": 2,
        "purpose": "Bind decoded racer packed cells to retained OAM/VRAM presentation identities without conflating the layers.",
        "static_renderer": static_listing(rom),
        "checkpoints": cps,
        "derived": {
            "obsel_mode": "0x83 selects 16x16 small and 64x64 large OBJs",
            "packed_cell_layer": "Each decoded frame has a 5x6 occupancy lattice and one packed 16-bit word per occupied cell.",
            "oam_layer": "The same large OAM tile identities remain in use while authoritative frame IDs and packed-cell records change.",
            "one_packed_cell_per_oam_object": False,
            "interpretation": "Packed records construct 8x8 subtiles inside stable large racer OAM objects; OAM owns later object placement, palette and orientation.",
            "spatially_proven_frames": proven,
            "spatial_axis_result": "For uniquely matched retained frames, major_slot is stored tile row and minor_slot is stored tile column; OAM H/V flip is applied afterward for presented position.",
        },
    }


def render_md(r: dict) -> str:
    lines = [
        "# Racer packed-cell to OAM/VRAM binding",
        "",
        "This report joins the recovered 30-cell packed-frame decoder to retained ordinary-2P OAM, register and VRAM snapshots.",
        "",
        "## Runtime object layer",
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
        "Frame IDs and packed records change while the large OAM object identities remain stable, so packed records are not one-record-per-OAM-entry.",
        "",
        "## Direct spatial bindings",
        "",
    ]
    for row in r["derived"]["spatially_proven_frames"]:
        m = row["match"]
        lines.append(
            f"- {row['checkpoint']} P{row['player']} frame {row['frame_id']}: "
            f"{row['bound_piece_count']}/{row['packed_cell_count']} packed records bind to nontransparent 8x8 VRAM subtiles "
            f"inside OAM slot {row['oam_slot']} tile {row['oam_tile']}; the 5x6 occupancy rectangle is uniquely located at "
            f"object-tile offset ({m['x']},{m['y']})."
        )
    lines += [
        "",
        "For these uniquely matched frames, major_slot is the stored 8x8 tile row and minor_slot is the stored tile column. "
        "The OAM flip bits are applied afterward to obtain presented tile coordinates. Each machine-readable binding includes the exact destination OBJ tile number, VRAM byte address, nonzero-pixel count and SHA-256 of the 32-byte 4bpp tile.",
        "",
        "The retained P1 endpoint snapshots do not yield an exact 5x6 occupancy match for their simultaneously sampled authoritative IDs, so this report does not promote a P1 spatial binding from those endpoints.",
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
        "The low two bits of each packed word remain unnamed. The spatial row/column interpretation above is promoted only for frames with an exact retained VRAM occupancy match; broader family-wide orientation remains a separate finite test.",
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
